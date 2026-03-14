"""
Game State Engine — Dev 1
Saab Smart Air Base Hackathon

Provides:
  - create_initial_state()     Build a realistic Day-2 Kris scenario
  - get_state() / reset_state() Module-level singleton for API/LLM layers
  - State mutation functions:  assign_aircraft, trigger_fault, complete_maintenance,
                               consume_resources, advance_time, return_from_mission
  - Dice / random events:      roll_bit_check, roll_post_mission, roll_fault_type,
                               roll_weapons_expenditure, roll_maintenance_variance,
                               generate_random_event
  - Serializers:               serialize_state (text), serialize_state_json (dict)
"""

from __future__ import annotations

import json
import random

from state import (
    Aircraft,
    ATO,
    BaseState,
    MaintenanceSlot,
    Mission,
    ResourceInventory,
    ScoreEvent,
)

# ---------------------------------------------------------------------------
# Fault type table (from brief)
# ---------------------------------------------------------------------------
FAULT_TABLE: dict[int, dict] = {
    1: {"description": "Quick LRU replacement (AU Steg 1)",     "hours": 2,  "slot_type": "service_bay"},
    2: {"description": "Quick LRU replacement (AU Steg 2/3)",   "hours": 2,  "slot_type": "service_bay"},
    3: {"description": "Complex LRU replacement (AU Steg 4)",   "hours": 6,  "slot_type": "service_bay"},
    4: {"description": "Direct repair (Kompositrep)",           "hours": 16, "slot_type": "maint_workshop"},
    5: {"description": "Minor troubleshooting (FK steg 1-3)",   "hours": 4,  "slot_type": "service_bay"},
    6: {"description": "Minor troubleshooting (FK steg 1-3)",   "hours": 4,  "slot_type": "service_bay"},
}

WEAPONS_EXPENDITURE_TABLE: dict[int, float] = {
    1: 0.10,
    2: 0.30,
    3: 0.50,
    4: 0.70,
    5: 0.90,
    6: 1.00,
}

MAINTENANCE_VARIANCE_TABLE: dict[int, float] = {
    1: 1.0,
    2: 1.0,
    3: 1.0,
    4: 1.1,
    5: 1.2,
    6: 1.5,
}

FUEL_PER_SORTIE = 4000  # liters per Gripen sortie


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
_state: BaseState | None = None


def get_state() -> BaseState:
    """Return the current global state, initializing if needed."""
    global _state
    if _state is None:
        _state = create_initial_state()
    return _state


def reset_state() -> BaseState:
    """Reinitialize to default starting state and return it."""
    global _state
    _state = create_initial_state()
    return _state


# ---------------------------------------------------------------------------
# Initial state
# ---------------------------------------------------------------------------
def create_initial_state() -> BaseState:
    """
    Build a realistic Day-2 Kris scenario:
      - 10 aircraft with varied wear levels
      - 5 ATO missions
      - Finite resources
      - 2 maintenance slots (service bay + workshop)
    """
    aircraft = [
        Aircraft(
            id="GE01", type="GripenE", status="green",
            remaining_life=180, total_flight_hours=120,
            configuration="DCA/CAP", current_payload=["Robot-1", "Robot-1", "ExtraTank"],
            location="flight_line",
        ),
        Aircraft(
            id="GE02", type="GripenE", status="green",
            remaining_life=145, total_flight_hours=155,
            configuration="RECCE", current_payload=["RecconPod", "ExtraTank"],
            location="flight_line",
        ),
        Aircraft(
            id="GE03", type="GripenE", status="green",
            remaining_life=110, total_flight_hours=190,
            configuration="DCA/CAP", current_payload=["Robot-1", "Robot-1"],
            location="flight_line",
        ),
        Aircraft(
            id="GE04", type="GripenE", status="green",
            remaining_life=85, total_flight_hours=215,
            configuration="AI/ST", current_payload=["Bomb-2", "Bomb-2", "ExtraTank"],
            location="flight_line",
        ),
        Aircraft(
            id="GE05", type="GripenE", status="green",
            remaining_life=62, total_flight_hours=238,
            configuration="DCA/CAP", current_payload=["Robot-1", "Robot-1"],
            location="flight_line",
        ),
        Aircraft(
            id="GE06", type="GripenE", status="green",
            remaining_life=48, total_flight_hours=252,
            configuration="DCA/CAP", current_payload=["Robot-1"],
            location="flight_line",
        ),
        Aircraft(
            id="GE07", type="GripenE", status="green",
            remaining_life=35, total_flight_hours=265,
            configuration="RECCE", current_payload=["RecconPod"],
            location="flight_line",
        ),
        Aircraft(
            id="GE08", type="GripenE", status="green",
            remaining_life=20, total_flight_hours=280,
            configuration="DCA/CAP", current_payload=["Robot-1"],
            location="flight_line",
        ),
        Aircraft(
            id="GF01", type="GripenF", status="green",
            remaining_life=155, total_flight_hours=45,
            configuration="DCA/CAP", current_payload=["Robot-1", "Robot-1", "ExtraTank"],
            location="flight_line",
        ),
        Aircraft(
            id="GF02", type="GripenF", status="green",
            remaining_life=95, total_flight_hours=105,
            configuration="DCA/CAP", current_payload=["Robot-1", "Robot-1"],
            location="flight_line",
        ),
    ]

    resources = ResourceInventory(
        fuel=80_000,
        weapons={
            "Robot-1": 14,
            "Bomb-2": 8,
            "Robot-15": 4,
        },
        exchange_units={
            "Radar": 3,
            "SignalProcessor": 2,
            "EjectionSeat": 1,
            "HydraulicPump": 2,
        },
        spare_parts=24,
        personnel={
            "klargoring_crew": 4,
            "maintenance_tech": 3,
            "pilots": 8,
        },
        tools={
            "test_equipment": 2,
            "heavy_lift": 1,
        },
    )

    missions = [
        Mission(
            id="M01", type="DCA", required_aircraft=2, required_config="DCA/CAP",
            departure_hour=10, return_hour=13,
            description="Combat Air Patrol — northern sector",
        ),
        Mission(
            id="M02", type="DCA", required_aircraft=2, required_config="DCA/CAP",
            departure_hour=14, return_hour=17,
            description="Combat Air Patrol — western sector",
        ),
        Mission(
            id="M03", type="DCA", required_aircraft=2, required_config="DCA/CAP",
            departure_hour=20, return_hour=23,
            description="Night CAP — northern sector",
        ),
        Mission(
            id="M04", type="RECCE", required_aircraft=1, required_config="RECCE",
            departure_hour=9, return_hour=11,
            description="Photo reconnaissance — bridge complex",
        ),
        Mission(
            id="M05", type="AI/ST", required_aircraft=2, required_config="AI/ST",
            departure_hour=12, return_hour=14,
            description="Air Interdiction — supply route strike",
        ),
        Mission(
            id="M06", type="QRA", required_aircraft=2, required_config="DCA/CAP",
            departure_hour=0, return_hour=23,
            description="Quick Reaction Alert — on standby",
        ),
    ]

    ato = ATO(day=1, phase="Fred", missions=missions)

    maintenance_slots = [
        MaintenanceSlot(
            id="service_bay", type="service_bay", capacity=2,
            current_occupants=[],
        ),
        MaintenanceSlot(
            id="minor_workshop", type="minor_workshop", capacity=1,
            current_occupants=[],
        ),
        MaintenanceSlot(
            id="major_workshop", type="major_workshop", capacity=1,
            current_occupants=[],
        ),
    ]

    return BaseState(
        current_hour=8,
        current_day=1,
        aircraft=aircraft,
        resources=resources,
        ato=ato,
        maintenance_slots=maintenance_slots,
        event_log=["[Day 1 08:00] Campaign started. Day 1 Fred ATO loaded. All 10 aircraft ready. Survive 3 days."],
    )


