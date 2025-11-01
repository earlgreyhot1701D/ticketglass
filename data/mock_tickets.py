"""
TicketGlass Mock Ticket Data - 8 Realistic IT Support Scenarios

Tickets cover:
- TKT-001: Excel crashes on startup (Software) [DEMO TICKET]
- TKT-002: Security cameras crashed (Hardware)
- TKT-003: Can't access shared drive (Access)
- TKT-004: Email sync broken (Email)
- TKT-005: Printer offline (Hardware)
- TKT-006: License error in Teams (Software)
- TKT-007: Password reset not working (Access)
- TKT-008: WiFi won't connect (Network)

Each ticket:
- Has 2-3 status events with user feedback
- Shows different user tones (frustrated, satisfied, neutral)
- Demonstrates escalation path
- Includes learning tip on resolution
- Uses diverse first names (not stereotypical)

Mock data is loaded into MockTicketAdapter for MVP testing.
"""

from datetime import datetime, timezone
from typing import Dict, Any, List

# ============================================================================
# MOCK TICKETS DATA
# ============================================================================

MOCK_TICKETS_DATA: Dict[str, Dict[str, Any]] = {
    # =======================================================================
    # TKT-001: Excel crashes on startup (DEMO TICKET)
    # =======================================================================
    "TKT-001": {
        "ticket_id": "TKT-001",
        "category": "Software",
        "title": "Excel crashes on startup",
        "user_name": "Amir",
        "user_tone": "frustrated",  # Deadline pressure
        "status_events": [
            {
                "time": "09:15",
                "phase": "Received",
                "event": "Ticket submitted - Employee needs quarterly report processed by 4 pm today and Excel keeps crashing",
            },
            {
                "time": "09:45",
                "phase": "Assigned",
                "event": "Assigned to TicketGlass IT support team",
            },
            {
                "time": "10:00",
                "phase": "Diagnosed",
                "event": "Initial diagnosis provided",
                "summary": "Hi Amir! 👋 We understand you need this done today—that's frustrating! 😤 Let's start simple. Restart your computer and try again. This fixes most Excel crashes.",
                "user_feedback": "Already tried restarting twice. Still crashes when I click the Excel icon.",
            },
            {
                "time": "10:45",
                "phase": "Escalated",
                "event": "Escalated to deeper diagnosis",
                "summary": "Got it—restart didn't work, which tells us something good: it's not a simple reboot issue. 🔍 That means we need to dig deeper. Check your add-ins (they cause 60% of Excel crashes). Go to File → Options → Add-ins. Tell us what you see.",
                "user_feedback": "Found the add-ins menu. Which ones should I disable?",
            },
            {
                "time": "11:30",
                "phase": "Resolved",
                "event": "Resolved",
                "resolution": "Awesome! 🎉 Disable all non-Microsoft add-ins first, then restart Excel. This should get you running in 2 minutes. If it works, you can re-enable add-ins one by one to see which caused the crash.",
                "user_feedback": "That worked! Excel is open now. Didn't know about add-ins.",
                "learning_tip": "When Excel crashes, try disabling add-ins FIRST (2 min fix) before reinstalling (30 min + data risk). Save this for next time!",
            },
        ],
    },
    # =======================================================================
    # TKT-002: Security cameras crashed (Hardware)
    # =======================================================================
    "TKT-002": {
        "ticket_id": "TKT-002",
        "category": "Hardware",
        "title": "Security camera system crashed - feeds offline",
        "user_name": "Jordan",
        "user_tone": "frustrated",  # Security concern
        "status_events": [
            {
                "time": "08:30",
                "phase": "Received",
                "event": "Urgent: Security cameras went offline 30 min ago",
            },
            {
                "time": "08:45",
                "phase": "Assigned",
                "event": "Escalated to P1 - assigned immediately",
            },
            {
                "time": "09:00",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Jordan, we're on it! 🚨 Security is priority #1. We're checking the DVR unit now. This usually means the hard drive overheated or lost power. Can you check: Is the DVR box powered on? Look for the blue light.",
                "user_feedback": "Blue light is off. The box is warm but not plugged in.",
            },
            {
                "time": "09:30",
                "phase": "Escalated",
                "event": "Escalated - on-site visit required",
                "summary": "Found it! 💡 The power cable came loose (heat + vibration sometimes causes this). Plug it back in. If that doesn't work, the hard drive might need replacement—we'll handle that. Let us know if power restores the feeds.",
                "user_feedback": "Plugged it back in. Cameras are back online. Thanks for the quick response!",
                "learning_tip": "Security gear overheating? Check power connections first. Also: label your cables and secure them. Prevents 80% of 'mysterious' outages.",
            },
        ],
    },
    # =======================================================================
    # TKT-003: Can't access shared drive (Access)
    # =======================================================================
    "TKT-003": {
        "ticket_id": "TKT-003",
        "category": "Access",
        "title": "Cannot access shared drive - permission denied",
        "user_name": "Blake",
        "user_tone": "neutral",  # Matter-of-fact
        "status_events": [
            {
                "time": "10:15",
                "phase": "Received",
                "event": "Permission error when accessing shared folder",
            },
            {
                "time": "10:30",
                "phase": "Assigned",
                "event": "Assigned to access team",
            },
            {
                "time": "11:00",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Hey Blake! 👋 We see the access error. This usually happens after a group membership change. Two things to try: 1) Restart your computer (refreshes permissions). 2) If that doesn't work, it's usually a 5-minute permission reset on our end.",
                "user_feedback": "Restarted. Still can't access the Q drive.",
            },
            {
                "time": "11:45",
                "phase": "Resolved",
                "event": "Resolved",
                "resolution": "All set! ✅ We've reset your group permissions (Security refresh). Try the Q drive again now—should work within 30 seconds.",
                "user_feedback": "Q drive works now. Thanks!",
                "learning_tip": "Permission errors after org changes? Restart first. If that doesn't fix it, it's usually a 5-minute backend sync. Patience = your friend here.",
            },
        ],
    },
    # =======================================================================
    # TKT-004: Email sync broken (Email)
    # =======================================================================
    "TKT-004": {
        "ticket_id": "TKT-004",
        "category": "Email",
        "title": "Outlook won't sync - emails stuck in Sent folder",
        "user_name": "Casey",
        "user_tone": "satisfied",  # Patient, understanding
        "status_events": [
            {
                "time": "12:00",
                "phase": "Received",
                "event": "Email sync issue - sent emails not showing in Inbox",
            },
            {
                "time": "12:30",
                "phase": "Assigned",
                "event": "Assigned to email support",
            },
            {
                "time": "13:00",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Hi Casey! 📧 Your sync issue is likely the local cache getting corrupted. Try this: Close Outlook → Go to Control Panel → Mail → Show Profiles → Delete and recreate. Takes 3-5 min and fixes 90% of these.",
                "user_feedback": "That worked! Emails are syncing now. Appreciate the clear steps.",
                "learning_tip": "Email sync frozen? Clear the local cache (delete & recreate profile). Faster than waiting for background sync to timeout.",
            },
        ],
    },
    # =======================================================================
    # TKT-005: Printer offline (Hardware)
    # =======================================================================
    "TKT-005": {
        "ticket_id": "TKT-005",
        "category": "Hardware",
        "title": "Printer showing offline - not printing",
        "user_name": "Morgan",
        "user_tone": "frustrated",  # Important meeting printouts needed
        "status_events": [
            {
                "time": "14:00",
                "phase": "Received",
                "event": "Conference room printer offline - meeting in 30 min",
            },
            {
                "time": "14:15",
                "phase": "Assigned",
                "event": "Assigned to hardware team",
            },
            {
                "time": "14:30",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Morgan, we're helping! 🖨️ Printer offline usually means network hiccup. First: Power cycle the printer (off 30 sec, back on). If it's still offline after that, it's likely a network card reset needed.",
                "user_feedback": "Power cycled it. Still offline. Need this working in 15 minutes.",
            },
            {
                "time": "14:50",
                "phase": "Resolved",
                "event": "Resolved",
                "resolution": "Fixed! ✅ We reset the network interface. Printer should be online now—give it 1 min to fully restart. You're good to print!",
                "user_feedback": "Printing now. Thank you!",
                "learning_tip": "Printer offline? 80% of the time it's the network card resetting. Power cycle first, then wait 60 sec for full restart.",
            },
        ],
    },
    # =======================================================================
    # TKT-006: License error in Teams (Software)
    # =======================================================================
    "TKT-006": {
        "ticket_id": "TKT-006",
        "category": "Software",
        "title": "Teams license error - 'Your license has expired'",
        "user_name": "Riley",
        "user_tone": "confused",  # Technical terms confusing
        "status_events": [
            {
                "time": "15:00",
                "phase": "Received",
                "event": "License error when opening Teams",
            },
            {
                "time": "15:30",
                "phase": "Assigned",
                "event": "Assigned to licensing team",
            },
            {
                "time": "16:00",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Riley, this is simpler than it sounds! 🎯 Your license didn't actually expire—the cache is just confused. Sign out of Teams completely → Restart → Sign back in. This refreshes the license check.",
                "user_feedback": "Signed out, restarted, signed back in. Same error. Don't really understand what cache means.",
            },
            {
                "time": "16:30",
                "phase": "Escalated",
                "event": "Escalated with clearer explanation",
                "summary": "No problem—let me explain differently. Think of it like this: Teams stores a 'memo' locally about your license. That memo got outdated. Restarting clears the memo. But yours is being stubborn. We're now clearing the memo from our server side (backend refresh). Try again in 2 min.",
                "user_feedback": "That makes sense! Should I try now?",
            },
            {
                "time": "16:45",
                "phase": "Resolved",
                "event": "Resolved",
                "resolution": "Yep, try now! ✅ We cleared it from our end. You should see 'Pro' license showing in Teams settings now.",
                "user_feedback": "Got it! License shows as Pro. Thanks for explaining it clearly.",
                "learning_tip": "License errors often just mean the system forgot to check the updated status. Restart + backend refresh usually does it.",
            },
        ],
    },
    # =======================================================================
    # TKT-007: Password reset not working (Access)
    # =======================================================================
    "TKT-007": {
        "ticket_id": "TKT-007",
        "category": "Access",
        "title": "Cannot reset password - reset link expired",
        "user_name": "Taylor",
        "user_tone": "frustrated",  # Locked out, can't work
        "status_events": [
            {
                "time": "09:00",
                "phase": "Received",
                "event": "Password reset link expired - can't set new password",
            },
            {
                "time": "09:15",
                "phase": "Assigned",
                "event": "Assigned to identity team",
            },
            {
                "time": "09:45",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Taylor, we hear you—being locked out is frustrating! 😤 Password reset links expire after 2 hours for security. We're sending a new one now. Check your email (spam folder too). You'll have 2 hours to use it.",
                "user_feedback": "Got the new link. Trying it now... worked! Password changed.",
                "learning_tip": "Password reset links time out for security. Use them within 2 hours. If you miss it, just request a new one—takes 30 sec.",
            },
        ],
    },
    # =======================================================================
    # TKT-008: WiFi won't connect (Network)
    # =======================================================================
    "TKT-008": {
        "ticket_id": "TKT-008",
        "category": "Network",
        "title": "Laptop won't connect to WiFi - authentication error",
        "user_name": "Devon",
        "user_tone": "neutral",  # Methodical, patient
        "status_events": [
            {
                "time": "10:30",
                "phase": "Received",
                "event": "WiFi authentication fails - can't connect to office network",
            },
            {
                "time": "10:45",
                "phase": "Assigned",
                "event": "Assigned to network team",
            },
            {
                "time": "11:15",
                "phase": "Diagnosed",
                "event": "Initial diagnosis",
                "summary": "Devon, WiFi auth errors usually mean the system forgot your credentials. Try this: Forget the network → Reconnect with password. Go to Settings → WiFi → Manage Known Networks → Select our network → Forget → Reconnect.",
                "user_feedback": "Forgot the network and reconnected. Same error. Password is definitely correct.",
            },
            {
                "time": "12:00",
                "phase": "Escalated",
                "event": "Escalated - DNS/certificate issue",
                "summary": "Hmm, that usually works. Let's check something deeper: Your system might have cached a bad certificate. We're purging that from our server. After you see this message, try disconnecting/reconnecting one more time.",
                "user_feedback": "Reconnected after you cleared it. Works now!",
                "learning_tip": "WiFi auth failing even with right password? Clear the local profile + server-side cache. Usually fixes it.",
            },
        ],
    },
}


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def get_mock_tickets() -> Dict[str, Dict[str, Any]]:
    """
    Get all mock tickets.

    Returns:
        Dictionary of ticket_id -> ticket_data
    """
    return MOCK_TICKETS_DATA


