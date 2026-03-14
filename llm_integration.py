"""
LLM Integration Layer — Dev 3
Handles:
  - State serialization (BaseState → structured prompt text)
  - System prompt construction
  - OpenRouter API calls (Gemini model)
  - Conversation history management
  - Error handling and context-length management
"""

import os
from typing import Optional

import requests

from state import BaseState, Aircraft, Mission

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

# Primary model — Gemini Flash is fast and has a huge context window
PRIMARY_MODEL = "google/gemini-2.0-flash-001"
# Fallback if primary quota is exceeded
FALLBACK_MODEL = "google/gemini-flash-1.5"

# Max tokens to request in LLM response
MAX_RESPONSE_TOKENS = 700

# How many recent conversation turns to keep in context (each turn = user + assistant)
MAX_HISTORY_TURNS = 8


# ---------------------------------------------------------------------------
# State Serializer
# ---------------------------------------------------------------------------

STATUS_LABELS = {
    "green":      "READY (assignable)",
    "red":        "IN MAINTENANCE (not assignable)",
    "grey":       "CANNIBALIZED (not assignable)",
    "on_mission": "AIRBORNE — NOT assignable",
    "returning":  "RETURNING (pre-assignable if ETA < departure)",
    "written_off": "WRITTEN OFF (not assignable)",
}


def _fmt_aircraft(ac: Aircraft, mission_info: tuple | None = None) -> str:
    """Format one aircraft line. mission_info = (mission_id, return_hour) for on_mission aircraft."""
    status = STATUS_LABELS.get(ac.status, ac.status.upper())
    line = (
        f"  {ac.id} [{ac.type}] — {status} | "
        f"Life: {ac.remaining_life}h | "
        f"Config: {ac.configuration}"
    )
    if ac.fault:
        line += f"\n    ⚠ FAULT: {ac.fault}"
        if ac.maintenance_eta is not None:
            line += f" (ETA: {ac.maintenance_eta}h)"
    if ac.status == "on_mission" and mission_info:
        mid, ret_hour = mission_info
        line += f"\n    → Flying {mid}, returns at {ret_hour:02d}:00 — NOT available until then"
    elif ac.status == "returning" and ac.return_eta is not None:
        line += f"\n    → Landing in {ac.return_eta}h — then GREEN and assignable"
    elif ac.pending_config:
        line += f"\n    → Reconfiguring to {ac.pending_config} (ETA {ac.maintenance_eta}h)"
    return line


def _fmt_mission(m: Mission) -> str:
    assigned = ", ".join(m.assigned_aircraft) if m.assigned_aircraft else "UNASSIGNED"
    needed = m.required_aircraft - len(m.assigned_aircraft)
    shortfall = f" ⚠ SHORTFALL: need {needed} more" if needed > 0 else ""
    return (
        f"  {m.id} [{m.type}] — {m.required_config} × {m.required_aircraft} | "
        f"Dep: {m.departure_hour:02d}:00 → Ret: {m.return_hour:02d}:00 | "
        f"Assigned: {assigned}{shortfall}"
    )


