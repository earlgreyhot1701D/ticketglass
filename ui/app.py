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

Run from PROJECT ROOT: streamlit run ui/app.py
"""

import sys
import os
import streamlit as st
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
import logging

# CRITICAL: Add parent directory to path so imports work
# When running: streamlit run ui/app.py
# __file__ = ticketglass/ui/app.py
# dirname(__file__) = ticketglass/ui
# dirname(dirname(__file__)) = ticketglass (PROJECT ROOT)
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Backend imports
from agent.core import Agent, TicketState, Phase, Sentiment, ContextEntry
from agent.prompts import get_system_prompt
from data.mock_tickets import get_mock_tickets, get_demo_ticket
from data.adapters import MockTicketAdapter

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
    
    /* Speaker label styling */
    .ticketglass-speaker-label {
        font-weight: 600;
        color: #0099cc;
        margin: 8px 0 6px 0;
        font-size: 0.95rem;
    }
    
    /* Support team speaker box */
    .ticketglass-summary-box {
        background-color: #e8f4f8;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0 12px 0;
        border-left: 4px solid #0099cc;
        color: #1a1a1a !important;
    }
    
    /* Customer speaker box */
    .ticketglass-feedback-box {
        background-color: #fff3cd;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0 12px 0;
        border-left: 4px solid #ffc107;
        color: #1a1a1a !important;
    }
    
    /* Status/event box */
    .ticketglass-event-box {
        background-color: #f0f0f0;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0 12px 0;
        border-left: 4px solid #888;
        color: #1a1a1a !important;
        font-style: italic;
    }
    
    /* Resolution box */
    .ticketglass-resolution-box {
        background-color: #e8f8e8;
        padding: 12px;
        border-radius: 4px;
        margin: 8px 0 12px 0;
        border-left: 4px solid #28a745;
        color: #1a1a1a !important;
    }
    </style>
"""


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if "selected_ticket_id" not in st.session_state:
    st.session_state.selected_ticket_id = "TKT-001"

if "expanded_phase" not in st.session_state:
    st.session_state.expanded_phase = None  # ACCORDION: Only one phase open at a time

if "expand_all" not in st.session_state:
    st.session_state.expand_all = False  # "View All Phases" toggle

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
    Render timeline view with ACCORDION pattern (only one phase open at a time).
    Clear speaker attribution, tight visual hierarchy, NO blank boxes.
    """
    st.subheader("📍 Your Ticket Timeline")
    
    # Control buttons
    col1, col2 = st.columns([0.5, 0.5])
    with col1:
        if st.button("📖 View All Phases", use_container_width=True):
            st.session_state.expand_all = not st.session_state.expand_all
    with col2:
        if st.button("📁 Close All", use_container_width=True):
            st.session_state.expand_all = False
            st.session_state.expanded_phase = None
    
    st.caption("💡 Click any phase to read what happened at that step")
    st.write("")  # Single spacing line before timeline
    
    agent = get_agent()
    
    for event_idx, event in enumerate(ticket_dict['status_events']):
        phase = event['phase']
        time = event['time']
        summary = event.get('summary')
        user_feedback = event.get('user_feedback')
        resolution = event.get('resolution')
        learning_tip = event.get('learning_tip')
        event_text = event.get('event')
        
        # Get phase style
        style = get_phase_style(ticket_dict, phase)
        symbol = style["symbol"]
        
        # ACCORDION LOGIC: Check if this phase is expanded
        is_expanded = (st.session_state.expanded_phase == phase) or st.session_state.expand_all
        
        # Visual indicator - arrow changes based on state
        expand_indicator = "▼" if is_expanded else "▶"
        
        # PHASE HEADER - SINGLE BUTTON (no st.columns!) with all symbols in one line
        # This eliminates the blank box issue completely
        if st.button(
            f"{symbol} {expand_indicator}  **{time}** – {phase}",
            key=f"phase_{phase}",
            use_container_width=True,
            help="Click to view this step"
        ):
            # ACCORDION LOGIC: Toggle this phase, close others
            if st.session_state.expanded_phase == phase:
                st.session_state.expanded_phase = None  # Close if clicking same one
            else:
                st.session_state.expanded_phase = phase  # Open this, close others
            st.session_state.expand_all = False  # Turn off "View All"
            st.rerun()
        
        # EXPANDED CONTENT - With clear speaker labels and NO blank spaces
        if is_expanded:
            # Show event info (who's handling it) for early phases
            if event_text and not summary:
                st.markdown(f'<div class="ticketglass-event-box">📌 {event_text}</div>', unsafe_allow_html=True)
            
            # What we're doing - WITH SPEAKER LABEL
            if summary:
                st.markdown('<div class="ticketglass-speaker-label">🏢 Support Team</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="ticketglass-summary-box">{summary}</div>',
                    unsafe_allow_html=True
                )
            
            # Your feedback - WITH SPEAKER LABEL
            if user_feedback:
                st.markdown('<div class="ticketglass-speaker-label">👤 You said</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="ticketglass-feedback-box">{user_feedback}</div>',
                    unsafe_allow_html=True
                )
            
            # Resolution - WITH SPEAKER LABEL
            if resolution:
                st.markdown('<div class="ticketglass-speaker-label">✅ Resolution</div>', unsafe_allow_html=True)
                st.markdown(
                    f'<div class="ticketglass-resolution-box">{resolution}</div>',
                    unsafe_allow_html=True
                )
            
            # Learning tip - WITH SPEAKER LABEL
            if learning_tip:
                st.markdown('<div class="ticketglass-speaker-label">💡 Tip for Next Time</div>', unsafe_allow_html=True)
                st.markdown(f"*{learning_tip}*")
        
        st.write("")  # Single spacing between phases
    
    st.divider()


def render_feedback_widget(ticket_dict: Dict[str, Any]):
    """Render feedback buttons - customer tells us if this helped."""
    st.subheader("👍 Was This Helpful?")
    
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
            
            st.markdown(f"{emoji} {fb.get('note')} – {timestamp}")
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