# ---------------------------------------------------------------------------
# Dice helpers
# ---------------------------------------------------------------------------
def roll_dice() -> int:
    return random.randint(1, 6)


def roll_bit_check() -> tuple[bool, int | None]:
    """Returns (passed, fault_roll). fault_roll is 1-6 if failed, else None."""
    r = roll_dice()
    if r <= 4:
        return True, None
    fault_roll = roll_dice()
    return False, fault_roll


def roll_post_mission() -> tuple[bool, int | None]:
    """Same probabilities as BIT check."""
    return roll_bit_check()


def roll_fault_type(fault_roll: int | None = None) -> dict:
    """Returns fault info dict from FAULT_TABLE."""
    r = fault_roll if fault_roll is not None else roll_dice()
    return dict(FAULT_TABLE[r])


def roll_weapons_expenditure(weapons_roll: int | None = None) -> float:
    """Returns fraction of weapons expended (0.0–1.0)."""
    r = weapons_roll if weapons_roll is not None else roll_dice()
    return WEAPONS_EXPENDITURE_TABLE[r]


def roll_maintenance_variance(variance_roll: int | None = None) -> float:
    """Returns time multiplier (1.0, 1.1, 1.2, or 1.5)."""
    r = variance_roll if variance_roll is not None else roll_dice()
    return MAINTENANCE_VARIANCE_TABLE[r]


# ---------------------------------------------------------------------------
# Helper: find aircraft by ID
# ---------------------------------------------------------------------------
def _find_aircraft(state: BaseState, aircraft_id: str) -> Aircraft:
    for ac in state.aircraft:
        if ac.id == aircraft_id:
            return ac
    raise ValueError(f"Aircraft '{aircraft_id}' not found in state")


def _find_aircraft_safe(state: BaseState, aircraft_id: str) -> Aircraft | None:
    """Like _find_aircraft but returns None instead of raising if not found."""
    return next((ac for ac in state.aircraft if ac.id == aircraft_id), None)


def _find_mission(state: BaseState, mission_id: str) -> Mission:
    for m in state.ato.missions:
        if m.id == mission_id:
            return m
    raise ValueError(f"Mission '{mission_id}' not found in ATO")


def _find_slot_for_aircraft(state: BaseState, aircraft_id: str) -> MaintenanceSlot | None:
    for slot in state.maintenance_slots:
        if aircraft_id in slot.current_occupants:
            return slot
    return None


def _log(state: BaseState, msg: str) -> None:
    entry = f"[Day {state.current_day} {state.current_hour:02d}:00] {msg}"
    state.event_log.append(entry)
    if len(state.event_log) > 100:
        state.event_log = state.event_log[-100:]


def _score(state: BaseState, delta: int, reason: str, detail: str, category: str) -> None:
    """Record a score event and update the campaign score."""
    event = ScoreEvent(
        day=state.current_day,
        hour=state.current_hour,
        delta=delta,
        reason=reason,
        detail=detail,
        category=category,
    )
    state.score_log.append(event)
    if len(state.score_log) > 50:
        state.score_log = state.score_log[-50:]
    state.campaign_score += delta
    sign = "+" if delta >= 0 else ""
    _log(state, f"SCORE {sign}{delta} [{category.upper()}] {reason}")


# Mission success probability
_MISSION_BASE_SUCCESS = {
    "DCA":   0.75,
    "RECCE": 0.85,
    "AI/ST": 0.70,
    "QRA":   0.90,
    "AEW":   0.80,
}

def _compute_success_prob(ac: Aircraft, mission: Mission, phase: str) -> float:
    base = _MISSION_BASE_SUCCESS.get(mission.type, 0.75)
    if ac.configuration == mission.required_config:
        base += 0.10
    else:
        base -= 0.15
    if ac.remaining_life > 100:
        base += 0.05
    elif ac.remaining_life <= 20:
        base -= 0.30
    elif ac.remaining_life <= 50:
        base -= 0.15
    if phase == "Kris":
        base -= 0.05
    elif phase == "Krig":
        base -= 0.15
    return max(0.05, min(0.95, base))


