"""
TicketGlass - Phase 3: Streamlit UI (CUSTOMER-FACING)
Customer transparency portal for IT support tickets
Demo app for SuperHack 2025

Features:
- Real-time ticket status for customer
- Clear timeline of support progress
- What we're doing at each step
- Customer feedback mechanism
- Transparent communication

Run: streamlit run app.py
"""

import sys
import os
import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging

# Add src directory to Python path (CRITICAL: allows imports to work when streamlit runs from project root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Backend imports
from agent.core import Agent, TicketState, Phase, Sentiment, ContextEntry
from agent.prompts import get_system_prompt
from data.mock_tickets import get_mock_tickets, get_demo_ticket
from data.adapters import MockTicketAdapter, TicketState as AdapterTicketState

# Setup logging
logger = logging.getLogger(__name__)


# ============================================================================
# CONSTANTS & STYLES
# ============================================================================

# Phase status styling - single source of truth
PHASE_STYLES = {
    "completed": {"color": "#90EE90", "symbol": "✅"},
    "current": {"color": "#FFD700", "symbol": "🟡"},
    "pending": {"color": "#D3D3D3", "symbol": "⚪"},
}

# Centralized CSS with isolated class names to prevent collisions
CSS_STYLES = """
    <style>
    /* Metric box styling */
    .ticketglass-metric-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
    }
    
    /* Phase badge styling */
    .ticketglass-phase-badge {
        display: inline-block;
        padding: 5px 10px;
        border-radius: 4px;
        font-weight: bold;
        margin: 2px;
    }
    
    /* Timeline item styling */
    .ticketglass-timeline-item {
        margin: 15px 0;
        padding: 12px;
        border-left: 4px solid #ccc;
        background-color: #f9f9f9;
    }
    
    /* Agent summary box */
    .ticketglass-summary-box {
        background-color: #e8f4f8;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
        border-left: 4px solid #0099cc;
    }
    
    /* User feedback box */
    .ticketglass-feedback-box {
        background-color: #fff3cd;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0;
        border-left: 4px solid #ffc107;
    }
    </style>
"""


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = "TKT-001"

if "expanded_phases" not in st.session_state:
    st.session_state.expanded_phases = {}

if "feedback_store" not in st.session_state:
    st.session_state.feedback_store = {}


# ============================================================================
# CACHING & UTILITIES
# ============================================================================

@st.cache_resource
def get_agent() -> Agent:
    """Initialize and cache the Agent."""
    return Agent(
        system_prompt=get_system_prompt(),
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        aws_region="us-east-1"
    )


def load_ticket_data(ticket_id: str) -> Dict[str, Any]:
    """Load ticket from mock data."""
    all_tickets = get_mock_tickets()
    return all_tickets.get(ticket_id, get_demo_ticket())


def build_context_from_events(ticket_dict: Dict[str, Any]) -> List[ContextEntry]:
    """Build context history for the agent from ticket events."""
    context = []
    
    for i, event in enumerate(ticket_dict['status_events']):
        if i == 0:
            continue  # Skip first event (just received)
        
        timestamp = datetime.fromisoformat(
            f"2025-10-26T{event.get('time', '10:00:00').replace(':', '')}:00Z")
        
        context.append(ContextEntry(
            phase=i + 1,
            timestamp=timestamp,
            what_we_said=event['summary'],
            what_user_said_back=event['user_feedback'],
            our_reasoning=f"Previous attempt at {event['phase']} phase"
        ))
    
    return TicketState(
        ticket_id=ticket_dict['ticket_id'],
        user_name=ticket_dict['user_name'],
        initial_issue=ticket_dict['title'],
        current_phase=Phase(ticket_dict['status_events'][-1]['phase']),
        context_history=context,
        user_sentiment=Sentiment(ticket_dict['user_tone']),
        latest_user_feedback=ticket_dict['status_events'][-1].get('user_feedback')
    )


