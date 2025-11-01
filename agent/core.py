"""
TicketGlass Agent Core - Agentic reasoning engine for IT support transparency.

This module provides the Agent class, which maintains per-ticket context,
detects sentiment, and generates empathetic, never-repeating explanations
using AWS Bedrock. Pure Python, zero UI dependencies, AWS-native.

Design principles:
- Single responsibility: Agent reasons about context, generates summaries
- Type-safe: Full Pydantic validation on inputs/outputs
- Testable: Pure logic, no side effects, deterministic reasoning
- Secure: AWS credentials from environment, input validation, no logging of sensitive data
- Efficient: Context_history scanned once per request, minimal LLM calls
"""

import os
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from enum import Enum

import boto3
from pydantic import BaseModel, Field, field_validator

# Import from local modules (using package paths)
from agent.prompts import get_system_prompt, TONE_INSTRUCTIONS, ToneTemplate
from agent.keywords import (
    SENTIMENT_KEYWORDS_MAP,
    HeuristicThresholds,
    get_sentiment_keywords,
)


# ============================================================================
# LOGGING CONFIGURATION (Structured for Production)
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Handler: console output (no sensitive data logged)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
handler.setFormatter(formatter)
logger.addHandler(handler)


# ============================================================================
# UTILITY FUNCTIONS (Shared Heuristics)
# ============================================================================


def keyword_overlap_ratio(text_a: str, text_b: str) -> float:
    """
    Calculate keyword overlap ratio between two texts.

    Used by both sentiment detection and repetition validation.
    Refactored from repeated logic to DRY principle.

    Args:
        text_a: First text (e.g., previous summary)
        text_b: Second text (e.g., new summary)

    Returns:
        float: Overlap ratio (0.0 to 1.0)
        - 0.0: No overlap
        - 1.0: 100% overlap
        - 0.6+: High overlap (likely repetition)

    Example:
        >>> ratio = keyword_overlap_ratio("clear DNS cache", "clear DNS cache")
        >>> ratio > 0.9
        True
    """
    words_a = set(text_a.lower().split())
    words_b = set(text_b.lower().split())

    if not words_a or not words_b:
        return 0.0

    overlap = len(words_a & words_b)
    max_len = max(len(words_a), len(words_b))

    return overlap / max_len if max_len > 0 else 0.0


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================


class Phase(str, Enum):
    """Ticket lifecycle phases."""

    RECEIVED = "Received"
    ASSIGNED = "Assigned"
    DIAGNOSED = "Diagnosed"
    RESOLVED = "Resolved"


class Sentiment(str, Enum):
    """User sentiment detection."""

    FRUSTRATED = "frustrated"
    SATISFIED = "satisfied"
    NEUTRAL = "neutral"
    CONFUSED = "confused"


class ToneApplied(str, Enum):
    """Tone applied to the agent response."""

    INITIAL = "initial"
    EMPATHETIC = "empathetic"
    ESCALATION = "escalation"
    CELEBRATORY = "celebratory"
    SIMPLIFIED = "simplified"


# ============================================================================
# PYDANTIC MODELS (Type-Safe Input/Output)
# ============================================================================


class ContextEntry(BaseModel):
    """Single entry in the ticket's context history."""

    phase: int = Field(..., ge=1, description="Phase number (1-indexed)")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    what_we_said: str = Field(..., min_length=1, description="Agent summary")
    what_user_said_back: str = Field(..., min_length=1, description="User feedback")
    our_reasoning: str = Field(
        ..., min_length=1, description="Why we said what we said"
    )

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Ensure timestamp is valid ISO 8601 format."""
        try:
            datetime.fromisoformat(v.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Invalid ISO 8601 timestamp: {v}")
        return v


class TicketState(BaseModel):
    """Full ticket state passed to the agent."""

    ticket_id: str = Field(..., min_length=1, description="Unique ticket ID")
    user_name: str = Field(..., min_length=1, description="User's name")
    initial_issue: str = Field(..., min_length=1, description="Original problem")
    current_phase: Phase = Field(..., description="Current ticket phase")
    context_history: List[ContextEntry] = Field(
        default_factory=list, description="Previous attempts and user feedback"
    )
    user_sentiment: Sentiment = Field(
        default=Sentiment.NEUTRAL, description="Detected user sentiment"
    )
    latest_user_feedback: Optional[str] = Field(
        default=None, description="Most recent user response"
    )

    @field_validator("context_history")
    @classmethod
    def validate_context_size(cls, v: List[ContextEntry]) -> List[ContextEntry]:
        """Ensure context_history doesn't exceed reasonable size (prevent token bloat)."""
        max_size = HeuristicThresholds.CONTEXT_HISTORY_MAX_SIZE
        truncate_to = HeuristicThresholds.CONTEXT_HISTORY_TRUNCATE_TO
        if len(v) > max_size:
            logger.warning(
                f"context_history exceeds {max_size} entries; truncating to last {truncate_to} entries"
            )
            return v[-truncate_to:]
        return v


