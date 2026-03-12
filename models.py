# models.py — compatibility shim
# llm_integration.py imports from here; we re-export from the canonical modules.
from state import Aircraft, ResourceInventory, Mission, ATO, MaintenanceSlot, BaseState  # noqa: F401
from engine import (  # noqa: F401
    create_initial_state, get_state, reset_state,
    serialize_state, serialize_state_json,
)