def get_phase_style(ticket_dict: Dict[str, Any], phase_name: str) -> Dict[str, str]:
    """Get complete style (color + symbol) for a phase."""
    phases_in_ticket = [e['phase'] for e in ticket_dict['status_events']]
    current_phase = ticket_dict['status_events'][-1]['phase']
    
    if phase_name in phases_in_ticket:
        status = "current" if phase_name == current_phase else "completed"
    else:
        status = "pending"
    
    return PHASE_STYLES[status]


# ============================================================================
# RENDERING FUNCTIONS (CUSTOMER-FACING)
# ============================================================================

def render_header(ticket_dict: Dict[str, Any]):
    """Render page header - personalized for customer."""
    customer_name = ticket_dict['user_name']
    issue_title = ticket_dict['title']
    
    st.title(f"🎫 Hi {customer_name}!")
    st.subheader(f"Your Support Ticket")
    st.markdown(f"**Issue:** {issue_title}")
    st.divider()


def render_ticket_status(ticket_dict: Dict[str, Any]):
    """Render ticket status - what customer cares about."""
    status = ticket_dict['status_events'][-1]['phase']
    
    # Status message mapping
    status_messages = {
        "Received": "✅ We got your ticket. We're looking into it.",
        "Assigned": "👨‍💼 Our team is assigned and investigating.",
        "Diagnosed": "🔍 We're figuring out what's wrong.",
        "Escalated": "⬆️ We're working with advanced support.",
        "Resolved": "✅ Issue resolved! You're all set."
    }
    
    message = status_messages.get(status, "Updating your ticket...")
    st.info(f"📊 Current Status: {message}")
    st.divider()


def render_status_bar(ticket_dict: Dict[str, Any]):
    """Render status bar with phase progression."""
    st.subheader("📈 Progress")
    
    phases = ["Received", "Assigned", "Diagnosed", "Escalated", "Resolved"]
    status_cols = st.columns(len(phases))
    
    for idx, phase in enumerate(phases):
        style = get_phase_style(ticket_dict, phase)
        color = style["color"]
        symbol = style["symbol"]
        
        with status_cols[idx]:
            st.markdown(
                f'<div style="text-align: center; padding: 8px; background-color: {color}; '
                f'border-radius: 4px; font-weight: bold;">{symbol} {phase}</div>',
                unsafe_allow_html=True
            )
    
    st.divider()


