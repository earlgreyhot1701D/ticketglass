# TicketGlass MVP - BUILD PLAN
**Status:** READY TO BUILD  
**Start:** Now  
**Philosophy:** Smallest working change, test-first, log everything

---

## PHASE 1: AGENT CORE FOUNDATION 

### Task 1.1: System Prompt & Reasoning Architecture (45 min)
**What:** Define agent personality, reasoning loop, context memory structure  
**Output:** `agent/prompts.py` (system prompt + tone templates)  

**CRITICAL: This is phase 1 of scalable design**
- Agent core will be extracted to separate service/API later
- Build as if it will be called from FastAPI, not just Streamlit
- Zero Streamlit imports in any agent files

**Checklist:**
- [ ] System prompt written (warm, "we", emoji-friendly, non-repeating)
- [ ] Tone templates for different phases (initial, escalation, resolution)
- [ ] Tone matching rules (detect user frustration Ã¢â€ â€™ empathetic)
- [ ] Context history structure defined
- [ ] Reasoning loop logic documented
- [ ] **API DESIGN:** Output format is standard JSON (no Streamlit formatting)
- [ ] **NO IMPORTS:** `agent/prompts.py` has NO streamlit imports

**Your Review Point:** Does the tone feel right? Can output be called from API?

---

### Task 1.2: Agent Core Class 
**What:** Build the reasoning engine  
**Output:** `agent/core.py` (Agent class)  

**CRITICAL: This is scalable from day 1**
- Pure Python class (can be called from Streamlit, FastAPI, Lambda, etc.)
- Zero UI dependencies (no streamlit imports)
- Returns clean JSON (API-ready output)

**Checklist:**
- [ ] `agent/core.py` created
  - [ ] `Agent` class defined (pure Python, no UI imports)
  - [ ] `__init__` sets up system prompt + model
  - [ ] `process_ticket(ticket_state)` main method
  - [ ] `reason_about_context(context_history, current_phase)` logic
  - [ ] `detect_escalation(user_feedback)` helper
  - [ ] `match_tone(user_tone)` helper
- [ ] Context history tracking (what we said, what user said back)
- [ ] Sentiment detection (frustrated, satisfied, neutral)
- [ ] Escalation detection (is this still unresolved?)
- [ ] Methods return clean JSON/dict (no Streamlit types)
- [ ] **NO streamlit imports in this file**
- [ ] Test: Pass mock ticket, get back adapted summary as JSON

**Your Review Point:** Run scenario. Does it read context + adapt? Output clean JSON?

---

### Task 1.3: Test-First Validation 
**What:** Create test framework before tools  
**Output:** `tests/test_agent.py` (basic validation)  
**Checklist:**
- [ ] Test: Agent reads context_history
- [ ] Test: Agent doesn't repeat previous summary
- [ ] Test: Agent detects escalation ("that didn't work")
- [ ] Test: Agent matches tone (frustrated vs satisfied)
- [ ] All tests passing

**Your Review Point:** Run tests, confirm agent logic is solid.

---

## PHASE 2: TOOLS & DATA 

### Task 2.1: Agent Tools 
**What:** Build fetch, generate, store functions  
**Output:** `agent/tools.py`  
**Checklist:**
- [ ] `fetch_ticket_state(ticket_id)` Ã¢â€ â€™ returns dict with context_history
- [ ] `generate_summary_with_context(ticket_state)` Ã¢â€ â€™ calls agent.process_ticket()
- [ ] `store_feedback(ticket_id, feedback, sentiment)` Ã¢â€ â€™ stores user response
- [ ] `update_context_history(ticket_id, summary, user_response)` Ã¢â€ â€™ logs the exchange
- [ ] All tools return clean JSON structures

**Your Review Point:** Test tools with mock data by hand.

---

### Task 2.2: Mock Ticket Data 
**What:** Create 8 realistic IT tickets with feedback loops  
**Output:** `data/mock_tickets.py` (all 8 tickets)  
**Checklist:**

