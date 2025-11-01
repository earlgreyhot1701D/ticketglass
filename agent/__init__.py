"""
TicketGlass Agent - Agentic reasoning engine for IT support transparency.

This package provides the Agent class and supporting utilities for generating
context-aware, never-repeating IT support explanations.

Core Components:
- Agent: Main reasoning engine
- TicketState: Pydantic model for ticket data
- AgentOutput: Response from agent processing
- Sentiment: User emotion detection
- Phase: Ticket lifecycle stages
- ToneApplied: Response tone selection

Usage:
    from agent import Agent, TicketState, Phase, Sentiment

    agent = Agent(model_id="claude-opus-4-1")
    ticket = TicketState(...)
    output = agent.process_ticket(ticket)
    print(output.summary)
"""

from agent.core import (
    Agent,
    TicketState,
    AgentOutput,
    ContextEntry,
    Phase,
    Sentiment,
    ToneApplied,
)
from agent.prompts import (
    get_system_prompt,
    get_tone_template,
    build_tone_instruction,
    TONE_TEMPLATES,
    TONE_INSTRUCTIONS,
    ToneTemplate,
)
from agent.keywords import (
    get_sentiment_keywords,
    add_sentiment_keyword,
    remove_sentiment_keyword,
    get_all_sentiment_keywords,
    HeuristicThresholds,
)

__all__ = [
    # Core
    "Agent",
    "TicketState",
    "AgentOutput",
    "ContextEntry",
    # Enums
    "Phase",
    "Sentiment",
    "ToneApplied",
    "ToneTemplate",
    # Prompts
    "get_system_prompt",
    "get_tone_template",
    "build_tone_instruction",
    "TONE_TEMPLATES",
    "TONE_INSTRUCTIONS",
    # Keywords
    "get_sentiment_keywords",
    "add_sentiment_keyword",
    "remove_sentiment_keyword",
    "get_all_sentiment_keywords",
    "HeuristicThresholds",
]

__version__ = "0.1.0"
__author__ = "TicketGlass Team"