def _check_fail_states(state: BaseState) -> None:
    """Check and trigger campaign fail/victory states. Mutates state in-place."""
    if state.campaign_over:
        return

    # Campaign complete — survived all 3 days
    if state.current_day > 3:
        state.campaign_over = True
        grade = _grade(state.campaign_score)
        state.campaign_result = "victory"
        state.campaign_over_reason = f"3-day campaign survived. Final score: {state.campaign_score} — {grade}"
        _log(state, f"CAMPAIGN COMPLETE — Victory! Score: {state.campaign_score} ({grade})")
        return

    # Score collapse
    if state.campaign_score < 700:
        state.campaign_over = True
        state.campaign_result = "defeat"
        state.campaign_over_reason = f"Score collapsed to {state.campaign_score} — too many critical decisions went wrong."
        _log(state, "CAMPAIGN OVER — Score collapse. Too many critical decisions went wrong.")
        return

    # Strategic defeat — too many aircraft written off
    if len(state.aircraft_written_off) >= 3:
        state.campaign_over = True
        state.campaign_result = "defeat"
        state.campaign_over_reason = f"{len(state.aircraft_written_off)} aircraft written off — fleet capability destroyed."
        _log(state, "CAMPAIGN OVER — Strategic defeat. Aircraft losses unsustainable.")
        return

    # Fleet collapse — track consecutive hours below 3 operational
    operational = [ac for ac in state.aircraft if ac.status in ("green", "on_mission", "returning")]
    if len(operational) < 3:
        state.low_fleet_hours += 1
        if state.low_fleet_hours >= 6:
            state.campaign_over = True
            state.campaign_result = "defeat"
            state.campaign_over_reason = f"Fleet collapsed — fewer than 3 aircraft operational for {state.low_fleet_hours}h."
            _log(state, "CAMPAIGN OVER — Fleet collapse. Operational capacity destroyed.")
    else:
        state.low_fleet_hours = 0


def _grade(score: int) -> str:
    if score >= 950:  return "Gold — Outstanding"
    if score >= 875:  return "Silver — Commended"
    if score >= 800:  return "Bronze — Satisfactory"
    if score >= 700:  return "Marginal — Survived"
    return "Busted — Campaign Failed"


# ---------------------------------------------------------------------------
# State mutation functions
# ---------------------------------------------------------------------------
def assign_aircraft(state: BaseState, mission_id: str, aircraft_ids: list[str]) -> BaseState:
    """Assign a list of aircraft to a mission. Aircraft must be green."""
    mission = _find_mission(state, mission_id)

    # Release previously assigned aircraft that are being replaced
    for prev_id in list(mission.assigned_aircraft):
        if prev_id not in aircraft_ids:
            try:
                prev_ac = _find_aircraft(state, prev_id)
                if prev_ac.status == "on_mission":
                    prev_ac.status = "green"
                    prev_ac.location = "flight_line"
                    _log(state, f"{prev_id} unassigned from mission {mission_id} — returned to flight line")
            except ValueError:
                pass

    # Check if any correct-config aircraft are being ignored
    correct_config_idle = [
        ac for ac in state.aircraft
        if ac.status == "green"
        and ac.configuration == mission.required_config
        and ac.id not in aircraft_ids
    ]

    for ac_id in aircraft_ids:
        ac = _find_aircraft(state, ac_id)

        if ac.status == "returning":
            # Pre-assignment: validate aircraft will land before mission departs
            if ac.return_eta is None:
                raise ValueError(f"Cannot pre-assign {ac_id}: returning aircraft has no ETA")
            land_at_hour = state.current_hour + ac.return_eta
            if land_at_hour >= mission.departure_hour:
                raise ValueError(
                    f"Cannot pre-assign {ac_id}: lands at ~{land_at_hour:02d}:00 "
                    f"but mission {mission_id} departs at {mission.departure_hour:02d}:00"
                )
            # Leave status as 'returning' — advance_time will dispatch at departure_hour
            _log(state, f"{ac_id} pre-assigned to {mission_id} — will auto-dispatch at {mission.departure_hour:02d}:00 after landing")
        elif ac.status == "green":
            if ac.configuration != mission.required_config:
                _log(state, f"WARNING: {ac_id} config '{ac.configuration}' ≠ mission {mission_id} required '{mission.required_config}'")
                if correct_config_idle:
                    idle_ids = ", ".join(a.id for a in correct_config_idle)
                    _score(
                        state, -25, "Config mismatch",
                        f"{ac_id} assigned to {mission.type} with wrong config. {idle_ids} had correct config and was idle.",
                        "decision",
                    )
            if ac.remaining_life <= 20:
                _score(
                    state, -35, "Grounded aircraft flown",
                    f"{ac_id} sent on {mission.type} sortie with only {ac.remaining_life}h remaining life (threshold: 20h).",
                    "decision",
                )
            if mission.departure_hour <= state.current_hour:
                # Mission already departing / in progress — dispatch immediately
                ac.status = "on_mission"
                ac.location = "on_mission"
            # else: future mission — leave green; advance_time will dispatch at departure_hour
        else:
            raise ValueError(f"Cannot assign {ac_id}: status is '{ac.status}' (must be green or returning)")

    mission.assigned_aircraft = list(aircraft_ids)
    _log(state, f"Assigned {', '.join(aircraft_ids)} to mission {mission_id} ({mission.type}) — departure {mission.departure_hour:02d}:00")
    return state


def trigger_fault(
    state: BaseState,
    aircraft_id: str,
    fault_roll: int | None = None,
) -> BaseState:
    """
    Put an aircraft into maintenance.
    fault_roll: 1-6 to select fault type; rolls randomly if omitted.
    """
    ac = _find_aircraft(state, aircraft_id)
    if ac.status == "red":
        raise ValueError(f"Cannot fault {aircraft_id}: already in maintenance")

    fault_info = roll_fault_type(fault_roll)
    variance = roll_maintenance_variance()
    hours = int(fault_info["hours"] * variance)

    ac.status = "red"
    ac.fault = fault_info["description"]
    ac.maintenance_eta = hours

    # Move aircraft to appropriate maintenance slot
    slot_type = fault_info["slot_type"]
    target_slot = next(
        (s for s in state.maintenance_slots if s.type == slot_type and len(s.current_occupants) < s.capacity),
        None,
    )
    if target_slot is None:
        # Fall back to any slot with capacity
        target_slot = next(
            (s for s in state.maintenance_slots if len(s.current_occupants) < s.capacity),
            None,
        )

    if target_slot:
        target_slot.current_occupants.append(aircraft_id)
        ac.location = target_slot.id
    else:
        ac.location = "flight_line"  # No slot available — aircraft waits
        _log(state, f"WARNING: No maintenance slot available for {aircraft_id}!")

    _log(state, f"{aircraft_id} fault: {fault_info['description']} — ETA {hours}h")
    return state