def get_mock_ticket(ticket_id: str) -> Dict[str, Any]:
    """
    Get a single mock ticket by ID.

    Args:
        ticket_id: Ticket ID (e.g., "TKT-001")

    Returns:
        Ticket data dictionary

    Raises:
        KeyError: If ticket not found
    """
    return MOCK_TICKETS_DATA[ticket_id]


def list_mock_tickets() -> List[Dict[str, str]]:
    """
    Get list of all ticket IDs.

    Useful for UI dropdowns.
    """
    return [
        {
            "id": ticket_id,
            "title": data["title"],
            "category": data["category"],
            "user": data["user_name"],
        }
        for ticket_id, data in MOCK_TICKETS_DATA.items()
    ]


def get_tickets_by_category(category: str) -> Dict[str, Dict[str, Any]]:
    """
    Get all tickets for a specific category.

    Args:
        category: Category filter (Software, Hardware, etc.)

    Returns:
        Dictionary of matching tickets
    """
    return {
        ticket_id: data
        for ticket_id, data in MOCK_TICKETS_DATA.items()
        if data["category"].lower() == category.lower()
    }


def get_demo_ticket() -> Dict[str, Any]:
    """Get the demo ticket (TKT-001: Excel crashes)."""
    return MOCK_TICKETS_DATA["TKT-001"]