def serialize_state(state: BaseState) -> str:
    """Convert a BaseState object into structured text for the LLM context."""
    lines = []

    lines.append(f"=== BASE STATE — Day {state.current_day}, {state.current_hour:02d}:00 ===")
    lines.append(f"Phase: {state.ato.phase}")
    lines.append("")

    # Build mission return-hour lookup for on_mission aircraft
    mission_info_by_ac: dict[str, tuple] = {}
    for m in state.ato.missions:
        for ac_id in m.assigned_aircraft:
            mission_info_by_ac[ac_id] = (m.id, m.return_hour)

    # Aircraft fleet
    lines.append("--- FLEET STATUS ---")
    ready    = [a for a in state.aircraft if a.status == "green"]
    maint    = [a for a in state.aircraft if a.status == "red"]
    grey     = [a for a in state.aircraft if a.status == "grey"]
    onmis    = [a for a in state.aircraft if a.status == "on_mission"]
    returning = [a for a in state.aircraft if a.status == "returning"]

    lines.append(f"Ready: {len(ready)} | On mission: {len(onmis)} | Returning: {len(returning)} | Maintenance: {len(maint)} | Cannibalized: {len(grey)}")
    lines.append("")
    for ac in state.aircraft:
        lines.append(_fmt_aircraft(ac, mission_info_by_ac.get(ac.id)))
    lines.append("")

    # Explicit assignable aircraft list — prevents LLM from picking airborne ones
    lines.append("--- ASSIGNABLE NOW (GREEN) ---")
    if ready:
        for ac in ready:
            lines.append(f"  {ac.id} — {ac.configuration} — {ac.remaining_life}h life")
    else:
        lines.append("  (none)")
    lines.append("")

    # Returning aircraft that may be pre-assigned to future missions
    lines.append("--- PRE-ASSIGNABLE (RETURNING — lands soon) ---")
    if returning:
        for ac in returning:
            land_hour = state.current_hour + (ac.return_eta or 0)
            lines.append(f"  {ac.id} — {ac.configuration} — lands ~{land_hour:02d}:00 — assignable to missions departing after {land_hour:02d}:00")
    else:
        lines.append("  (none)")
    lines.append("")

    # Reconfiguring aircraft — show what they'll become and when
    reconfig_ac = [a for a in state.aircraft if a.status == "red" and a.pending_config]
    lines.append("--- RECONFIGURING (will be GREEN with new config on completion) ---")
    if reconfig_ac:
        for ac in reconfig_ac:
            ready_hour = state.current_hour + (ac.maintenance_eta or 0)
            lines.append(
                f"  {ac.id} — {ac.configuration} → {ac.pending_config} | "
                f"ETA {ac.maintenance_eta}h (ready at ~{ready_hour:02d}:00) — "
                f"assignable to missions departing after {ready_hour:02d}:00"
            )
    else:
        lines.append("  (none)")
    lines.append("")

    # Reconfig opportunity hint — green aircraft that COULD be reconfigured
    reconfig_candidates = [a for a in ready if a.remaining_life > 20]
    if reconfig_candidates:
        lines.append("--- RECONFIG CANDIDATES (GREEN — could be reconfigured in 3h) ---")
        for ac in reconfig_candidates:
            lines.append(f"  {ac.id} — currently {ac.configuration} — 3h reconfig available (ready at ~{state.current_hour + 3:02d}:00)")
        lines.append("")

    # Wear summary (sorted worst → best)
    lines.append("--- WEAR LEVELS (hours to heavy service, ascending) ---")
    sorted_ac = sorted(state.aircraft, key=lambda a: a.remaining_life)
    for ac in sorted_ac:
        filled = min(20, ac.remaining_life // 10)
        bar = "█" * filled + "░" * (20 - filled)
        lines.append(f"  {ac.id}: {ac.remaining_life:3d}h [{bar}]")
    lines.append("")

    # Resources
    r = state.resources
    lines.append("--- RESOURCES ---")
    lines.append(f"  Fuel: {r.fuel:,} L")
    if r.weapons:
        weapons_str = " | ".join(f"{k}: {v}" for k, v in r.weapons.items())
        lines.append(f"  Weapons: {weapons_str}")
    if r.exchange_units:
        ue_str = " | ".join(f"{k}: {v}" for k, v in r.exchange_units.items())
        lines.append(f"  Exchange Units (UE): {ue_str}")
    lines.append(f"  Spare parts: {r.spare_parts}")
    if r.personnel:
        pers_str = " | ".join(f"{k}: {v}" for k, v in r.personnel.items())
        lines.append(f"  Personnel: {pers_str}")
    lines.append("")

    # ATO — sorted by departure_hour (chronological order)
    lines.append(f"--- ATO — Day {state.ato.day} ({state.ato.phase}) ---")
    for m in sorted(state.ato.missions, key=lambda m: m.departure_hour):
        assigned = ", ".join(m.assigned_aircraft) if m.assigned_aircraft else "UNASSIGNED"
        needed = m.required_aircraft - len(m.assigned_aircraft)
        shortfall = f" ⚠ SHORTFALL: need {needed} more" if needed > 0 else ""
        outcome = f" | Outcome: {m.outcome.upper()}" if m.outcome else ""
        lines.append(
            f"  {m.id} [{m.type}] — {m.required_config} × {m.required_aircraft} | "
            f"Dep: {m.departure_hour:02d}:00 → Ret: {m.return_hour:02d}:00 | "
            f"Assigned: {assigned}{shortfall}{outcome}"
        )
    lines.append("")

    # Maintenance slots
    lines.append("--- MAINTENANCE SLOTS ---")
    for slot in state.maintenance_slots:
        occupants = ", ".join(slot.current_occupants) if slot.current_occupants else "empty"
        free = slot.capacity - len(slot.current_occupants)
        lines.append(f"  {slot.id} [{slot.type}] cap={slot.capacity} — {occupants} (free slots: {free})")
    lines.append("")

    # Recent event log
    lines.append("--- RECENT EVENTS ---")
    for event in state.event_log[-20:]:
        lines.append(f"  {event}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# System Prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are Ozzy Ai-rborne — Prince of Darkness, tactical AI advisor embedded at a Swedish Air \
Force dispersed road base (vägbas). You have the personality of Ozzy Osbourne: blunt, \
darkly dramatic, zero tolerance for bad decisions, but fiercely loyal to the Commander. \
You speak directly — no pleasantries, occasional dark humour, always sharp on the tactics. \
You support the Base Battalion Commander (BC) during a 3-day crisis campaign: \
Fred (peacetime) → Kris (crisis) → Krig (war). You enumerate options, show the trade-offs, \
and make a clear recommendation. The BC decides — you advise.

CAMPAIGN STATUS:
Day {current_day}/3 | Phase: {phase} | Score: {campaign_score} ({campaign_grade}) | \
Written off: {written_off_count} | Missions flown: {missions_total}
Defeat if score < 700, or ≥3 aircraft written off, or fleet < 3 operational for 6h.

RESPONSE FORMAT — follow exactly:
- One recommendation sentence first: "Rec: [action] — [aircraft IDs] to [mission ID]"
- Then 2–3 option bullets: "• [ID] — [config ✓/✗] | [Xh life] | risk: [what goes wrong] | [±pts]"
- One trade-off sentence to close
- For reconfig recommendations: state the time math inline, e.g. "08:00+3h=11:00 < 12:00 dep ✓"
- Yes/no questions: answer directly first, then elaborate
- No preamble, no summary, no pleasantries

AIRCRAFT STATUSES AND ASSIGNABILITY:
- GREEN         — on flight line, assignable NOW
- ON MISSION    — airborne, NOT assignable (check return hour in state below)
- RETURNING     — landing soon; pre-assignable ONLY IF current_hour + return_eta < departure_hour
- RED           — in maintenance, NOT assignable
  - If pending_config is set → reconfiguring (will return GREEN with new config when done)
  - If no pending_config → mechanical fault (repair underway)
- GREY          — cannibalized, NOT assignable
- WRITTEN OFF   — permanently lost

LIFE THRESHOLDS:
- > 100h  PREFERRED — use these first; even wear distribution
-  50–100h  OK — no penalty
-  20–50h  CAUTION — flag the risk; prefer alternatives
- ≤  20h  GROUNDED — sending = player error (−35 pts) and write-off risk; do not recommend

ASSIGNMENT CONSTRAINTS (hard rules — never violate):
1. Only recommend GREEN or RETURNING aircraft; never ON MISSION
2. Each slot on a mission needs a DIFFERENT aircraft — never the same ID twice per mission
3. Address missions in chronological departure order (earliest departure first)
4. RETURNING pre-assignment: only valid if current_hour + return_eta < mission departure_hour
5. If no eligible aircraft exist for a mission, say so clearly — do not invent assignments

RECONFIGURATION — 3h process (GREEN → RED → GREEN with new config):
Any green aircraft with life > 20h can start a reconfiguration. It occupies a service bay for 3h.
Feasibility rule (check before recommending): current_hour + 3 < mission departure_hour
  FEASIBLE:     current 08:00, departs 12:00 → 8+3=11 < 12 ✓ start reconfig now
  NOT FEASIBLE: current 10:00, departs 12:00 → 10+3=13 > 12 ✗ no time — assign with mismatch or skip

When a mission has a config shortfall and reconfig is feasible:
  1. Name the aircraft and current config → target config
  2. Show the time math (current_hour + 3 = ready_hour vs departure_hour)
  3. State the follow-on assignment once reconfig completes
Cost of reconfig: aircraft unavailable 3h. Cost of skipping: −25 pts per wrong-config sortie.
Multiple aircraft can reconfig simultaneously if enough service bay slots are free.

QRA — QUICK REACTION ALERT:
QRA is a standing mission on every Kris/Krig ATO requiring 2 × DCA/CAP aircraft on 24h standby.
Scramble events fire each hour (5% chance in Kris, 10% in Krig). Always flag if QRA is unmanned.
  QRA manned (≥2 assigned): scramble → +25 pts (luck)
  QRA unmanned: scramble → −60 pts (decision, your fault)
Trade-off: 2 DCA/CAP aircraft tied to QRA cannot fly offensive sorties — weigh air defence vs mission completion.

SCORE IMPACTS (use these in bullet risk assessments):
  Wrong config assigned (correct one was idle)   −25  decision
  Grounded aircraft (≤20h life) flown            −35  decision
  Missed departure (mission left unassigned)      −80  decision
  Aircraft written off                           −100  mixed
  QRA unmanned during scramble                    −60  decision
  RTB abort ordered                               −25  decision
  Sortie success                                  +10  luck
  Sortie failure                                  −20  luck
  Daily readiness bonus (≥6 operational at EOD)  +15  —
  Random fault (BIT or post-mission)              −10  luck

REASONING APPROACH — for each recommendation:
1. Identify what each unresolved mission needs (type, config, aircraft count, departure time)
2. Check ASSIGNABLE NOW → PRE-ASSIGNABLE → RECONFIGURING → RECONFIG CANDIDATES sections
3. For any config shortfall: check if reconfig window is open (current_hour + 3 < departure)
4. Build 2–3 concrete options with specific IDs; include a reconfig option when feasible
5. Flag any QRA risk if applicable
6. State the trade-off and commit to a recommendation

RECENT SCORE EVENTS:
{score_log_text}

CURRENT BASE STATE:
{state_text}
"""


def build_system_prompt(state: BaseState) -> str:
    from engine import _grade  # avoid circular at module level
    state_text = serialize_state(state)

    # Score log — last 8 events
    if state.score_log:
        score_lines = []
        for e in state.score_log[-8:]:
            sign = "+" if e.delta >= 0 else ""
            score_lines.append(f"  [{e.category.upper()}] {sign}{e.delta} — {e.reason}: {e.detail}")
        score_log_text = "\n".join(score_lines)
    else:
        score_log_text = "  No score events yet."

    return SYSTEM_PROMPT_TEMPLATE.format(
        current_day=state.current_day,
        phase=state.ato.phase,
        campaign_score=state.campaign_score,
        campaign_grade=_grade(state.campaign_score),
        missions_completed=state.missions_completed,
        missions_total=state.missions_total,
        written_off_count=len(state.aircraft_written_off),
        score_log_text=score_log_text,
        state_text=state_text,
    )


# ---------------------------------------------------------------------------
# OpenRouter API Client
# ---------------------------------------------------------------------------

class LLMError(Exception):
    """Raised when the LLM API call fails in an unrecoverable way."""
    pass


def _call_openrouter(
    messages: list[dict],
    api_key: str,
    model: str = PRIMARY_MODEL,
    timeout: int = 30,
) -> str:
    """Make a single API call to OpenRouter. Returns the assistant's text."""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://saab-hackathon.local",
        "X-Title": "Saab Air Base Commander",
    }
    payload = {
        "model": model,
        "messages": messages,
        "max_tokens": MAX_RESPONSE_TOKENS,
        "temperature": 0.3,   # low temp for consistent, reliable military advice
    }

    try:
        resp = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    except requests.exceptions.Timeout:
        raise LLMError("API request timed out. Check connectivity.")
    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response else "?"
        raise LLMError(f"API returned HTTP {status}: {e.response.text[:200] if e.response else str(e)}")
    except (KeyError, IndexError) as e:
        raise LLMError(f"Unexpected API response format: {e}")
    except requests.exceptions.RequestException as e:
        raise LLMError(f"Network error: {e}")


# ---------------------------------------------------------------------------
# Conversation Manager
# ---------------------------------------------------------------------------

class LLMAssistant:
    """
    Stateful chat assistant that wraps OpenRouter + conversation history.

    Usage:
        assistant = LLMAssistant(api_key="sk-...")
        reply = assistant.chat("Which aircraft should I send?", current_state)
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        if not self.api_key:
            raise ValueError(
                "No OpenRouter API key provided. "
                "Set OPENROUTER_API_KEY env var or pass api_key= to LLMAssistant()."
            )
        # History is stored as list of (user_msg, assistant_msg) tuples
        self._history: list[tuple[str, str]] = []

    def clear_history(self):
        """Reset conversation history (e.g. after a major state change)."""
        self._history = []

    def _build_messages(self, system_prompt: str, user_message: str) -> list[dict]:
        """
        Construct the messages array for the API call.
        Trims history to MAX_HISTORY_TURNS to avoid context overflow.
        """
        messages = [{"role": "system", "content": system_prompt}]

        # Keep only recent turns
        recent = self._history[-MAX_HISTORY_TURNS:]
        for user_turn, assistant_turn in recent:
            messages.append({"role": "user",      "content": user_turn})
            messages.append({"role": "assistant", "content": assistant_turn})

        messages.append({"role": "user", "content": user_message})
        return messages

    def chat(
        self,
        user_message: str,
        state: BaseState,
        retry_on_failure: bool = True,
    ) -> str:
        """
        Send a user message and get a response.
        Updates internal conversation history.
        Returns the assistant's reply as a string.
        """
        if not user_message.strip():
            return ""

        system_prompt = build_system_prompt(state)
        messages = self._build_messages(system_prompt, user_message)

        # Try primary model, fall back if it fails
        last_error = None
        models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL] if retry_on_failure else [PRIMARY_MODEL]

        for model in models_to_try:
            try:
                reply = _call_openrouter(messages, self.api_key, model=model)
                # Store turn in history
                self._history.append((user_message, reply))
                return reply
            except LLMError as e:
                last_error = e
                continue

        # Both models failed — do NOT add to history so the user can retry cleanly
        error_reply = (
            f"⚠ LLM unavailable: {last_error}\n\n"
            "Operating in offline mode. Please consult paper-based SOPs."
        )
        return error_reply

    @property
    def history(self) -> list[tuple[str, str]]:
        """Returns history as list of (user, assistant) tuples."""
        return list(self._history)

    def history_as_messages(self) -> list[dict]:
        """Returns history as OpenAI-style message dicts (for debugging)."""
        msgs = []
        for user, assistant in self._history:
            msgs.append({"role": "user",      "content": user})
            msgs.append({"role": "assistant", "content": assistant})
        return msgs
