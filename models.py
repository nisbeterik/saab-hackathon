"""
Shared data models — owned by Dev 1.
Dataclasses match the project brief exactly.
Dev 1 adds state mutation methods (assign_aircraft, trigger_fault, etc.) to this file.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Aircraft:
    id: str
    type: str                       # "GripenE", "GripenF", "GlobalEye"
    status: str                     # "green", "red", "grey", "on_mission"
    remaining_life: int             # flight hours until heavy service
    total_flight_hours: int
    configuration: str              # "DCA/CAP", "RECCE", "AI/ST", "AEW&C"
    current_payload: list = field(default_factory=list)
    location: str = "flight_line"   # "flight_line", "service_bay", "maint_workshop", "on_mission"
    maintenance_eta: Optional[int] = None
    fault: Optional[str] = None


@dataclass
class ResourceInventory:
    fuel: int = 50000
    weapons: dict = field(default_factory=dict)
    exchange_units: dict = field(default_factory=dict)
    spare_parts: int = 20
    personnel: dict = field(default_factory=dict)
    tools: dict = field(default_factory=dict)


@dataclass
class Mission:
    id: str
    type: str                       # "DCA", "RECCE", "AI/ST", "QRA", "AEW"
    required_aircraft: int
    required_config: str
    departure_hour: int
    return_hour: int
    assigned_aircraft: list = field(default_factory=list)


@dataclass
class ATO:
    day: int
    phase: str                      # "Fred", "Kris", "Krig"
    missions: list = field(default_factory=list)


@dataclass
class MaintenanceSlot:
    id: str
    type: str                       # "service_bay", "minor_workshop", "major_workshop"
    capacity: int
    current_occupants: list = field(default_factory=list)


@dataclass
class BaseState:
    current_hour: int = 6
    current_day: int = 2
    aircraft: list = field(default_factory=list)
    resources: ResourceInventory = field(default_factory=ResourceInventory)
    ato: ATO = field(default_factory=lambda: ATO(day=2, phase="Kris", missions=[]))
    maintenance_slots: list = field(default_factory=list)
    event_log: list = field(default_factory=list)


def create_demo_state() -> BaseState:
    """Realistic Day 2 Kris-phase starting state for demo and testing."""
    aircraft = [
        Aircraft("GE01", "GripenE", "green",      142, 358, "DCA/CAP",  ["Robot1", "Robot1"],        "flight_line"),
        Aircraft("GE02", "GripenE", "green",       88, 412, "DCA/CAP",  ["Robot1", "AimSight"],      "flight_line"),
        Aircraft("GE03", "GripenE", "red",         61, 439, "RECCE",    ["RecPod"],                  "service_bay",    maintenance_eta=4, fault="Radar LRU fault — AU Steg 2/3 repair"),
        Aircraft("GE04", "GripenE", "green",      175, 325, "DCA/CAP",  ["Robot1", "Robot1"],        "flight_line"),
        Aircraft("GE05", "GripenE", "green",       34, 466, "AI/ST",    ["Bomb2", "Bomb2"],          "flight_line"),
        Aircraft("GE06", "GripenE", "green",      110, 390, "RECCE",    ["RecPod", "ExtraTank"],     "flight_line"),
        Aircraft("GE07", "GripenF", "on_mission",  95, 505, "DCA/CAP",  ["Robot1", "Robot1"],        "on_mission"),
        Aircraft("GE08", "GripenF", "green",      158, 342, "AI/ST",    ["Bomb2", "Bomb2"],          "flight_line"),
        Aircraft("GE09", "GripenF", "grey",        72, 428, "DCA/CAP",  [],                          "maint_workshop", maintenance_eta=8, fault="Cannibalized — Radar unit removed for GE03"),
        Aircraft("LO21", "GlobalEye", "green",    320, 180, "AEW&C",    [],                          "flight_line"),
    ]

    resources = ResourceInventory(
        fuel=38000,
        weapons={"Robot1": 14, "AimSight": 4, "Bomb2": 10, "Maverick": 6},
        exchange_units={"Radar": 1, "SignalProcessor": 2, "EjectionSeat": 1, "Hydraulics": 2},
        spare_parts=15,
        personnel={"klargoring_crew": 5, "maintenance_tech": 4, "pilots": 9, "logistics": 3},
        tools={"test_equipment": 3, "heavy_lift": 1},
    )

    missions = [
        Mission("M01", "DCA",   2, "DCA/CAP", departure_hour=8,  return_hour=12, assigned_aircraft=["GE07"]),
        Mission("M02", "RECCE", 1, "RECCE",   departure_hour=10, return_hour=14),
        Mission("M03", "DCA",   2, "DCA/CAP", departure_hour=14, return_hour=18),
        Mission("M04", "AI/ST", 2, "AI/ST",   departure_hour=16, return_hour=20),
        Mission("M05", "QRA",   1, "DCA/CAP", departure_hour=0,  return_hour=24),
    ]

    maintenance_slots = [
        MaintenanceSlot("SB1", "service_bay",    capacity=2, current_occupants=["GE03"]),
        MaintenanceSlot("MW1", "maint_workshop", capacity=2, current_occupants=["GE09"]),
        MaintenanceSlot("MW2", "major_workshop", capacity=1, current_occupants=[]),
    ]

    event_log = [
        "Day 2 06:00 — Base operational. ATO received for Day 2 Kris phase.",
        "Day 2 06:30 — GE03 failed pre-flight BIT. Radar LRU fault. Repair started (est. 4h).",
        "Day 2 07:00 — GE09 cannibalized: Radar unit transferred to GE03 repair stock.",
        "Day 2 07:30 — GE07 launched on M01 DCA sortie.",
    ]

    return BaseState(
        current_hour=8,
        current_day=2,
        aircraft=aircraft,
        resources=resources,
        ato=ATO(day=2, phase="Kris", missions=missions),
        maintenance_slots=maintenance_slots,
        event_log=event_log,
    )
