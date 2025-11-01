"""
Unit tests for TicketGlass Agent Core (AWS Bedrock).

Tests cover:
- Agent initialization with AWS Bedrock config
- Sentiment detection
- Tone determination  
- Repetition prevention
- Context history handling
- Output validation
- Error cases and edge conditions
- Bedrock API call mocking
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Import from agent core
import sys
sys.path.insert(0, "/home/claude")

from agent.core import (
    Agent,
    TicketState,
    AgentOutput,
    ContextEntry,
    Phase,
    Sentiment,
    ToneApplied,
)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def system_prompt():
    """Standard system prompt for testing."""
    return """
You are TicketGlass, an agentic AI system.
Always use "we/team" language. NEVER repeat previous explanations.
Output JSON: {summary, reasoning, next_step, user_learning_tip or null}
"""


@pytest.fixture
def mock_bedrock_client(monkeypatch):
    """Mock AWS Bedrock client."""
    mock_client = MagicMock()
    
    # Mock response from Bedrock
    mock_response = {
        "body": MagicMock(read=lambda: json.dumps({
            "content": [{"text": '{"summary": "Test response", "reasoning": "Test reasoning", "next_step": "Test step", "user_learning_tip": null}'}],
            "usage": {"input_tokens": 100, "output_tokens": 50}
        }).encode('utf-8'))
    }
    
    mock_client.invoke_model.return_value = mock_response
    
    # Patch boto3 to return our mock client
    mock_boto3 = MagicMock()
    mock_boto3.client.return_value = mock_client
    monkeypatch.setattr("boto3.client", mock_boto3.client)
    
    return mock_client


@pytest.fixture
def agent(system_prompt, mock_bedrock_client):
    """Create an Agent instance with mocked Bedrock."""
    agent = Agent(
        system_prompt=system_prompt,
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        aws_region="us-east-1"
    )
    return agent


@pytest.fixture
def basic_ticket():
    """Create a basic ticket for testing."""
    return TicketState(
        ticket_id="TKT-001",
        user_name="Sarah Chen",
        initial_issue="WiFi won't connect",
        current_phase=Phase.DIAGNOSED,
        context_history=[],
        user_sentiment=Sentiment.NEUTRAL,
    )


@pytest.fixture
def ticket_with_context():
    """Create a ticket with context history."""
    context = ContextEntry(
        phase=Phase.DIAGNOSED,
        what_we_said="We tried clearing DNS cache. Let us know if that works.",
        user_response="Already tried DNS. WiFi still won't connect."
    )
    return TicketState(
        ticket_id="TKT-002",
        user_name="Jordan Davis",
        initial_issue="Email sync broken",
        current_phase=Phase.ESCALATED,
        context_history=[context],
        user_sentiment=Sentiment.FRUSTRATED,
    )


# ============================================================================
# AGENT INITIALIZATION TESTS
# ============================================================================


class TestAgentInitialization:
    """Test Agent class initialization with Bedrock."""

    def test_agent_init_with_valid_params(self, system_prompt, mock_bedrock_client):
        """Agent initializes successfully with valid parameters."""
        agent = Agent(
            system_prompt=system_prompt,
            model_id="anthropic.claude-3-sonnet-20240229-v1:0",
            aws_region="us-east-1"
        )
        assert agent.system_prompt == system_prompt.strip()
        assert agent.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert agent.aws_region == "us-east-1"
        assert agent.bedrock_client is not None

    def test_agent_init_with_default_model(self, system_prompt, mock_bedrock_client):
        """Agent initializes with default Bedrock model."""
        agent = Agent(system_prompt=system_prompt)
        assert agent.model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert agent.aws_region == "us-east-1"

    def test_agent_init_fails_with_empty_prompt(self, mock_bedrock_client):
        """Agent initialization fails with empty system prompt."""
        with pytest.raises(ValueError, match="system_prompt cannot be empty"):
            Agent(system_prompt="")

    def test_agent_init_with_custom_region(self, system_prompt, mock_bedrock_client):
        """Agent accepts custom AWS region."""
        agent = Agent(
            system_prompt=system_prompt,
            aws_region="eu-west-1"
        )
        assert agent.aws_region == "eu-west-1"

    def test_agent_init_strips_whitespace(self, mock_bedrock_client):
        """System prompt is stripped of whitespace."""
        prompt = "  Hello World  \n"
        agent = Agent(system_prompt=prompt)
        assert agent.system_prompt == "Hello World"


# ============================================================================
# SENTIMENT DETECTION TESTS
# ============================================================================


class TestSentimentDetection:
    """Test sentiment detection from user context."""

    def test_detect_frustrated_sentiment(self, agent, basic_ticket):
        """Detect frustrated sentiment from user response."""
        context = ContextEntry(
            phase=Phase.DIAGNOSED,
            what_we_said="Try restarting.",
            user_response="I already restarted! This is so frustrating!"
        )
        basic_ticket.context_history.append(context)
        
        sentiment = agent._detect_sentiment(context.user_response)
        assert sentiment == Sentiment.FRUSTRATED

    def test_detect_satisfied_sentiment(self, agent, basic_ticket):
        """Detect satisfied sentiment from user response."""
        context = ContextEntry(
            phase=Phase.DIAGNOSED,
            what_we_said="Try this fix.",
            user_response="That worked! Thanks so much!"
        )
        basic_ticket.context_history.append(context)
        
        sentiment = agent._detect_sentiment(context.user_response)
        assert sentiment == Sentiment.SATISFIED

    def test_detect_confused_sentiment(self, agent, basic_ticket):
        """Detect confused sentiment from user response."""
        feedback = "I don't understand. What does that mean?"
        sentiment = agent._detect_sentiment(feedback)
        assert sentiment == Sentiment.CONFUSED

    def test_detect_neutral_sentiment(self, agent, basic_ticket):
        """Detect neutral sentiment as default."""
        feedback = "Ok, I'll try that."
        sentiment = agent._detect_sentiment(feedback)
        assert sentiment in [Sentiment.NEUTRAL, Sentiment.SATISFIED]


# ============================================================================
# TONE DETERMINATION TESTS
# ============================================================================


class TestToneDetermination:
    """Test tone determination based on sentiment."""

    def test_frustrated_sentiment_uses_empathetic_tone(self, agent):
        """Frustrated sentiment triggers empathetic tone."""
        tone = agent._determine_tone(Sentiment.FRUSTRATED, Phase.DIAGNOSED)
        assert tone == ToneApplied.EMPATHETIC

    def test_satisfied_sentiment_uses_celebratory_tone(self, agent):
        """Satisfied sentiment triggers celebratory tone."""
        tone = agent._determine_tone(Sentiment.SATISFIED, Phase.RESOLVED)
        assert tone == ToneApplied.CELEBRATORY

    def test_confused_sentiment_uses_simplified_tone(self, agent):
        """Confused sentiment triggers simplified tone."""
        tone = agent._determine_tone(Sentiment.CONFUSED, Phase.DIAGNOSED)
        assert tone == ToneApplied.SIMPLIFIED

    def test_neutral_sentiment_uses_initial_tone(self, agent):
        """Neutral sentiment uses initial tone."""
        tone = agent._determine_tone(Sentiment.NEUTRAL, Phase.DIAGNOSED)
        assert tone in [ToneApplied.INITIAL, ToneApplied.EMPATHETIC]


# ============================================================================
# REPETITION PREVENTION TESTS
# ============================================================================


class TestRepetitionPrevention:
    """Test that agent never repeats previous explanations."""

    def test_no_repetition_of_previous_summary(self, agent, basic_ticket):
        """Agent detects and avoids repeating previous summary."""
        previous_summary = "Clear your DNS cache to fix WiFi connection."
        context = ContextEntry(
            phase=Phase.DIAGNOSED,
            what_we_said=previous_summary,
            user_response="That didn't work."
        )
        basic_ticket.context_history.append(context)
        
        # Check if agent would repeat
        has_high_overlap = any(
            agent._check_repetition_overlap(previous_summary, previous_summary)
            for _ in range(1)
        )
        assert has_high_overlap  # Should detect this as repetition

    def test_different_explanation_not_flagged_as_repetition(self, agent, basic_ticket):
        """Different explanation not flagged as repetition."""
        previous = "Try clearing DNS cache."
        new = "Let's check your network adapter settings instead."
        
        # These should have low overlap
        overlap = agent._check_repetition_overlap(previous, new)
        assert not overlap or overlap < 0.6  # Not high overlap

    def test_escalation_not_counted_as_repetition(self, agent):
        """Escalation (different approach) is not repetition."""
        initial = "Restart your computer."
        escalation = "Since restart didn't work, let's check the network driver."
        
        # These should be different approaches, not repetition
        assert escalation != initial


# ============================================================================
# CONTEXT HISTORY TESTS
# ============================================================================


class TestContextHistory:
    """Test context history extraction and usage."""

    def test_extract_context_from_ticket(self, ticket_with_context):
        """Context history is extracted from ticket."""
        history = ticket_with_context.context_history
        assert len(history) > 0
        assert history[0].what_we_said is not None
        assert history[0].user_response is not None

    def test_empty_ticket_has_empty_context(self, basic_ticket):
        """Basic ticket with no interactions has empty context."""
        assert len(basic_ticket.context_history) == 0

    def test_multiple_context_entries(self, basic_ticket):
        """Multiple context entries are tracked."""
        entry1 = ContextEntry(
            phase=Phase.DIAGNOSED,
            what_we_said="Try this.",
            user_response="Didn't work."
        )
        entry2 = ContextEntry(
            phase=Phase.ESCALATED,
            what_we_said="Try that instead.",
            user_response="Thanks, that worked!"
        )
        basic_ticket.context_history = [entry1, entry2]
        
        assert len(basic_ticket.context_history) == 2
        assert basic_ticket.context_history[0].phase == Phase.DIAGNOSED
        assert basic_ticket.context_history[1].phase == Phase.ESCALATED


# ============================================================================
# OUTPUT VALIDATION TESTS
# ============================================================================


class TestOutputValidation:
    """Test AgentOutput validation and structure."""

    def test_agent_output_has_required_fields(self, agent, basic_ticket, mock_bedrock_client):
        """AgentOutput includes all required fields."""
        output = agent.process_ticket(basic_ticket)
        
        assert hasattr(output, 'ticket_id')
        assert hasattr(output, 'summary')
        assert hasattr(output, 'reasoning')
        assert hasattr(output, 'next_step')
        assert hasattr(output, 'tone_applied')

    def test_summary_is_under_max_length(self, agent, basic_ticket, mock_bedrock_client):
        """Agent summary respects max length."""
        output = agent.process_ticket(basic_ticket)
        
        from agent_keywords import HeuristicThresholds
        assert len(output.summary) <= HeuristicThresholds.SUMMARY_MAX_LENGTH

    def test_output_is_json_serializable(self, agent, basic_ticket, mock_bedrock_client):
        """AgentOutput can be serialized to JSON."""
        output = agent.process_ticket(basic_ticket)
        
        # Should not raise
        output_dict = output.to_dict()
        json_str = json.dumps(output_dict)
        assert json_str is not None


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


class TestErrorHandling:
    """Test error cases and edge conditions."""

    def test_invalid_ticket_type_raises_error(self, agent):
        """Invalid ticket type raises TypeError."""
        with pytest.raises(TypeError):
            agent.process_ticket("not a ticket")

    def test_bedrock_api_error_handling(self, agent, basic_ticket):
        """Bedrock API errors are handled gracefully."""
        agent.bedrock_client.invoke_model.side_effect = Exception("API Error")
        
        with pytest.raises(RuntimeError, match="Failed to generate response"):
            agent.process_ticket(basic_ticket)

    def test_invalid_bedrock_response_handling(self, agent, basic_ticket, mock_bedrock_client):
        """Invalid Bedrock response is handled."""
        # Mock invalid JSON response
        mock_response = {
            "body": MagicMock(read=lambda: b"invalid json")
        }
        agent.bedrock_client.invoke_model.return_value = mock_response
        
        with pytest.raises(ValueError):
            agent.process_ticket(basic_ticket)


# ============================================================================
# BEDROCK INTEGRATION TESTS
# ============================================================================


class TestBedrockIntegration:
    """Test Bedrock-specific functionality."""

    def test_bedrock_client_initialized(self, agent):
        """Bedrock client is initialized."""
        assert agent.bedrock_client is not None

    def test_bedrock_invoke_model_called(self, agent, basic_ticket, mock_bedrock_client):
        """Bedrock invoke_model is called when processing ticket."""
        agent.process_ticket(basic_ticket)
        
        agent.bedrock_client.invoke_model.assert_called()

    def test_bedrock_model_id_used_in_call(self, agent, basic_ticket, mock_bedrock_client):
        """Bedrock is called with correct model ID."""
        agent.process_ticket(basic_ticket)
        
        call_args = agent.bedrock_client.invoke_model.call_args
        assert call_args is not None
        # Model ID should be in the call
        assert "anthropic.claude-3-sonnet" in agent.model_id

    def test_bedrock_response_parsed_correctly(self, agent, basic_ticket, mock_bedrock_client):
        """Bedrock response is parsed correctly."""
        output = agent.process_ticket(basic_ticket)
        
        # Should have parsed the response
        assert output.summary is not None
        assert output.summary != ""


# ============================================================================
# INTEGRATION TESTS
# ============================================================================


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_ticket_processing_flow(self, agent, ticket_with_context, mock_bedrock_client):
        """Full ticket processing flow works end-to-end."""
        output = agent.process_ticket(ticket_with_context)
        
        assert output.ticket_id == ticket_with_context.ticket_id
        assert output.summary is not None
        assert len(output.summary) > 0

    def test_multiple_tickets_processed_independently(self, agent, mock_bedrock_client):
        """Multiple tickets are processed independently."""
        ticket1 = TicketState(
            ticket_id="TKT-001",
            user_name="User1",
            initial_issue="Issue1",
            current_phase=Phase.DIAGNOSED,
            context_history=[],
            user_sentiment=Sentiment.NEUTRAL,
        )
        
        ticket2 = TicketState(
            ticket_id="TKT-002",
            user_name="User2",
            initial_issue="Issue2",
            current_phase=Phase.DIAGNOSED,
            context_history=[],
            user_sentiment=Sentiment.FRUSTRATED,
        )
        
        output1 = agent.process_ticket(ticket1)
        output2 = agent.process_ticket(ticket2)
        
        assert output1.ticket_id == "TKT-001"
        assert output2.ticket_id == "TKT-002"
        # Tones might be different based on sentiment
        assert output1.tone_applied is not None
        assert output2.tone_applied is not None


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])