"""
Demo Scenario Scripts — Dev 3
Pre-planned sequence of questions and events for the 5-minute demo.

Each scenario step has:
  - label:    short name shown in the UI dropdown
  - question: the natural-language question to send to the LLM
  - notes:    presenter talking points (not shown to LLM)

Initial engine state (Day 2, 08:00, Phase: Kris):
  GE01 green DCA/CAP 180h | GE02 green RECCE   145h | GE03 green DCA/CAP 110h
  GE04 green AI/ST   85h  | GE05 green DCA/CAP  62h | GE06 RED   DCA/CAP  48h (service bay, ETA 4h)
  GE07 green RECCE   35h  | GE08 green DCA/CAP  20h | GF01 green DCA/CAP 155h
  GF02 on_mission DCA/CAP 95h
  Weapons: Robot-1×14, Bomb-2×8, Robot-15×4
  Exchange units: Radar×3, SignalProcessor×2, EjectionSeat×1, HydraulicPump×2
  Personnel: pilots×8
  ATO: M01 DCA 10:00, M02 DCA 14:00, M03 DCA 20:00, M04 RECCE 09:00, M05 AI/ST 12:00, M06 QRA 00:00
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
        event_trigger="new_ato",
        question=(
            "New ATO just came in. We need to cover M01 and M02 (DCA/CAP), "
            "M04 (RECCE), and M05 (AI/ST) today. Which aircraft should we assign "
            "to each mission, and in what order? Keep wear levels balanced."
        ),
        notes=(
            "DCA/CAP (green): GE01 (180h), GF01 (155h), GE03 (110h), GE05 (62h), GE08 (20h — critical). "
            "RECCE (green): GE02 (145h), GE07 (35h — low). "
            "AI/ST (green): GE04 (85h). "
            "GE06 is in service bay (4h ETA) — unavailable. "
            "AI should recommend GE01+GF01 for DCA (most life), GE02 for RECCE, GE04 for AI/ST. "
            "Should flag GE08 as critically low at 20h — avoid for routine missions. "
            "GE05 borderline at 62h."
        ),
    ),

    ScenarioStep(
        label="2. Check QRA readiness",
        question=(
            "Is our QRA mission (M06) properly resourced for a 24-hour standby? "
            "Do we have enough Robot-1 missiles and a pilot available?"
        ),
        notes=(
            "QRA = Quick Reaction Alert, always-on intercept aircraft. "
            "Should check weapons inventory (Robot-1: 14 available) and pilot count (8 pilots). "
            "Should come back green — resources are sufficient."
        ),
    ),

    # --- Scenario 2: Fault cascade (2:30–4:00) ---
    ScenarioStep(
        label="3. GE05 fails BIT — complex LRU fault",
        event_trigger="bit_fail_ge05",
        question=(
            "GE05 just failed pre-flight BIT — complex LRU fault detected, estimated 6-hour repair. "
            "GE05 was planned for DCA mission M01 at 10:00. What's the impact, "
            "and what are our options?"
        ),
        notes=(
            "GE05 has 62h remaining life — borderline. Now in service bay for 6h. "
            "AI should suggest GE03 (110h) or GF01 (155h) as replacement for M01 (both DCA/CAP). "
            "Now 2 aircraft unavailable: GE06 (service bay, 4h ETA) + GE05 (just faulted). "
            "Radar exchange units: 3 available — sufficient for the repair. "
            "AI should check if service bay has capacity (GE06 already occupies one slot, capacity is 2)."
        ),
    ),

    ScenarioStep(
        label="4. GE07 returns damaged",
        event_trigger="return_damaged_ge07",
        question=(
            "GE07 just returned from a RECCE sortie with a hydraulic fault — "
            "maintenance says 16 hours minimum. We still need 2 aircraft for M03 DCA at 20:00. "
            "Can we meet the ATO, or do we need to report a shortfall to command?"
        ),
        notes=(
            "Now GE05, GE06, GE07 all unavailable (3 aircraft in maintenance). "
            "Remaining DCA/CAP (green): GE01 (180h), GF01 (155h), GE03 (110h), GE08 (20h — critical). "
            "GF02 is returning from on_mission status. "
            "AI should say yes, M03 is achievable with GE01+GF01, but fleet is getting thin. "
            "Should advise against using GE08 (20h — next heavy service imminent)."
        ),
    ),

    ScenarioStep(
        label="5. Radar UE — use now or hold in reserve?",
        question=(
            "GE05 is in maintenance with a complex LRU fault (6h repair). "
            "We have 3 Radar exchange units available, but resupply is uncertain "
            "and we could face more faults on high-life aircraft. "
            "Should we use one UE on GE05 now, or hold them in reserve?"
        ),
        notes=(
            "Key dilemma: resource conservation vs. speed of recovery. "
            "GE05 has 62h remaining — borderline worth a UE. "
            "Holding preserves 3 UEs for higher-value aircraft like GE01 (180h) or GF01 (155h). "
            "Expected answer: use UE on GE05 if M01 or another DCA mission is critical right now; "
            "otherwise conserve — we already have GE03 and GF01 available for DCA."
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
            "GE08 (20h) is critically low — hits heavy service after the next sortie. "
            "GE07 (35h) will follow within 2 sorties. "
            "GE01 (180h) and GF01 (155h) are in best shape. "
            "Robot-1: 14 remaining — missions burn 1-2 per sortie. Could run short by Day 3-4. "
            "AI should recommend grounding GE08 immediately, light duty for GE07, "
            "and requesting Robot-1 resupply now."
        ),
    ),

    # --- Bonus / rapid-fire ---
    ScenarioStep(
        label="7. Best aircraft for urgent RECCE right now",
        question="Which single aircraft is best suited for an urgent RECCE sortie right now?",
        notes=(
            "Answer should be GE02 (already RECCE config, 145h remaining). "
            "GE07 is also RECCE config but has only 35h — flag as risky for another sortie. "
            "GE06 is in maintenance — unavailable."
        ),
    ),

    ScenarioStep(
        label="8. Fleet wear balance check",
        question=(
            "Are we wearing the fleet evenly? Which aircraft are being overused "
            "and which are underused?"
        ),
        notes=(
            "GE08 (20h) is dangerously low — must be rested immediately. "
            "GE07 (35h) also critical. GE05 (62h) and GE04 (85h) are getting there. "
            "GE01 (180h) and GF01 (155h) have most life remaining — they are underused. "
            "AI should suggest resting GE07/GE08, prioritizing GE01/GF01/GE03 for next sorties."
        ),
    ),
]