**Ticket Structure (example):**
```python
{
  "ticket_id": "TKT-001",
  "category": "Network",
  "title": "Laptop won't connect to WiFi",
  "user_name": "Sarah Chen",
  "user_tone": "frustrated",  # affects agent tone
  "status_events": [
    {
      "time": "09:15",
      "phase": "Received",
      "event": "Ticket submitted",
      "summary": None
    },
    {
      "time": "09:45",
      "phase": "Assigned",
      "event": "Assigned to support",
      "summary": None
    },
    {
      "time": "10:00",
      "phase": "Diagnosed",
      "event": "Initial diagnosis",
      "summary": "We found a DNS cache issue. Here's how to clear it...",
      "user_feedback": "Tried it. WiFi still won't connect."  # KEY
    },
    {
      "time": "10:45",
      "phase": "Escalated",
      "event": "Escalated to deeper diagnosis",
      "summary": "DNS didn't work. We're checking adapter config next...",
      "user_feedback": "Thanks for escalating quickly."
    },
    {
      "time": "11:30",
      "phase": "Resolved",
      "event": "Resolved",
      "resolution": "Reinstalled adapter driver. WiFi restored.",
      "user_feedback": "This tip about drivers is helpful.",
      "learning_tip": "Update network drivers monthly to prevent this."
    }
  ]
}
```

**All 8 Tickets:**
- TKT-001: WiFi won't connect (Network) Ã¢â‚¬â€ **DEMO TICKET**
- TKT-002: Monitor won't turn on (Hardware)
- TKT-003: Excel crashes on startup (Software)
- TKT-004: Can't access shared drive (Access)
- TKT-005: Email sync broken (Email)
- TKT-006: Printer offline (Hardware)
- TKT-007: License error in Teams (Software)
- TKT-008: Password reset not working (Access)

**For each ticket:**
- [ ] 2-3 user feedback loops (shows agent reasoning in action)
- [ ] Different user tones (frustrated, satisfied, neutral)
- [ ] Escalation path (simple issue Ã¢â€ â€™ complex fix)
- [ ] Learning tip on resolution
- [ ] Comments explaining why the ticket structure matters

**Your Review Point:** Do these feel realistic? Would actual IT users submit these?

---

## PHASE 3: STREAMLIT UI 

### Task 3.1: Streamlit Foundation 
**What:** Build the basic page structure  
**Output:** `ui/app.py` (skeletal UI)  
**Checklist:**
- [ ] Page title + layout
- [ ] Ticket ID input field
- [ ] Load ticket button
- [ ] Session state management (for feedback storage)
- [ ] Basic styling (clean, readable)

**Your Review Point:** Does it feel lightweight and fast?

---

### Task 3.2: Timeline View 
**What:** Display ticket progression with AI summaries  
**Output:** Enhanced `ui/app.py`  
**Checklist:**
- [ ] Progress bar showing 4 phases (Received Ã¢â€ â€™ Assigned Ã¢â€ â€™ Diagnosed Ã¢â€ â€™ Resolved)
- [ ] Timeline showing:
  - Timestamp
  - Phase
  - Agent summary (from agent core)
  - User feedback response (if any)
  - Reasoning note (e.g., "DNS didn't work, escalating")
- [ ] Expandable/collapsible sections for readability

**Your Review Point:** Is the reasoning chain clear? Can you follow what happened?

---

### Task 3.3: Feedback Widget & Analytics 
**What:** Collect feedback + show simple analytics  
**Output:** Enhanced `ui/app.py`  
**Checklist:**
- [ ] Feedback widget (Yes/No buttons for current phase)
- [ ] Feedback storage (in memory, saved to mock DB)
- [ ] Analytics display:
  - Total responses collected
  - % marked helpful
  - Sample themes from feedback
  - Transparency caveat: "Early stage, more data coming"
- [ ] Feedback persists across sessions (mock storage)

**Your Review Point:** Does the feedback feel useful without being overwhelming?

---

## PHASE 4: INTEGRATION & TESTING 

### Task 4.1: Wire Agent and UI 
**What:** Connect all pieces  
**Checklist:**
- [ ] UI ticket ID lookup Ã¢â€ â€™ fetches from mock_tickets.py
- [ ] Agent processes ticket state Ã¢â€ â€™ generates summaries
- [ ] Summaries display in timeline
- [ ] User feedback flows to feedback store
- [ ] Analytics recalculate
- [ ] Full app flow works end-to-end

**Your Review Point:** Run through a complete ticket scenario. No breaks.

---

### Task 4.2: Agent Output Quality Review 
**What:** Test all 8 tickets, validate agent reasoning  
**Checklist:**
- [ ] TKT-001 (demo): Agent reads feedback, doesn't repeat Ã¢Å“â€¦
- [ ] TKT-002-008: Agent behaves correctly for each
- [ ] Tone matching: Frustrated users get empathetic tone Ã¢Å“â€¦
- [ ] Escalation: System notes escalation appropriately Ã¢Å“â€¦
- [ ] Resolution: Learning tips are useful Ã¢Å“â€¦
- [ ] No hallucinations or off-topic text Ã¢Å“â€¦

**Your Review Point:** Read agent outputs for all 8 tickets. This is where you say "adjust tone" or "sounds perfect."