def _write_off_aircraft(state: BaseState, aircraft_id: str) -> None:
    """Mark an aircraft as permanently written off (life = 0)."""
    ac = _find_aircraft(state, aircraft_id)
    ac.status = "written_off"
    ac.location = "written_off"
    ac.remaining_life = 0
    if aircraft_id not in state.aircraft_written_off:
        state.aircraft_written_off.append(aircraft_id)
    _log(state, f"CRITICAL: {aircraft_id} WRITTEN OFF — life exhausted. Aircraft permanently out of service.")
    _score(
        state, -100, f"{aircraft_id} written off",
        f"{aircraft_id} reached 0h remaining life and is permanently grounded.",
        "mixed",
    )


def complete_maintenance(state: BaseState, aircraft_id: str) -> BaseState:
    """Mark maintenance complete; aircraft returns to flight line as green.
    If pending_config is set, applies it (reconfiguration complete)."""
    ac = _find_aircraft(state, aircraft_id)
    if ac.status != "red":
        raise ValueError(f"Cannot complete maintenance on {aircraft_id}: status is '{ac.status}' (must be red)")
    slot = _find_slot_for_aircraft(state, aircraft_id)
    if slot:
        slot.current_occupants.remove(aircraft_id)

    ac.status = "green"
    ac.fault = None
    ac.maintenance_eta = None
    ac.location = "flight_line"

    if ac.pending_config is not None:
        old_config = ac.configuration
        ac.configuration = ac.pending_config
        ac.pending_config = None
        _log(state, f"{aircraft_id} reconfiguration complete — {old_config} → {ac.configuration}. Returned to flight line (green)")
    else:
        _log(state, f"{aircraft_id} maintenance complete — returned to flight line (green)")
    return state


RECONFIG_HOURS = 3  # hours to reconfigure an aircraft to a different configuration


def reconfigure_aircraft(state: BaseState, aircraft_id: str, new_config: str) -> BaseState:
    """Send a ready (green) aircraft for reconfiguration. Takes RECONFIG_HOURS hours."""
    valid_configs = {"DCA/CAP", "RECCE", "AI/ST", "AEW&C"}
    if new_config not in valid_configs:
        raise ValueError(f"Invalid config '{new_config}' — must be one of {sorted(valid_configs)}")
    ac = _find_aircraft(state, aircraft_id)
    if ac.status != "green":
        raise ValueError(f"Cannot reconfigure {aircraft_id}: status is '{ac.status}' (must be green)")
    if ac.configuration == new_config:
        raise ValueError(f"{aircraft_id} is already configured as {new_config}")

    ac.status = "red"
    ac.fault = f"Reconfiguration: {ac.configuration} → {new_config}"
    ac.pending_config = new_config
    ac.maintenance_eta = RECONFIG_HOURS
    ac.location = "service_bay"

    # Occupy a service bay slot if available
    target_slot = next(
        (s for s in state.maintenance_slots if s.type == "service_bay" and len(s.current_occupants) < s.capacity),
        None,
    )
    if target_slot:
        target_slot.current_occupants.append(aircraft_id)
        ac.location = target_slot.id

    _log(state, f"{aircraft_id} reconfiguration started: {ac.fault} — ETA {RECONFIG_HOURS}h")
    return state


def consume_resources(
    state: BaseState,
    mission_id: str,
    weapons_roll: int | None = None,
) -> BaseState:
    """
    Deduct fuel and weapons for a completed mission.
    weapons_roll: 1-6 for expenditure fraction; rolls randomly if omitted.
    """
    mission = _find_mission(state, mission_id)
    n_ac = len(mission.assigned_aircraft)

    # Fuel
    fuel_used = FUEL_PER_SORTIE * n_ac
    state.resources.fuel = max(0, state.resources.fuel - fuel_used)

    # Weapons — expend fraction of what assigned aircraft carry
    fraction = roll_weapons_expenditure(weapons_roll)
    weapons_expended: dict[str, int] = {}
    for ac_id in mission.assigned_aircraft:
        ac = _find_aircraft(state, ac_id)
        # Count how many of each weapon type this aircraft carries
        payload_counts: dict[str, int] = {}
        for weapon in ac.current_payload:
            payload_counts[weapon] = payload_counts.get(weapon, 0) + 1
        # Expend fraction of each weapon type carried
        for weapon, count in payload_counts.items():
            if weapon in state.resources.weapons:
                expend = round(fraction * count)
                if expend > 0:
                    state.resources.weapons[weapon] = max(0, state.resources.weapons[weapon] - expend)
                    weapons_expended[weapon] = weapons_expended.get(weapon, 0) + expend

    weapons_str = ", ".join(f"{k}×{v}" for k, v in weapons_expended.items()) if weapons_expended else "none"
    _log(state, f"Mission {mission_id} resources consumed: fuel {fuel_used}L, weapons: {weapons_str}")
    return state