class AgentOutput(BaseModel):
    """Agent's structured output (JSON-safe, API-ready)."""

    ticket_id: str = Field(..., description="Reference to input ticket")
    phase: Phase = Field(..., description="Current phase")
    summary: str = Field(
        ..., min_length=1, max_length=500, description="Agent explanation (plain language)"
    )
    reasoning: str = Field(
        ..., min_length=1, max_length=300, description="Why we said what we said"
    )
    next_step: str = Field(
        ..., min_length=1, max_length=300, description="What user should do next"
    )
    tone_applied: ToneApplied = Field(..., description="Tone used in this response")
    sentiment_detected: Sentiment = Field(..., description="User sentiment detected")
    user_learning_tip: Optional[str] = Field(
        default=None,
        max_length=250,
        description="Preventive tip (only on resolution phase)",
    )
    model_used: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0", description="AWS Bedrock model used for generation"
    )
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("user_learning_tip")
    @classmethod
    def learning_tip_only_on_resolve(cls, v: Optional[str], info) -> Optional[str]:
        """Validate: learning tips only appear on RESOLVED phase."""
        if v is not None and info.data.get("phase") != Phase.RESOLVED:
            raise ValueError("user_learning_tip should only be set on RESOLVED phase")
        return v

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary (JSON-serializable)."""
        return self.model_dump()

    def to_json(self) -> str:
        """Convert to JSON string."""
        return self.model_dump_json()


# ============================================================================
# AGENT CORE CLASS
# ============================================================================


class Agent:
    """
    TicketGlass Agent - Context-aware reasoning engine for IT support.

    Maintains per-ticket memory, detects sentiment, and generates empathetic,
    never-repeating explanations using AWS Bedrock.

    Example:
        >>> agent = Agent(system_prompt="...", model_id="anthropic.claude-3-sonnet-20240229-v1:0")
        >>> ticket = TicketState(
        ...     ticket_id="TKT-001",
        ...     user_name="Sarah",
        ...     initial_issue="WiFi won't connect",
        ...     current_phase=Phase.DIAGNOSED,
        ...     context_history=[...],
        ...     user_sentiment=Sentiment.FRUSTRATED
        ... )
        >>> output = agent.process_ticket(ticket)
        >>> print(output.summary)
    """

    def __init__(
        self,
        system_prompt: Optional[str] = None,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        aws_region: str = "us-east-1",
    ):
        """
        Initialize the Agent for AWS Bedrock.

        Args:
            system_prompt: Core system prompt (defaults to extracted prompt from agent_prompts)
            model_id: AWS Bedrock model ID (default: Claude 3 Sonnet)
            aws_region: AWS region for Bedrock (default: us-east-1)

        Raises:
            ValueError: If system_prompt is empty
        """
        # Use extracted system prompt if not provided
        if system_prompt is None:
            system_prompt = get_system_prompt()

        if not system_prompt or not system_prompt.strip():
            raise ValueError("system_prompt cannot be empty")

        self.system_prompt = system_prompt.strip()
        self.model_id = model_id
        self.aws_region = aws_region

        # Initialize AWS Bedrock client
        self.bedrock_client = boto3.client(
            "bedrock-runtime",
            region_name=self.aws_region
        )

        logger.info(
            f"Agent initialized with model: {self.model_id} "
            f"(region: {self.aws_region}, prompt length: {len(self.system_prompt)} chars)"
        )

    def process_ticket(self, ticket: TicketState) -> AgentOutput:
        """
        Process a ticket through the agent reasoning pipeline.

        Steps:
        1. Validate input ticket state
        2. Scan context_history to extract what's been tried
        3. Detect sentiment from latest user feedback
        4. Generate response that avoids repetition
        5. Match tone to user sentiment
        6. Return structured output

        Args:
            ticket: Full ticket state with context history

        Returns:
            AgentOutput: Structured agent response (JSON-safe)

        Raises:
            ValueError: If ticket validation fails
        """
        # Validate input
        if not isinstance(ticket, TicketState):
            raise TypeError(f"Expected TicketState, got {type(ticket)}")

        logger.info(f"Processing ticket {ticket.ticket_id} (phase: {ticket.current_phase})")

        # Extract previous attempts from context
        previous_attempts = self._extract_previous_attempts(ticket.context_history)

        # Detect sentiment (enhanced by latest feedback)
        sentiment = self._detect_sentiment(
            ticket.user_sentiment, ticket.latest_user_feedback
        )

        # Determine tone to apply
        tone = self._determine_tone(ticket.current_phase, sentiment)

        # Build context-aware prompt (avoid repetition)
        user_context = self._build_user_context(ticket, previous_attempts)

        # Generate response via Bedrock
        response_text = self._call_bedrock(
            ticket=ticket,
            user_context=user_context,
            tone=tone,
            sentiment=sentiment,
        )

        # Parse and validate response
        output = self._parse_response(
            response_text=response_text,
            ticket=ticket,
            tone=tone,
            sentiment=sentiment,
        )

        logger.info(f"Generated response for {ticket.ticket_id}: {tone}")

        return output

    def _extract_previous_attempts(
        self, context_history: List[ContextEntry]
    ) -> Dict[str, Any]:
        """
        Extract what's already been tried to avoid repetition.

        Args:
            context_history: List of previous context entries

        Returns:
            Dictionary with keys: attempted_fixes, user_responses, escalations
        """
        if not context_history:
            return {
                "attempted_fixes": [],
                "user_responses": [],
                "escalations": [],
            }

        attempted_fixes = [entry.what_we_said for entry in context_history]
        user_responses = [entry.what_user_said_back for entry in context_history]
        escalations = [
            entry.our_reasoning
            for entry in context_history
            if "escalat" in entry.our_reasoning.lower()
        ]

        return {
            "attempted_fixes": attempted_fixes,
            "user_responses": user_responses,
            "escalations": escalations,
        }

    def _detect_sentiment(
        self,
        initial_sentiment: Sentiment,
        latest_feedback: Optional[str],
    ) -> Sentiment:
        """
        Detect or refine sentiment from user feedback using keyword heuristics.

        Args:
            initial_sentiment: Pre-detected sentiment
            latest_feedback: Most recent user message

        Returns:
            Refined Sentiment

        Logic:
        1. If no feedback, return initial sentiment
        2. Scan feedback for sentiment keywords (from agent_keywords module)
        3. Return most likely sentiment
        """
        if not latest_feedback:
            return initial_sentiment

        feedback_lower = latest_feedback.lower()

        # Check for frustrated keywords
        frustrated_keywords = get_sentiment_keywords("frustrated")
        if any(word in feedback_lower for word in frustrated_keywords):
            logger.debug(f"Sentiment detected: frustrated (feedback: {len(latest_feedback)} chars)")
            return Sentiment.FRUSTRATED

        # Check for satisfied keywords
        satisfied_keywords = get_sentiment_keywords("satisfied")
        if any(word in feedback_lower for word in satisfied_keywords):
            logger.debug(f"Sentiment detected: satisfied (feedback: {len(latest_feedback)} chars)")
            return Sentiment.SATISFIED

        # Check for confused keywords
        confused_keywords = get_sentiment_keywords("confused")
        if any(word in feedback_lower for word in confused_keywords):
            logger.debug(f"Sentiment detected: confused (feedback: {len(latest_feedback)} chars)")
            return Sentiment.CONFUSED

        logger.debug(f"Sentiment: neutral (no keywords matched, feedback: {len(latest_feedback)} chars)")
        return initial_sentiment

    def _determine_tone(self, phase: Phase, sentiment: Sentiment) -> ToneApplied:
        """
        Determine which tone to apply based on phase and sentiment.

        Args:
            phase: Current ticket phase
            sentiment: Detected user sentiment

        Returns:
            ToneApplied: Tone to use in response
        """
        # Resolution phase: celebratory
        if phase == Phase.RESOLVED:
            return ToneApplied.CELEBRATORY

        # Frustrated users get empathetic tone
        if sentiment == Sentiment.FRUSTRATED:
            return ToneApplied.EMPATHETIC

        # Confused users get simplified tone
        if sentiment == Sentiment.CONFUSED:
            return ToneApplied.SIMPLIFIED

        # Escalation phase or later: escalation tone
        if phase in [Phase.DIAGNOSED, Phase.RESOLVED]:
            return ToneApplied.ESCALATION

        # Default: initial/professional tone
        return ToneApplied.INITIAL

    def _build_user_context(
        self,
        ticket: TicketState,
        previous_attempts: Dict[str, Any],
    ) -> str:
        """
        Build context string for Bedrock inference, highlighting what NOT to repeat.

        Args:
            ticket: Full ticket state
            previous_attempts: Extracted attempts to avoid

        Returns:
            Formatted context string for Bedrock
        """
        context_parts = [
            f"User: {ticket.user_name}",
            f"Issue: {ticket.initial_issue}",
            f"Phase: {ticket.current_phase.value}",
        ]

        # Add what we've already tried
        if previous_attempts["attempted_fixes"]:
            context_parts.append("---PREVIOUS ATTEMPTS---")
            for i, fix in enumerate(previous_attempts["attempted_fixes"], 1):
                context_parts.append(f"{i}. {fix}")

        # Add what user said in response
        if previous_attempts["user_responses"]:
            context_parts.append("---USER RESPONSES---")
            for i, response in enumerate(previous_attempts["user_responses"], 1):
                context_parts.append(f"{i}. {response}")

        # Add sentiment
        context_parts.append(f"---USER SENTIMENT---")
        context_parts.append(f"Detected: {ticket.user_sentiment.value}")
        if ticket.latest_user_feedback:
            context_parts.append(f'Latest: "{ticket.latest_user_feedback}"')

        # Add critical instruction
        context_parts.append("---CRITICAL---")
        context_parts.append(
            "NEVER repeat the previous attempts above. If a fix didn't work (user said so), "
            "move to a DIFFERENT approach. Show you're listening."
        )

        return "\n".join(context_parts)

    def _call_bedrock(
        self,
        ticket: TicketState,
        user_context: str,
        tone: ToneApplied,
        sentiment: Sentiment,
    ) -> str:
        """
        Call AWS Bedrock with context-aware prompt.

        Uses the Bedrock Runtime API to invoke Claude model.
        Logs structured metadata about the call for observability.

        Args:
            ticket: Full ticket state
            user_context: Built context string
            tone: Tone to apply
            sentiment: User sentiment

        Returns:
            Raw response text from Bedrock

        Raises:
            RuntimeError: If Bedrock API call fails
        """
        # Build the user message
        tone_str = tone.value
        tone_instruction = TONE_INSTRUCTIONS.get(
            tone_str,
            f"Apply {tone_str} tone to your response.",
        )

        user_message = f"""