**Iteration Loop:**
- You flag: "Agent sounds too robotic on TKT-003"
- I adjust: System prompt + regenerate
- Repeat until tone is locked

---

## PHASE 5: DEMO & DOCUMENTATION 

### Task 5.1: Demo Script (30 min)
**What:** Write tight 3-min demo narration  
**Output:** `DEMO_SCRIPT.md`  
**Checklist:**
- [ ] Script covers (by second):
  - 0-30s: Problem statement (one ticket shows frustration)
  - 30-90s: Agent reasoning chain (2-3 phases of TKT-001, user feedback visible)
  - 90-150s: Feedback loop (widget click, analytics shown)
  - 150-180s: Scalability (quick mention of 8 ticket categories)
- [ ] Key moments highlighted (where you pause, where you click)
- [ ] Exact wording provided (no improvisation needed)

**Your Review Point:** Does the script flow? Feel comfortable delivering it?

---

### Task 5.2: Demo Recording 
**What:** You record the demo  
**Checklist:**
- [ ] Screen recording (Streamlit app running locally)
- [ ] Voiceover (clear, calm, follows script)
- [ ] Audio quality (no background noise)
- [ ] Length: Ã¢â€°Â¤3 minutes
- [ ] Upload to YouTube (unlisted) or GDrive
- [ ] Get shareable link

**Note:** I provide the script; you do the recording (your voice = authentic).

---

### Task 5.3: README.md 
**What:** Document the project for judges  
**Output:** `README.md`  
**Checklist:**
- [ ] **What is TicketGlass?** (1 paragraph)
- [ ] **The Problem** (why this matters)
- [ ] **The Wow** (context reasoning, never repeats)
- [ ] **How to Run Locally** (step-by-step)
- [ ] **Architecture Overview** (simple diagram or text)
- [ ] **Mock Ticket Categories** (list + examples)
- [ ] **Key Design Decisions** (why we built it this way)
- [ ] **Testing** (how to validate agent outputs)
- [ ] **Future Development** (post-MVP vision)

---

### Task 5.4: Architecture Documentation 
**What:** Explain system design for judges  
**Output:** `docs/ARCHITECTURE.md` + `docs/DESIGN_DECISIONS.md`  
**Checklist:**
- [ ] System diagram (agent Ã¢â€ â€™ tools Ã¢â€ â€™ data Ã¢â€ â€™ UI)
- [ ] Agent reasoning flow (with example)
- [ ] Context history structure
- [ ] Feedback loop mechanic
- [ ] Key decisions + rationale
- [ ] Post-MVP roadmap

---

### Task 5.5: Prototype Deck 
**What:** Build presentation deck for judges  
**Output:** `TicketGlass_Prototype_Deck.pdf`  
**Structure:**
- Slide 1: Title + Team
- Slide 2: Problem Statement
- Slide 3: Solution Overview (TicketGlass)
- Slide 4: Differentiation (context reasoning, tone matching)
- Slide 5: Key Features (timeline, feedback, analytics)
- Slide 6: Agent Architecture Diagram
- Slide 7: UI Mockup/Screenshot
- Slide 8: Tech Stack (Python, AWS Bedrock, Streamlit)
- Slide 9: Agent Reasoning Example (before/after)
- Slide 10: Feedback Loop Mechanic
- Slide 11: Demo Screenshots
- Slide 12: Post-MVP Vision
- Slide 13: GitHub + Demo Video Links

**Your Review Point:** Does it tell the story? Does it show you understand the problem?

---

## QUALITY GATES

| Gate | Owner | Check |
|------|-------|-------|
| Agent outputs quality | You | Read 8 tickets, tone feels right |
| Mock data realism | You | "Would employees actually submit these?" |
| UI clarity | You | "I understand what's happening" |
| Demo video | You | Recording, narration, timing |
| README | You | Clear enough for judges to run locally |
| Deck narrative | You | Tells a compelling story |

---

## BUFFER & CONTINGENCY

**If we run over:**
- Trim polish on UI (keep it functional, lose animations)
- Simplify deck (9 slides vs 13)
- Pre-record demo as fallback (not improvise)

**If we finish early:**
- Add 1-2 more mock tickets
- Enhance README with code walkthrough
- Add inline code comments for judges reading the repo

---

## SUCCESS = SHIPPED

**You know we're done when:**
- [] GitHub repo is public + cloneable
- []Demo video is uploaded
- []README explains how to run locally
- []Deck tells the TicketGlass story
- []Submission form is filled with all links

**After that:** Judges see the work, evaluate, and we iterate based on feedback (post-submission).

---

**LET'S BUILD.**