def advance_time(state: BaseState, hours: int) -> BaseState:
    """
    Advance the simulation clock by the given number of hours.
    Auto-completes maintenance when ETA reaches 0.
    Auto-generates a new ATO when the day rolls over.
    Handles campaign arc escalation, missed departure scoring, fail states.
    """
    if state.campaign_over:
        return state

    for _ in range(hours):
        if state.campaign_over:
            break

        prev_hour = state.current_hour
        state.current_hour += 1

        if state.current_hour >= 24:
            state.current_hour = 0
            state.current_day += 1

            # Force-return any aircraft still on_mission before wiping the ATO
            # (covers return_hour=24 missions and any that were missed)
            for mission in state.ato.missions:
                if mission.outcome is None:
                    # QRA is standby — aircraft don't actually fly for 23h
                    if mission.type == "QRA":
                        flight_hours = 1
                    else:
                        duration = mission.return_hour - mission.departure_hour
                        if duration <= 0:
                            duration += 24
                        flight_hours = max(1, duration)
                    for ac_id in list(mission.assigned_aircraft):
                        ac = _find_aircraft_safe(state, ac_id)
                        if ac and ac.status == "on_mission":
                            return_from_mission(state, ac_id, flight_hours=flight_hours)

            # Campaign arc — auto phase escalation
            new_phase = None
            if state.current_day == 2 and state.ato.phase == "Fred":
                new_phase = "Kris"
                _log(state, "CAMPAIGN EVENT: Intelligence confirms threat escalation. Phase: Fred → Kris.")
            elif state.current_day == 3 and state.ato.phase == "Kris":
                new_phase = "Krig"
                _log(state, "CAMPAIGN EVENT: Hostilities confirmed. Phase: Kris → Krig.")

            if new_phase:
                state.ato.phase = new_phase

            # Daily readiness bonus
            operational = [ac for ac in state.aircraft if ac.status in ("green", "on_mission", "returning")]
            if len(operational) >= 6:
                _score(state, +15, "Daily readiness bonus", f"Day ended with {len(operational)} operational aircraft.", "luck")

            _log(state, f"--- New day: Day {state.current_day} ({state.ato.phase}) ---")
            generate_new_ato(state)

            # Check campaign end on Day 8
            _check_fail_states(state)
            if state.campaign_over:
                break

        # Score missed departures — missions whose departure_hour just passed with no aircraft
        for mission in state.ato.missions:
            if mission.departure_hour == state.current_hour and not mission.assigned_aircraft:
                # Count how many green aircraft were available and idle
                idle_green = [ac for ac in state.aircraft if ac.status == "green"]
                if idle_green:
                    idle_ids = ", ".join(ac.id for ac in idle_green[:3])
                    _score(
                        state, -80, f"Missed departure: {mission.id}",
                        f"Mission {mission.id} ({mission.type}) departed unassigned. {len(idle_green)} green aircraft were available ({idle_ids}).",
                        "decision",
                    )
                else:
                    _log(state, f"Mission {mission.id} departed unassigned — no green aircraft available")

        # Decrement resupply ETA
        if state.resupply_eta is not None:
            state.resupply_eta -= 1
            if state.resupply_eta <= 0:
                state.resupply_eta = None
                state.resources.fuel = min(100_000, state.resources.fuel + 30_000)
                for k, add in [("Robot-1", 4), ("Bomb-2", 2), ("Robot-15", 1)]:
                    if k in state.resources.weapons:
                        state.resources.weapons[k] += add
                _log(state, "Resupply convoy arrived — +30,000L fuel, +Robot-1×4, +Bomb-2×2, +Robot-15×1")

        # Decrement maintenance ETAs
        for ac in state.aircraft:
            if ac.status == "red" and ac.maintenance_eta is not None:
                ac.maintenance_eta -= 1
                if ac.maintenance_eta <= 0:
                    complete_maintenance(state, ac.id)

        # Decrement return ETAs for aircraft transiting back to base
        for ac in state.aircraft:
            if ac.status == "returning" and ac.return_eta is not None:
                ac.return_eta -= 1
                if ac.return_eta <= 0:
                    return_from_mission(state, ac.id)

        # QRA scramble — fires each hour with phase-scaled probability (independent of random events)
        if state.ato.phase in ("Kris", "Krig"):
            scramble_chance = 0.05 if state.ato.phase == "Kris" else 0.10
            if random.random() < scramble_chance:
                qra_mission = next((m for m in state.ato.missions if m.type == "QRA"), None)
                manned = qra_mission and len(qra_mission.assigned_aircraft) >= 2
                if manned:
                    ac_str = ", ".join(qra_mission.assigned_aircraft)
                    _log(state, f"⚠ SCRAMBLE: Unidentified contacts. QRA ({ac_str}) launched — intercept successful.")
                    _score(state, +25, "QRA scramble — intercept", f"{ac_str} responded to scramble. Airspace defended.", "luck")
                else:
                    _log(state, "⚠ SCRAMBLE: Unidentified contacts. QRA UNMANNED — airspace undefended!")
                    _score(state, -60, "QRA unmanned during scramble", "Scramble fired but no aircraft assigned to QRA. Undefended airspace.", "decision")

        # Auto-return: aircraft whose mission return_hour has been reached
        # (Order: auto-return BEFORE auto-dispatch so same-hour handoffs work correctly)
        for mission in state.ato.missions:
            if mission.return_hour == state.current_hour and mission.outcome is None:
                # QRA is standby — aircraft don't actually fly for 23h
                if mission.type == "QRA":
                    flight_hours = 1
                else:
                    duration = mission.return_hour - mission.departure_hour
                    if duration <= 0:
                        duration += 24  # overnight mission
                    flight_hours = max(1, duration)
                for ac_id in list(mission.assigned_aircraft):
                    ac = _find_aircraft_safe(state, ac_id)
                    if ac and ac.status == "on_mission":
                        return_from_mission(state, ac_id, flight_hours=flight_hours)

        # Auto-dispatch: green aircraft assigned to missions departing this hour
        for mission in state.ato.missions:
            if mission.departure_hour == state.current_hour and mission.outcome is None:
                for ac_id in list(mission.assigned_aircraft):
                    ac = _find_aircraft_safe(state, ac_id)
                    if ac and ac.status == "green":
                        ac.status = "on_mission"
                        ac.location = "on_mission"
                        _log(state, f"{ac_id} auto-dispatched on {mission.id} ({mission.type}) at {state.current_hour:02d}:00")

        _check_fail_states(state)

    _log(state, f"Time advanced — now Day {state.current_day} {state.current_hour:02d}:00")
    return state


# ---------------------------------------------------------------------------
# ATO generation
# ---------------------------------------------------------------------------
_MISSION_POOL = [
    {
        "type": "DCA",
        "config": "DCA/CAP",
        "required": 2,
        "duration": 3,
        "descriptions": [
            "Combat Air Patrol — northern sector",
            "Air Defence — eastern approach",
            "Combat Air Patrol — coastal sector",
        ],
        "weight": {"Fred": 2, "Kris": 3, "Krig": 4},
    },
    {
        "type": "RECCE",
        "config": "RECCE",
        "required": 1,
        "duration": 2,
        "descriptions": [
            "Photo reconnaissance — bridge complex",
            "Intelligence gathering — supply depot",
            "Reconnaissance — enemy troop movement",
        ],
        "weight": {"Fred": 3, "Kris": 2, "Krig": 1},
    },
    {
        "type": "AI/ST",
        "config": "AI/ST",
        "required": 2,
        "duration": 2,
        "descriptions": [
            "Air Interdiction — supply route strike",
            "Strike mission — logistics hub",
            "Air Interdiction — fuel storage facility",
        ],
        "weight": {"Fred": 1, "Kris": 2, "Krig": 3},
    },
]