# ============================================================================
# HELPER FUNCTIONS (For UI and tests)
# ============================================================================


def get_mock_tickets() -> Dict[str, Dict[str, Any]]:
    """
    Get all mock tickets for UI dropdown and initialization.

    Returns:
        Dict mapping ticket_id (str) to ticket data (Dict)

    Example:
        >>> tickets = get_mock_tickets()
        >>> len(tickets)
        8
        >>> tickets['TKT-001']['title']
        'Excel crashes on startup'
    """
    return MOCK_TICKETS_DATA


def get_demo_ticket() -> Dict[str, Any]:
    """
    Get the demo ticket (TKT-001) for UI first-time visitors.

    TKT-001 is the primary demo ticket showing:
    - User frustration (Amir needed report done today)
    - Multiple feedback loops
    - Escalation path
    - Resolution with learning tip

    Returns:
        Dict with complete ticket data including all status events

    Example:
        >>> demo = get_demo_ticket()
        >>> demo['ticket_id']
        'TKT-001'
        >>> len(demo['status_events'])
        4
    """
    return MOCK_TICKETS_DATA.get("TKT-001")


# ============================================================================
# DATA STATISTICS (For debugging)
# ============================================================================

if __name__ == "__main__":
    print("TicketGlass Mock Ticket Data")
    print("=" * 70)
    print(f"\nTotal tickets: {len(MOCK_TICKETS_DATA)}")
    print("\nTickets by category:")

    categories = {}
    for ticket_id, ticket_data in MOCK_TICKETS_DATA.items():
        cat = ticket_data["category"]
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")

    print("\nTicket user names (diversity check):")
    names = [data["user_name"] for data in MOCK_TICKETS_DATA.values()]
    print(f"  {', '.join(names)}")

    print("\nDemo ticket:")
    demo = get_demo_ticket()
    print(f"  ID: {demo['ticket_id']}")
    print(f"  Title: {demo['title']}")
    print(f"  User: {demo['user_name']}")
    print(f"  Tone: {demo['user_tone']}")
    print(f"  Events: {len(demo['status_events'])}")

    print("\n✅ All mock tickets loaded successfully")