def render_timeline(ticket_dict: Dict[str, Any]):
    """
    Render timeline view - what the customer sees.
    Shows: When things happened, what we suggested, what you told us, what's next.
    """
    st.subheader("📅 Your Ticket Timeline")
    
    agent = get_agent()
    current_phase_name = ticket_dict['status_events'][-1]['phase']
    
    for event_idx, event in enumerate(ticket_dict['status_events']):
        phase = event['phase']
        time = event['time']
        summary = event.get('summary')
        user_feedback = event.get('user_feedback')
        resolution = event.get('resolution')
        learning_tip = event.get('learning_tip')
        
        # Get phase style
        style = get_phase_style(ticket_dict, phase)
        symbol = style["symbol"]
        
        is_expanded = st.session_state.expanded_phases.get(phase, False)
        
        with st.container():
            # Clickable phase header
            col1, col2 = st.columns([0.1, 0.9])
            with col1:
                st.write(symbol)
            with col2:
                if st.button(
                    f"**{time}** — {phase}",
                    key=f"phase_{phase}",
                    use_container_width=True,
                    help="Click to expand/collapse"
                ):
                    st.session_state.expanded_phases[phase] = not is_expanded
            
            # Expanded content
            if is_expanded:
                with st.container():
                    # What we're doing / what happened
                    if summary:
                        st.markdown("#### What We're Doing")
                        st.markdown(
                            f'<div class="ticketglass-summary-box">{summary}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Your feedback / update
                    if user_feedback:
                        st.markdown("#### Your Update")
                        st.markdown(
                            f'<div class="ticketglass-feedback-box">{user_feedback}</div>',
                            unsafe_allow_html=True
                        )
                    
                    # Resolution (if applicable)
                    if resolution:
                        st.markdown("#### ✅ Resolution")
                        st.markdown(resolution)
                    
                    # Learning tip (if applicable)
                    if learning_tip:
                        st.markdown("#### 💡 For Future Reference")
                        st.markdown(f"*{learning_tip}*")
            
            st.markdown("")  # Spacing
    
    st.divider()


def render_feedback_widget(ticket_dict: Dict[str, Any]):
    """Render feedback buttons - customer tells us if this helped."""
    st.subheader("📝 Was This Helpful?")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    ticket_id = ticket_dict['ticket_id']
    
    with col1:
        if st.button("✅ Yes, this helped!", use_container_width=True, key=f"helpful_{ticket_id}"):
            if ticket_id not in st.session_state.feedback_store:
                st.session_state.feedback_store[ticket_id] = []
            st.session_state.feedback_store[ticket_id].append({
                "sentiment": "satisfied",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": "Customer marked as helpful"
            })
            st.success("✅ Thanks! We're glad we could help.")
    
    with col2:
        if st.button("❌ No, I still need help", use_container_width=True, key=f"not_helpful_{ticket_id}"):
            if ticket_id not in st.session_state.feedback_store:
                st.session_state.feedback_store[ticket_id] = []
            st.session_state.feedback_store[ticket_id].append({
                "sentiment": "frustrated",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "note": "Customer indicated still needs help"
            })
            st.warning("⚠️ We understand. We'll keep working on this.")
    
    st.divider()


def render_your_feedback_history(ticket_dict: Dict[str, Any]):
    """Show customer's own feedback (not team metrics)."""
    st.subheader("📋 Your Feedback")
    
    ticket_id = ticket_dict['ticket_id']
    feedback_list = st.session_state.feedback_store.get(ticket_id, [])
    
    if feedback_list:
        for fb in feedback_list:
            timestamp = fb.get('timestamp', 'Unknown time')
            sentiment = fb.get('sentiment', 'neutral')
            emoji = "✅" if sentiment == "satisfied" else "⚠️"
            
            st.markdown(f"{emoji} {fb.get('note')} — {timestamp}")
    else:
        st.info("No feedback recorded yet. Let us know if this helped!")
    
    st.divider()


def render_contact_support():
    """Show customer how to reach support if they need more help."""
    st.subheader("🆘 Still Need Help?")
    
    st.markdown("""
    If these steps didn't solve your issue, here's how to get more help:
    
    - **Reply directly** to this ticket with more details
    - **Call support:** (555) 123-4567
    - **Email:** support@company.com
    
    We're here to help! 💪
    """)


# ============================================================================
# MAIN APP
# ============================================================================

def main():
    """Main app - customer-facing ticket portal."""
    
    # Page config
    st.set_page_config(
        page_title="TicketGlass - Your Support Ticket",
        page_icon="🎫",
        layout="wide"
    )
    
    # Apply CSS
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    
    # Load demo ticket (customer sees their ticket, not a queue)
    ticket_dict = load_ticket_data(st.session_state.selected_ticket_id)
    
    # CUSTOMER PORTAL LAYOUT
    # (No ticket selector - customer sees THEIR ticket)
    
    render_header(ticket_dict)
    render_ticket_status(ticket_dict)
    render_status_bar(ticket_dict)
    render_timeline(ticket_dict)
    render_feedback_widget(ticket_dict)
    render_your_feedback_history(ticket_dict)
    render_contact_support()
    
    # Footer
    st.divider()
    st.markdown("""
    ---
    *TicketGlass: Real-time transparency for your IT support tickets*  
    *Powered by AI • AWS Bedrock Native • Secure & Private*
    """)


if __name__ == "__main__":
    main()