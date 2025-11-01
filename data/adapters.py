"""
TicketGlass Data Adapters - Swappable data sources

Adapter pattern implementation:
- Abstract base: TicketDataAdapter
- Mock implementation: MockTicketAdapter
- Post-MVP: SuperOpsAdapter, ZendeskAdapter, ServiceNowAdapter

Enables:
- Swap mock data ↔ real PSA API with 1-line change
- No agent code changes when switching data sources
- Easy testing (use mock in tests, real API in production)
- Multi-tenant ready (add tenant filtering in adapter)

Design:
- Adapters handle data fetching + storage
- Agent calls adapter methods (zero data layer dependency)
- Each adapter returns consistent TicketState format
- Errors handled gracefully with structured responses
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


# ============================================================================
# LOGGING
# ============================================================================

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# ============================================================================
# DATA MODELS (Shared across all adapters)
# ============================================================================


@dataclass
class StatusEvent:
    """Single status event in a ticket's history."""

    time: str  # HH:MM format
    phase: str  # Received, Assigned, Diagnosed, Escalated, Resolved
    event: str  # Human-readable event description
    summary: Optional[str] = None  # Agent summary at this phase
    user_feedback: Optional[str] = None  # User's response to summary
    resolution: Optional[str] = None  # Final resolution (if Resolved phase)
    learning_tip: Optional[str] = None  # Learning tip (if Resolved phase)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class TicketState:
    """
    Data layer representation of ticket state (in-memory storage format).

    IMPORTANT: This is DIFFERENT from agent.core.TicketState (Pydantic model).

    This class is used by the DATA LAYER (adapters):
    - MockTicketAdapter stores tickets in this format
    - Real adapters (SuperOps, Zendesk) will use this format
    - Data is stored as-is without transformation

    The AGENT LAYER uses agent.core.TicketState (Pydantic):
    - agent/core.py defines its own TicketState
    - Different structure optimized for reasoning
    - Type-validated with Pydantic

    In the UI (ui/app.py line 24), we import this as:
        from data.adapters import TicketState as AdapterTicketState
    
    This avoids collision with:
        from agent.core import TicketState  # (Pydantic model)

    The UI converts between these two representations:
    1. adapter.fetch_ticket_state() returns data.adapters.TicketState
    2. mock_to_ticketstate() converts to agent.core.TicketState
    3. Agent.process_ticket() works with agent.core.TicketState

    See ARCHITECTURE_HARMONY_CHECK.md for detailed data flow diagrams.
    """

    ticket_id: str
    category: str  # Software, Hardware, Network, Access, Email
    title: str
    user_name: str
    user_tone: str  # frustrated, satisfied, neutral
    status_events: List[StatusEvent] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def get_context_history(self) -> List[Dict[str, Any]]:
        """
        Extract context history from status events.

        Returns what was already said and what user said back.
        """
        history = []
        for event in self.status_events:
            if event.summary or event.user_feedback:
                history.append(
                    {
                        "phase": event.phase,
                        "time": event.time,
                        "what_we_said": event.summary,
                        "user_response": event.user_feedback,
                    }
                )
        return history

    def get_current_phase(self) -> str:
        """Get the current phase (last status event)."""
        if not self.status_events:
            return "Received"
        return self.status_events[-1].phase

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "ticket_id": self.ticket_id,
            "category": self.category,
            "title": self.title,
            "user_name": self.user_name,
            "user_tone": self.user_tone,
            "status_events": [event.to_dict() for event in self.status_events],
            "created_at": self.created_at,
            "context_history": self.get_context_history(),
            "current_phase": self.get_current_phase(),
        }


# ============================================================================
# ABSTRACT BASE ADAPTER
# ============================================================================


class TicketDataAdapter(ABC):
    """
    Abstract base for all ticket data adapters.

    Subclasses must implement:
    - fetch_ticket_state(ticket_id)
    - store_feedback(ticket_id, feedback, sentiment)
    - get_all_tickets()
    """

    @abstractmethod
    def fetch_ticket_state(self, ticket_id: str) -> Optional[TicketState]:
        """
        Fetch ticket state by ID.

        Args:
            ticket_id: Ticket identifier (e.g., "TKT-001")

        Returns:
            TicketState if found, None otherwise
        """
        pass

    @abstractmethod
    def store_feedback(
        self, ticket_id: str, feedback: str, sentiment: str
    ) -> bool:
        """
        Store user feedback on current phase's summary.

        Args:
            ticket_id: Ticket ID
            feedback: User's feedback text
            sentiment: User sentiment (frustrated, satisfied, neutral)

        Returns:
            True if stored successfully, False otherwise
        """
        pass

    @abstractmethod
    def get_all_tickets(self) -> Dict[str, TicketState]:
        """
        Get all tickets (for UI dropdown, testing, etc.).

        Returns:
            Dictionary of ticket_id -> TicketState
        """
        pass

    @abstractmethod
    def update_context_history(
        self, ticket_id: str, summary: str, phase: str
    ) -> bool:
        """
        Update context history with agent-generated summary.

        Args:
            ticket_id: Ticket ID
            summary: Agent-generated summary
            phase: Current phase

        Returns:
            True if updated successfully
        """
        pass