def generate_new_ato(state: BaseState) -> BaseState:
    """
    Generate a fresh ATO for the current day.
    QRA standby is always included in Kris/Krig phases.
    3–5 additional missions are drawn from a phase-weighted pool,
    with departure times spread across the remaining hours of the day.
    """
    phase = state.ato.phase
    missions: list[Mission] = []

    # QRA is always present in Kris/Krig — standby all day
    if phase in ("Kris", "Krig"):
        missions.append(Mission(
            id="M01",
            type="QRA",
            required_aircraft=2,
            required_config="DCA/CAP",
            departure_hour=0,
            return_hour=23,
            description="Quick Reaction Alert — 24h standby, must be manned at all times",
        ))

    weights = [p["weight"].get(phase, 1) for p in _MISSION_POOL]
    n_extra = random.randint(3, 5)

    # First departure 2h from now (or 06:00 if called at midnight)
    slot_hour = max((state.current_hour + 2) % 24, 2)

    for _ in range(n_extra):
        if slot_hour > 22:
            break
        pool_entry = random.choices(_MISSION_POOL, weights=weights, k=1)[0]
        dep = slot_hour
        ret = min(dep + pool_entry["duration"], 24)
        slot_hour = dep + max(pool_entry["duration"], 3)

        missions.append(Mission(
            id=f"M{len(missions) + 1:02d}",
            type=pool_entry["type"],
            required_aircraft=pool_entry["required"],
            required_config=pool_entry["config"],
            departure_hour=dep,
            return_hour=ret,
            description=random.choice(pool_entry["descriptions"]),
        ))

    state.ato.missions = missions
    state.ato.day = state.current_day
    _log(state, f"New ATO generated for Day {state.current_day} ({phase}) — {len(missions)} missions")
    return state


def request_resupply(state: BaseState) -> BaseState:
    """Request a resupply convoy. Arrives in 8h with +30kL fuel and weapons."""
    if state.resupply_eta is not None:
        raise ValueError(f"Resupply already en route — ETA {state.resupply_eta}h")
    state.resupply_eta = 8
    _log(state, "Resupply convoy dispatched — ETA 8h (+30,000L fuel, +Robot-1×4, +Bomb-2×2, +Robot-15×1)")
    return state


def apply_exchange_unit(state: BaseState, aircraft_id: str, ue_type: str) -> BaseState:
    """Apply an Exchange Unit to reduce an aircraft's maintenance ETA by 4h."""
    ac = _find_aircraft(state, aircraft_id)
    if ac.status != "red":
        raise ValueError(f"Cannot apply UE to {aircraft_id}: status is '{ac.status}' (must be in maintenance)")
    if ac.maintenance_eta is None or ac.maintenance_eta <= 1:
        raise ValueError(f"Cannot apply UE to {aircraft_id}: maintenance ETA too low ({ac.maintenance_eta}h)")
    available = state.resources.exchange_units.get(ue_type, 0)
    if available <= 0:
        raise ValueError(f"No {ue_type} exchange units available")
    state.resources.exchange_units[ue_type] = available - 1
    old_eta = ac.maintenance_eta
    ac.maintenance_eta = max(1, ac.maintenance_eta - 4)
    _log(state, f"Applied {ue_type} UE to {aircraft_id} — maintenance ETA {old_eta}h → {ac.maintenance_eta}h")
    return state


def recall_aircraft(state: BaseState, aircraft_id: str) -> BaseState:
    """
    Order an airborne aircraft to return to base early (RTB).
    Sets status to 'returning' with a 1–2h transit ETA.
    Marks the current mission as 'aborted' and scores a decision penalty.
    The aircraft still undergoes post-mission check on landing.
    The aircraft lands automatically when advance_time decrements the ETA to 0.
    """
    ac = _find_aircraft(state, aircraft_id)
    if ac.status != "on_mission":
        raise ValueError(f"Cannot recall {aircraft_id}: status is '{ac.status}' (must be on_mission)")
    ac.status = "returning"
    ac.return_eta = random.randint(1, 2)

    # Mark mission aborted and score the penalty
    for mission in state.ato.missions:
        if aircraft_id in mission.assigned_aircraft:
            mission.outcome = "aborted"
            _score(
                state, -25, f"RTB order — sortie aborted",
                f"{aircraft_id} recalled from {mission.type} mission mid-sortie. Effectiveness lost.",
                "decision",
            )
            break

    _log(state, f"{aircraft_id} RTB ordered — returning in {ac.return_eta}h. Post-mission check will apply on landing.")
    return state


def set_phase(state: BaseState, phase: str) -> BaseState:
    """Change operational phase and regenerate the ATO with new phase-weighted missions."""
    if phase not in ("Fred", "Kris", "Krig"):
        raise ValueError(f"Invalid phase '{phase}' — must be Fred, Kris, or Krig")
    old_phase = state.ato.phase
    state.ato.phase = phase
    _log(state, f"Phase changed: {old_phase} → {phase}")
    generate_new_ato(state)
    return state


