"""
Demo Scenario Scripts — Dev 3
Pre-planned sequence of questions and events for the 5-minute demo.

Each scenario step has:
  - label:    short name shown in the UI dropdown
  - question: the natural-language question to send to the LLM
  - notes:    presenter talking points (not shown to LLM)
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ScenarioStep:
    label: str
    question: str
    notes: str
    # If not None, trigger this event on the state engine BEFORE asking the question
    event_trigger: Optional[str] = None


# ---------------------------------------------------------------------------
# Full 5-minute demo sequence
# ---------------------------------------------------------------------------

DEMO_SCRIPT: list[ScenarioStep] = [

    # --- Scenario 1: Aircraft allocation (1:00–2:30) ---
    ScenarioStep(
        label="1. New ATO — allocate aircraft",
        question=(
            "New ATO just came in. We need 4 DCA/CAP sorties and 2 RECCE sorties "
            "starting from 14:00 today. Which aircraft should we assign, and in what order? "
            "Keep wear levels balanced."
        ),
        notes=(
            "AI should recommend GE01/GE02/GE04/GE08 for DCA, GE06 for RECCE. "
            "Should flag GE05 as low-life (34h) — avoid for routine missions. "
            "GE03 is in maintenance so unavailable."
        ),
    ),

    ScenarioStep(
        label="2. Check QRA readiness",
        question=(
            "Is our QRA aircraft (M05) properly resourced for a 24-hour standby? "
            "Do we have enough Robot-1 missiles and a pilot available?"
        ),
        notes=(
            "QRA = Quick Reaction Alert, always-on intercept aircraft. "
            "Should check weapons inventory (Robot1: 14 available), pilot count (9). "
            "Should come back green."
        ),
    ),

    # --- Scenario 2: Fault cascade (2:30–4:00) ---
    ScenarioStep(
        label="3. GE05 fails BIT — radar fault",
        event_trigger="bit_fail_ge05",
        question=(
            "GE05 just failed pre-flight BIT — radar fault detected, estimated 6-hour repair. "
            "GE05 was assigned to the AI/ST mission M04 at 16:00. What's the impact, "
            "and what are our options?"
        ),
        notes=(
            "GE05 has only 34h remaining life — it was already a concern. "
            "AI should suggest GE08 as replacement (also AI/ST config, 158h life). "
            "Should flag we now have 2 aircraft in maintenance (GE03 + GE05). "
            "Should ask: do we have a Radar exchange unit? (Yes, 1 left after GE03 took one.)"
        ),
    ),

    ScenarioStep(
        label="4. GE07 returns damaged",
        event_trigger="return_damaged_ge07",
        question=(
            "GE07 just returned from M01. Post-mission inspection found hydraulic fault — "
            "maintenance team says 8 hours minimum. We still need 2 aircraft for M03 DCA at 14:00. "
            "Can we meet the ATO, or do we need to report a shortfall to command?"
        ),
        notes=(
            "Now GE03, GE05, GE07 are all unavailable. "
            "Remaining green: GE01, GE02, GE04, GE06, GE08, LO21. "
            "LO21 is GlobalEye (AEW) — not suited for DCA. "
            "So we have GE01/GE02/GE04/GE06/GE08 = 5 green Gripens. Enough for M03×2. "
            "AI should say yes, but the fleet is getting thin."
        ),
    ),

    ScenarioStep(
        label="5. Cannibalize GE09 or wait?",
        question=(
            "GE05 needs a Radar exchange unit for its 6h repair, but we only have 1 UE left "
            "and GE09 is already cannibalized. Resupply is 12–24 hours away. "
            "Should we use the last Radar UE on GE05, or hold it in reserve for a worse case?"
        ),
        notes=(
            "This is the key dilemma question. AI should weigh: "
            "GE05 has 34h life — borderline worth the UE. "
            "Holding the UE preserves flexibility if another radar fault hits. "
            "Expected answer: use the UE on GE05 IF M04 is critical, otherwise hold it."
        ),
    ),

    # --- Scenario 3: 48h readiness forecast (4:00–4:30) ---
    ScenarioStep(
        label="6. 48-hour readiness forecast",
        question=(
            "Give me a readiness forecast for the next 48 hours. "
            "Which aircraft will hit heavy service? Will we run short of any weapons or fuel? "
            "What's our expected sortie generation rate?"
        ),
        notes=(
            "GE05 is at 34h — hits heavy service in ~2 days if flying. "
            "Robot-1: 14 remaining, missions burn ~3–5 per sortie. "
            "At current ATO pace, may hit shortage by Day 3–4. "
            "AI should recommend requesting resupply now and flagging GE05 for scheduling light duty."
        ),
    ),

    # --- Bonus / rapid-fire ---
    ScenarioStep(
        label="7. Best aircraft for RECCE right now",
        question="Which single aircraft is best suited for an urgent RECCE sortie right now?",
        notes="Quick allocation question. Answer should be GE06 (already RECCE config, 110h life).",
    ),

    ScenarioStep(
        label="8. Fleet wear balance check",
        question=(
            "Are we wearing the fleet evenly? Which aircraft are being overused "
            "and which are underused?"
        ),
        notes=(
            "GE05 (34h) is dangerously low. GE04 (175h) and LO21 (320h) have most life left. "
            "AI should suggest resting GE05 and prioritizing GE04 for next missions."
        ),
    ),
]


# ---------------------------------------------------------------------------
# Quick-access individual questions (for free-form demo navigation)
# ---------------------------------------------------------------------------

QUICK_QUESTIONS: list[str] = [
    "Which aircraft should I send on the next RECCE sortie?",
    "Can we handle 2 extra DCA sorties in the next 12 hours?",
    "What's the impact of losing GE05 for 6 hours?",
    "What's our readiness forecast for the next 48 hours?",
    "Should I cannibalize GE03 for the radar unit or wait for resupply?",
    "What's the current fleet status summary?",
    "Which missions are at risk right now?",
    "What resources are running critically low?",
    "Recommend a maintenance priority order for the workshop.",
    "If we get a new Bredduppgift (surge order) for 3 AI/ST sorties, can we handle it?",
]


# ---------------------------------------------------------------------------
# Gradio helper — returns dropdown choices for the demo panel
# ---------------------------------------------------------------------------

def get_scenario_labels() -> list[str]:
    return [s.label for s in DEMO_SCRIPT]


def get_scenario_question(label: str) -> str:
    for s in DEMO_SCRIPT:
        if s.label == label:
            return s.question
    return ""


def get_scenario_event(label: str) -> Optional[str]:
    for s in DEMO_SCRIPT:
        if s.label == label:
            return s.event_trigger
    return None
