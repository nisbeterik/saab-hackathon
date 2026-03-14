from __future__ import annotations
from dataclasses import dataclass, field


@dataclass
class Aircraft:
    id: str                        # e.g. "GE01", "GF02"
    type: str                      # "GripenE", "GripenF", "GlobalEye"
    status: str                    # "green", "red", "grey", "on_mission"
    remaining_life: int            # flight hours until heavy service (0-200)
    total_flight_hours: int        # total accumulated flight hours
    configuration: str             # "DCA/CAP", "RECCE", "AI/ST", "AEW&C"
    current_payload: list[str] = field(default_factory=list)
    location: str = "flight_line"  # "flight_line", "service_bay", "maint_workshop", "on_mission"
    maintenance_eta: int | None = None  # hours until maintenance complete
    fault: str | None = None            # current fault description if any
    return_eta: int | None = None       # hours until aircraft returns to base (when status="returning")


@dataclass
class ResourceInventory:
    fuel: int                      # liters available
    weapons: dict[str, int] = field(default_factory=dict)
    exchange_units: dict[str, int] = field(default_factory=dict)
    spare_parts: int = 0
    personnel: dict[str, int] = field(default_factory=dict)
    tools: dict[str, int] = field(default_factory=dict)


@dataclass
class Mission:
    id: str
    type: str                      # "DCA", "RECCE", "AI/ST", "QRA", "AEW"
    required_aircraft: int
    required_config: str
    departure_hour: int            # hour in 24h cycle
    return_hour: int
    assigned_aircraft: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ATO:
    day: int
    phase: str                     # "Fred", "Kris", "Krig"
    missions: list[Mission] = field(default_factory=list)


@dataclass
class MaintenanceSlot:
    id: str
    type: str                      # "service_bay", "minor_workshop", "major_workshop"
    capacity: int
    current_occupants: list[str] = field(default_factory=list)


@dataclass
class BaseState:
    current_hour: int              # 0-23
    current_day: int
    aircraft: list[Aircraft]
    resources: ResourceInventory
    ato: ATO
    maintenance_slots: list[MaintenanceSlot]
    event_log: list[str] = field(default_factory=list)