def return_from_mission(
    state: BaseState,
    aircraft_id: str,
    flight_hours: int = 2,
    do_post_mission_roll: bool = True,
) -> BaseState:
    """
    Return an aircraft from a mission.
    Decrements remaining_life, rolls mission outcome, optionally rolls post-mission check.
    If remaining_life reaches 0, the aircraft is written off permanently.
    """
    ac = _find_aircraft(state, aircraft_id)
    if ac.status not in ("on_mission", "returning"):
        raise ValueError(f"Cannot return {aircraft_id}: status is '{ac.status}' (must be on_mission or returning)")

    ac.status = "green"
    ac.location = "flight_line"
    ac.return_eta = None
    ac.remaining_life = max(0, ac.remaining_life - flight_hours)
    ac.total_flight_hours += flight_hours

    # Consume fuel for this sortie
    state.resources.fuel = max(0, state.resources.fuel - FUEL_PER_SORTIE)

    # Find the mission this aircraft was on and resolve the sortie outcome
    mission_for_outcome = None
    for mission in state.ato.missions:
        if aircraft_id in mission.assigned_aircraft:
            mission_for_outcome = mission
            break

    _log(state, f"{aircraft_id} returned from mission ({flight_hours}h) — life remaining: {ac.remaining_life}h | fuel -{FUEL_PER_SORTIE}L → {state.resources.fuel:,}L")
    # No points just for returning — success/failure roll below is what matters
    state.missions_total += 1

    # Resolve mission outcome — skip if sortie was aborted via RTB
    if mission_for_outcome:
        if mission_for_outcome.outcome == "aborted":
            _log(state, f"{aircraft_id} returned from aborted {mission_for_outcome.type} sortie — no effectiveness credited")
        else:
            phase = state.ato.phase
            prob = _compute_success_prob(ac, mission_for_outcome, phase)
            if random.random() < prob:
                _log(state, f"{aircraft_id} {mission_for_outcome.type} sortie SUCCESSFUL ({int(prob*100)}% chance)")
                _score(state, +10, "Sortie success", f"{aircraft_id} succeeded on {mission_for_outcome.type} sortie.", "luck")
                state.missions_completed += 1
                mission_for_outcome.outcome = "success"
            else:
                _log(state, f"{aircraft_id} {mission_for_outcome.type} sortie FAILED ({int((1-prob)*100)}% failure chance) — effectiveness degraded")
                _score(state, -20, "Sortie failed", f"{aircraft_id} failed {mission_for_outcome.type} sortie.", "luck")
                mission_for_outcome.outcome = "failure"
        mission_for_outcome.assigned_aircraft.remove(aircraft_id)
    else:
        # Remove from any mission (fallback)
        for mission in state.ato.missions:
            if aircraft_id in mission.assigned_aircraft:
                mission.assigned_aircraft.remove(aircraft_id)

    # Check if aircraft is written off
    if ac.remaining_life <= 0:
        _write_off_aircraft(state, aircraft_id)
        _check_fail_states(state)
        return state

    if do_post_mission_roll:
        passed, fault_roll = roll_post_mission()
        if not passed:
            _log(state, f"{aircraft_id} post-mission check FAILED")
            _score(state, -10, "Post-mission fault", f"{aircraft_id} developed fault after landing — random mechanical failure.", "luck")
            trigger_fault(state, aircraft_id, fault_roll)
        else:
            _log(state, f"{aircraft_id} post-mission check OK")

    # Warn if remaining life is critically low
    if ac.remaining_life <= 20 and ac.status == "green":
        _log(state, f"WARNING: {aircraft_id} has only {ac.remaining_life}h remaining life — written off if flown again without heavy service!")

    return state


# ---------------------------------------------------------------------------
# Random event injection
# ---------------------------------------------------------------------------
def generate_random_event(state: BaseState) -> BaseState:
    """Inject a random event into the current state."""
    green_aircraft = [ac for ac in state.aircraft if ac.status == "green"]

    # Build phase-weighted event pool
    event_types = ["bit_fault", "new_mission"]
    if state.ato.phase in ("Kris", "Krig"):
        event_types += ["qra_scramble", "qra_scramble"]  # 2× weight in wartime
    if not green_aircraft:
        event_types = [e for e in event_types if e != "bit_fault"]
    if not event_types:
        _log(state, "Random event: no eligible events available")
        return state

    event_type = random.choice(event_types)

    if event_type == "bit_fault":
        ac = random.choice(green_aircraft)
        _log(state, f"RANDOM EVENT: BIT fault triggered on {ac.id}")
        trigger_fault(state, ac.id)
        _score(state, -10, "Random BIT fault", f"{ac.id} developed unexpected BIT fault — random mechanical failure.", "luck")

    elif event_type == "new_mission":
        # Don't add new missions if too late in the day to react (< 3h until midnight)
        if state.current_hour >= 20:
            _log(state, "Random event: too late in day to add new mission — skipped")
            return state
        dep = min(state.current_hour + 2, 20)
        ret = min(dep + 3, 23)
        mission_type = random.choice(["DCA", "RECCE"])
        config = "DCA/CAP" if mission_type == "DCA" else "RECCE"
        new_mission = Mission(
            id=f"M{len(state.ato.missions) + 1:02d}",
            type=mission_type,
            required_aircraft=random.choice([1, 2]),
            required_config=config,
            departure_hour=dep,
            return_hour=ret,
            description="Unplanned tasking from higher command",
        )
        state.ato.missions.append(new_mission)
        _log(state, f"RANDOM EVENT: New mission {new_mission.id} ({new_mission.type}) — departs {dep:02d}:00, returns {ret:02d}:00")

    elif event_type == "qra_scramble":
        qra_mission = next((m for m in state.ato.missions if m.type == "QRA"), None)
        manned = qra_mission and len(qra_mission.assigned_aircraft) >= 2
        if manned:
            ac_str = ", ".join(qra_mission.assigned_aircraft)
            _log(state, f"⚠ SCRAMBLE: Unidentified contacts detected. QRA ({ac_str}) launched — intercept successful.")
            _score(state, +25, "QRA scramble — intercept", f"{ac_str} responded to scramble alert. Airspace defended.", "luck")
        else:
            _log(state, "⚠ SCRAMBLE: Unidentified contacts detected. QRA UNMANNED — airspace undefended!")
            _score(state, -60, "QRA unmanned during scramble", "Scramble alert fired but no aircraft assigned to QRA. Undefended airspace.", "decision")

    return state