# ============================================================================
# MOCK ADAPTER (MVP Implementation)
# ============================================================================


class MockTicketAdapter(TicketDataAdapter):
    """
    Mock adapter for MVP.

    Stores all tickets in memory.
    Suitable for:
    - Local development
    - Testing
    - Hackathon demo
    - Zero external dependencies

    Post-MVP: Replace with SuperOpsAdapter, ZendeskAdapter, etc.
    """

    def __init__(self):
        """Initialize with empty ticket store."""
        self.tickets: Dict[str, TicketState] = {}
        self.feedback_store: Dict[str, List[Dict[str, str]]] = {}
        logger.info("MockTicketAdapter initialized")

    def fetch_ticket_state(self, ticket_id: str) -> Optional[TicketState]:
        """Fetch ticket from in-memory store."""
        ticket = self.tickets.get(ticket_id)
        if ticket:
            logger.info(f"Fetched ticket {ticket_id} from mock store")
            return ticket
        logger.warning(f"Ticket {ticket_id} not found in mock store")
        return None

    def store_feedback(
        self, ticket_id: str, feedback: str, sentiment: str
    ) -> bool:
        """Store feedback in memory."""
        if ticket_id not in self.feedback_store:
            self.feedback_store[ticket_id] = []

        self.feedback_store[ticket_id].append(
            {
                "feedback": feedback,
                "sentiment": sentiment,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        logger.info(f"Stored feedback for {ticket_id}: sentiment={sentiment}")
        return True

    def get_all_tickets(self) -> Dict[str, TicketState]:
        """Return all tickets."""
        logger.info(f"Retrieved {len(self.tickets)} tickets from mock store")
        return self.tickets

    def update_context_history(
        self, ticket_id: str, summary: str, phase: str
    ) -> bool:
        """Add summary to last status event's context."""
        ticket = self.tickets.get(ticket_id)
        if not ticket:
            logger.error(f"Cannot update context: ticket {ticket_id} not found")
            return False

        if not ticket.status_events:
            logger.error(f"Cannot update context: ticket {ticket_id} has no events")
            return False

        # Update the last event's summary
        ticket.status_events[-1].summary = summary
        logger.info(
            f"Updated context history for {ticket_id} at phase {phase}"
        )
        return True

    def load_tickets(self, tickets_dict: Dict[str, Dict[str, Any]]) -> None:
        """
        Load tickets from dictionary.

        Used to populate mock store with initial data.

        Args:
            tickets_dict: Dictionary of ticket_id -> ticket_data
        """
        for ticket_id, ticket_data in tickets_dict.items():
            # Convert status_events dicts to StatusEvent objects
            events = [
                StatusEvent(**event) for event in ticket_data.get("status_events", [])
            ]

            ticket = TicketState(
                ticket_id=ticket_data["ticket_id"],
                category=ticket_data["category"],
                title=ticket_data["title"],
                user_name=ticket_data["user_name"],
                user_tone=ticket_data["user_tone"],
                status_events=events,
            )
            self.tickets[ticket_id] = ticket

        logger.info(f"Loaded {len(self.tickets)} tickets into mock adapter")

    def get_feedback(self, ticket_id: str) -> List[Dict[str, str]]:
        """Get all feedback for a ticket."""
        return self.feedback_store.get(ticket_id, [])

    def get_analytics(self) -> Dict[str, Any]:
        """Simple analytics for all tickets."""
        total_responses = sum(len(v) for v in self.feedback_store.values())
        if total_responses == 0:
            return {
                "total_responses": 0,
                "helpful_count": 0,
                "helpful_percentage": 0,
            }

        helpful_count = sum(
            1
            for feedback_list in self.feedback_store.values()
            for feedback in feedback_list
            if "helpful" in feedback.get("sentiment", "").lower()
            or feedback.get("sentiment") == "satisfied"
        )

        return {
            "total_responses": total_responses,
            "helpful_count": helpful_count,
            "helpful_percentage": round((helpful_count / total_responses * 100), 1),
        }


# ============================================================================
# POST-MVP ADAPTER TEMPLATES (For reference)
# ============================================================================


class SuperOpsAdapter(TicketDataAdapter):
    """
    SuperOps API adapter (POST-MVP).

    When ready to integrate with real PSA:
    1. Initialize with API credentials
    2. Swap 1 line: adapter = SuperOpsAdapter(credentials)
    3. Rest of code unchanged
    """

    def __init__(self, superops_api_key: str, superops_account_id: str):
        """Initialize with SuperOps credentials."""
        self.api_key = superops_api_key
        self.account_id = superops_account_id
        # self.client = superops.Client(api_key, account_id)  # POST-MVP
        logger.info("SuperOpsAdapter initialized (POST-MVP)")

    def fetch_ticket_state(self, ticket_id: str) -> Optional[TicketState]:
        """Fetch ticket from SuperOps API (POST-MVP)."""
        # response = self.client.tickets.get(ticket_id)
        # return self._parse_superops_response(response)
        raise NotImplementedError("SuperOpsAdapter is POST-MVP")

    def store_feedback(self, ticket_id: str, feedback: str, sentiment: str) -> bool:
        """Store feedback in SuperOps (POST-MVP)."""
        # self.client.tickets.add_comment(ticket_id, feedback, metadata={"sentiment": sentiment})
        raise NotImplementedError("SuperOpsAdapter is POST-MVP")

    def get_all_tickets(self) -> Dict[str, TicketState]:
        """Get all tickets from SuperOps (POST-MVP)."""
        raise NotImplementedError("SuperOpsAdapter is POST-MVP")

    def update_context_history(
        self, ticket_id: str, summary: str, phase: str
    ) -> bool:
        """Update ticket context in SuperOps (POST-MVP)."""
        raise NotImplementedError("SuperOpsAdapter is POST-MVP")


class ZendeskAdapter(TicketDataAdapter):
    """Zendesk API adapter (POST-MVP)."""

    def __init__(self, zendesk_subdomain: str, zendesk_api_token: str):
        """Initialize with Zendesk credentials."""
        self.subdomain = zendesk_subdomain
        self.api_token = zendesk_api_token
        logger.info("ZendeskAdapter initialized (POST-MVP)")

    def fetch_ticket_state(self, ticket_id: str) -> Optional[TicketState]:
        raise NotImplementedError("ZendeskAdapter is POST-MVP")

    def store_feedback(self, ticket_id: str, feedback: str, sentiment: str) -> bool:
        raise NotImplementedError("ZendeskAdapter is POST-MVP")

    def get_all_tickets(self) -> Dict[str, TicketState]:
        raise NotImplementedError("ZendeskAdapter is POST-MVP")

    def update_context_history(
        self, ticket_id: str, summary: str, phase: str
    ) -> bool:
        raise NotImplementedError("ZendeskAdapter is POST-MVP")


# ============================================================================
# ADAPTER FACTORY (For easy switching)
# ============================================================================


def get_adapter(adapter_type: str = "mock", **kwargs) -> TicketDataAdapter:
    """
    Factory function to get adapter instance.

    Args:
        adapter_type: "mock", "superops", "zendesk", "servicenow"
        **kwargs: Credentials for non-mock adapters

    Returns:
        TicketDataAdapter instance

    Example:
        # MVP (local development)
        >>> adapter = get_adapter("mock")

        # Post-MVP (live deployment)
        >>> adapter = get_adapter("superops", api_key="...", account_id="...")
    """
    if adapter_type == "mock":
        return MockTicketAdapter()
    elif adapter_type == "superops":
        return SuperOpsAdapter(
            superops_api_key=kwargs.get("api_key"),
            superops_account_id=kwargs.get("account_id"),
        )
    elif adapter_type == "zendesk":
        return ZendeskAdapter(
            zendesk_subdomain=kwargs.get("subdomain"),
            zendesk_api_token=kwargs.get("api_token"),
        )
    else:
        raise ValueError(f"Unknown adapter type: {adapter_type}")


if __name__ == "__main__":
    # Example usage
    print("TicketGlass Data Adapters")
    print("=" * 60)
    print("\nAdapter types:")
    print("  - mock: In-memory (MVP)")
    print("  - superops: SuperOps API (POST-MVP)")
    print("  - zendesk: Zendesk API (POST-MVP)")
    print("  - servicenow: ServiceNow API (POST-MVP)")
    print("\nUsage:")
    print("  adapter = get_adapter('mock')")
    print("  ticket = adapter.fetch_ticket_state('TKT-001')")