You are helping an IT support agent communicate with this user.

{user_context}

{tone_instruction}

Generate a response for this ticket following the system prompt rules.
Output ONLY valid JSON (no markdown, no code blocks).
Structure: {{"summary": "...", "reasoning": "...", "next_step": "...", "user_learning_tip": "..." or null}}

Keep summary under 100 words. Plain language, warm tone. Use "we/team" language.
"""

        try:
            # Log Bedrock call details
            logger.info(
                f"Bedrock API call: ticket={ticket.ticket_id}, phase={ticket.current_phase.value}, "
                f"tone={tone_str}, sentiment={sentiment.value}, context_entries={len(ticket.context_history)}, "
                f"context_len={len(user_context)}, message_len={len(user_message)}"
            )

            # Build messages for Bedrock Claude
            messages = [{"role": "user", "content": user_message}]

            # Call Bedrock Runtime
            response = self.bedrock_client.invoke_model(
                modelId=self.model_id,
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-06-01",
                    "max_tokens": HeuristicThresholds.CLAUDE_MAX_TOKENS,
                    "system": get_system_prompt(),
                    "messages": messages,
                }),
            )

            # Parse Bedrock response
            response_body = json.loads(response["body"].read())
            response_text = response_body["content"][0]["text"]
            
            # Extract token usage if available
            input_tokens = response_body.get("usage", {}).get("input_tokens", 0)
            output_tokens = response_body.get("usage", {}).get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Log successful response
            logger.info(
                f"Bedrock API response: ticket={ticket.ticket_id}, "
                f"input_tokens={input_tokens}, "
                f"output_tokens={output_tokens}, "
                f"total_tokens={total_tokens}, response_len={len(response_text)}"
            )

            return response_text

        except Exception as e:
            logger.error(
                f"Bedrock API error for ticket {ticket.ticket_id}: {type(e).__name__}: {e}"
            )
            raise RuntimeError(f"Failed to generate response via Bedrock: {e}") from e

    def _parse_response(
        self,
        response_text: str,
        ticket: TicketState,
        tone: ToneApplied,
        sentiment: Sentiment,
    ) -> AgentOutput:
        """
        Parse Bedrock's response and create AgentOutput.

        Args:
            response_text: Raw text from Bedrock
            ticket: Original ticket state
            tone: Applied tone
            sentiment: Detected sentiment

        Returns:
            AgentOutput: Validated structured output

        Raises:
            ValueError: If response cannot be parsed
        """
        try:
            # Extract JSON (handle potential markdown wrapping)
            response_text = response_text.strip()
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()

            response_dict = json.loads(response_text)

            # Build AgentOutput
            output = AgentOutput(
                ticket_id=ticket.ticket_id,
                phase=ticket.current_phase,
                summary=response_dict.get("summary", "").strip(),
                reasoning=response_dict.get("reasoning", "").strip(),
                next_step=response_dict.get("next_step", "").strip(),
                tone_applied=tone,
                sentiment_detected=sentiment,
                user_learning_tip=response_dict.get("user_learning_tip"),
                model_used=self.model_id,
            )

            return output

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Failed to parse Bedrock response: {e}")
            logger.error(f"Response text: {response_text[:200]}")
            raise ValueError(f"Invalid response from Bedrock: {e}") from e

    def validate_no_repetition(
        self,
        new_summary: str,
        context_history: List[ContextEntry],
    ) -> bool:
        """
        Validate that new_summary doesn't repeat previous explanations.

        Uses shared keyword_overlap_ratio() helper for DRY principle.

        Args:
            new_summary: Newly generated summary
            context_history: Previous attempts

        Returns:
            True if no repetition detected, False otherwise

        Logic:
        - Calculate overlap ratio between new summary and each previous summary
        - If any overlap > REPETITION_OVERLAP_THRESHOLD, return False
        - Otherwise return True
        """
        if not context_history:
            return True

        threshold = HeuristicThresholds.REPETITION_OVERLAP_THRESHOLD

        for entry in context_history:
            overlap = keyword_overlap_ratio(new_summary, entry.what_we_said)
            if overlap > threshold:
                logger.warning(
                    f"High overlap detected: {overlap:.1%} (threshold: {threshold:.1%}, "
                    f"prev_summary: {len(entry.what_we_said)} chars)"
                )
                return False

        logger.debug(
            f"Repetition check passed ({len(context_history)} history entries, "
            f"new summary: {len(new_summary)} chars)"
        )
        return True


# ============================================================================
# MAIN (Example usage)
# ============================================================================


if __name__ == "__main__":
    # Example: Create agent and process a ticket
    system_prompt = """
You are TicketGlass, an agentic AI system that helps IT support teams communicate.
Always use "we/team" language. Match user tone. NEVER repeat previous explanations.
Output ONLY JSON with: summary, reasoning, next_step, user_learning_tip (or null).
"""

    agent = Agent(system_prompt=system_prompt, model_id="anthropic.claude-3-sonnet-20240229-v1:0")

    # Example ticket
    ticket = TicketState(
        ticket_id="TKT-001",
        user_name="Sarah",
        initial_issue="WiFi won't connect",
        current_phase=Phase.DIAGNOSED,
        context_history=[
            ContextEntry(
                phase=1,
                timestamp="2025-10-18T09:00:00Z",
                what_we_said="Let's clear your DNS cache using these steps...",
                what_user_said_back="Tried it. WiFi still won't connect.",
                our_reasoning="DNS fix didn't work, so likely adapter or driver issue",
            )
        ],
        user_sentiment=Sentiment.FRUSTRATED,
        latest_user_feedback="Tried it. WiFi still won't connect.",
    )

    # Process
    output = agent.process_ticket(ticket)
    print(output.to_json())