# ---------------------------------------------------------------------------
# State serialization
# ---------------------------------------------------------------------------
def serialize_state(state: BaseState) -> str:
    """
    Convert BaseState to a structured text block for LLM injection.
    Inject into system prompt as {state_json}.
    """
    lines: list[str] = []
    lines.append(f"=== BASE STATE — Day {state.current_day} ({state.ato.phase}) — Hour {state.current_hour:02d}:00 ===")
    lines.append("")

    # Fleet status
    lines.append("FLEET STATUS:")
    for ac in state.aircraft:
        status_str = ac.status.upper().ljust(10)
        life_str = f"Life: {ac.remaining_life:3d}h"
        config_str = f"Config: {ac.configuration}"
        loc_str = f"Loc: {ac.location}"
        fault_str = f" | FAULT: {ac.fault} (ETA: {ac.maintenance_eta}h)" if ac.fault else ""
        lines.append(f"  {ac.id} | {ac.type} | {status_str} | {life_str} | {config_str} | {loc_str}{fault_str}")
    lines.append("")

    # ATO missions
    lines.append(f"ATO — Day {state.ato.day} ({state.ato.phase}):")
    for m in state.ato.missions:
        assigned_str = ", ".join(m.assigned_aircraft) if m.assigned_aircraft else "UNASSIGNED"
        slots_str = f"{len(m.assigned_aircraft)}/{m.required_aircraft}"
        lines.append(
            f"  {m.id} | {m.type} | Dep: {m.departure_hour:02d}:00 Ret: {m.return_hour:02d}:00"
            f" | Aircraft: {assigned_str} ({slots_str}) | {m.description}"
        )
    lines.append("")

    # Resources
    r = state.resources
    weapons_str = " | ".join(f"{k}: {v}" for k, v in r.weapons.items())
    ue_str = " | ".join(f"{k}: {v}" for k, v in r.exchange_units.items())
    personnel_str = " | ".join(f"{k}: {v}" for k, v in r.personnel.items())
    lines.append("RESOURCES:")
    lines.append(f"  Fuel: {r.fuel:,}L")
    lines.append(f"  Weapons:        {weapons_str}")
    lines.append(f"  Exchange Units: {ue_str}")
    lines.append(f"  Spare Parts:    {r.spare_parts}")
    lines.append(f"  Personnel:      {personnel_str}")
    lines.append("")

    # Maintenance slots
    lines.append("MAINTENANCE SLOTS:")
    for slot in state.maintenance_slots:
        occupants_str = ", ".join(slot.current_occupants) if slot.current_occupants else "empty"
        lines.append(f"  {slot.id} (cap {slot.capacity}): [{occupants_str}]")
    lines.append("")

    # Recent events
    lines.append("RECENT EVENTS (last 15):")
    for entry in state.event_log[-15:]:
        lines.append(f"  {entry}")

    return "\n".join(lines)


def serialize_state_json(state: BaseState) -> dict:
    """Return state as a plain dict (JSON-serializable) for Dev 3."""
    def ac_to_dict(ac: Aircraft) -> dict:
        return {
            "id": ac.id,
            "type": ac.type,
            "status": ac.status,
            "remaining_life": ac.remaining_life,
            "total_flight_hours": ac.total_flight_hours,
            "configuration": ac.configuration,
            "current_payload": ac.current_payload,
            "location": ac.location,
            "maintenance_eta": ac.maintenance_eta,
            "fault": ac.fault,
            "return_eta": ac.return_eta,
            "pending_config": ac.pending_config,
        }

    def mission_to_dict(m: Mission) -> dict:
        return {
            "id": m.id,
            "type": m.type,
            "required_aircraft": m.required_aircraft,
            "required_config": m.required_config,
            "departure_hour": m.departure_hour,
            "return_hour": m.return_hour,
            "assigned_aircraft": m.assigned_aircraft,
            "description": m.description,
            "outcome": m.outcome,
        }

    def score_event_to_dict(e: ScoreEvent) -> dict:
        return {
            "day": e.day,
            "hour": e.hour,
            "delta": e.delta,
            "reason": e.reason,
            "detail": e.detail,
            "category": e.category,
        }

    r = state.resources
    return {
        "current_hour": state.current_hour,
        "current_day": state.current_day,
        "phase": state.ato.phase,
        "aircraft": [ac_to_dict(ac) for ac in state.aircraft],
        "ato": {
            "day": state.ato.day,
            "phase": state.ato.phase,
            "missions": [mission_to_dict(m) for m in state.ato.missions],
        },
        "resources": {
            "fuel": r.fuel,
            "weapons": r.weapons,
            "exchange_units": r.exchange_units,
            "spare_parts": r.spare_parts,
            "personnel": r.personnel,
        },
        "maintenance_slots": [
            {"id": s.id, "type": s.type, "capacity": s.capacity, "current_occupants": s.current_occupants}
            for s in state.maintenance_slots
        ],
        "event_log": state.event_log[-20:],
        # Campaign / scoring
        "campaign_score": state.campaign_score,
        "score_log": [score_event_to_dict(e) for e in state.score_log[-15:]],
        "campaign_over": state.campaign_over,
        "campaign_result": state.campaign_result,
        "campaign_over_reason": state.campaign_over_reason,
        "aircraft_written_off": state.aircraft_written_off,
        "missions_completed": state.missions_completed,
        "missions_total": state.missions_total,
        "campaign_grade": _grade(state.campaign_score),
        "resupply_eta": state.resupply_eta,
    }


# ---------------------------------------------------------------------------
# Smoke test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 70)
    print("SMOKE TEST — Game State Engine")
    print("=" * 70)

    s = reset_state()
    print("\n--- INITIAL STATE ---")
    print(serialize_state(s))

    print("\n--- BIT CHECK on GE05 (forced fail, fault type 3 = complex LRU) ---")
    trigger_fault(s, "GE05", fault_roll=3)
    print(serialize_state(s))

    print("\n--- ASSIGN GE01 + GF01 to M01 ---")
    assign_aircraft(s, "M01", ["GE01", "GF01"])
    print(serialize_state(s))

    print("\n--- ADVANCE TIME 2 hours ---")
    advance_time(s, 2)
    print(serialize_state(s))

    print("\n--- GF02 RETURNS FROM MISSION (post-mission roll enabled) ---")
    return_from_mission(s, "GF02", flight_hours=3, do_post_mission_roll=True)
    print(serialize_state(s))

    print("\n--- JSON SNAPSHOT (first 500 chars) ---")
    j = serialize_state_json(s)
    print(json.dumps(j, indent=2)[:500] + "...")
