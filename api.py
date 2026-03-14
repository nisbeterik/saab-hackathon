"""
FastAPI backend — SAAB Base Commander
Replaces Gradio with a REST API consumed by the React frontend.
"""
from __future__ import annotations

import os
import pathlib
import sys

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

# Ensure the project directory is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from engine import (
    get_state, reset_state, serialize_state_json,
    trigger_fault, complete_maintenance,
    advance_time, return_from_mission, assign_aircraft,
    generate_random_event, generate_new_ato, recall_aircraft, set_phase,
)
from llm_integration import LLMAssistant
from demo_scenarios import DEMO_SCRIPT

app = FastAPI(title="SAAB Base Commander API")

# CORS for Vite dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LLM Assistant singleton
try:
    assistant = LLMAssistant()
except ValueError:
    assistant = None


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    message: str

class AdvanceTimeRequest(BaseModel):
    hours: int = Field(1, gt=0)

class AssignAircraftRequest(BaseModel):
    mission_id: str
    aircraft_ids: list[str] = Field(..., min_length=1)

class AircraftIdRequest(BaseModel):
    aircraft_id: str

class SetPhaseRequest(BaseModel):
    phase: str

class DemoRunRequest(BaseModel):
    label: str


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------

@app.get("/api/state")
def api_get_state():
    return serialize_state_json(get_state())


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/api/chat")
def api_chat(body: ChatRequest):
    if not assistant:
        return {"reply": "LLM unavailable: No API key configured. Set OPENROUTER_API_KEY in .env"}
    reply = assistant.chat(body.message, get_state())
    return {"reply": reply}

@app.post("/api/chat/clear")
def api_chat_clear():
    if assistant:
        assistant.clear_history()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

@app.post("/api/action/reset")
def api_reset():
    reset_state()
    if assistant:
        assistant.clear_history()
    result = serialize_state_json(get_state())
    result["chat_cleared"] = True
    return result

@app.post("/api/action/advance-time")
def api_advance_time(body: AdvanceTimeRequest):
    advance_time(get_state(), body.hours)
    return serialize_state_json(get_state())

@app.post("/api/action/assign-aircraft")
def api_assign_aircraft(body: AssignAircraftRequest):
    try:
        assign_aircraft(get_state(), body.mission_id, body.aircraft_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())

@app.post("/api/action/trigger-fault")
def api_trigger_fault(body: AircraftIdRequest):
    try:
        trigger_fault(get_state(), body.aircraft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())

@app.post("/api/action/complete-maintenance")
def api_complete_maintenance(body: AircraftIdRequest):
    try:
        complete_maintenance(get_state(), body.aircraft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())

@app.post("/api/action/return-from-mission")
def api_return_from_mission(body: AircraftIdRequest):
    try:
        return_from_mission(get_state(), body.aircraft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())

@app.post("/api/action/random-event")
def api_random_event():
    generate_random_event(get_state())
    return serialize_state_json(get_state())

@app.post("/api/action/new-ato")
def api_new_ato():
    generate_new_ato(get_state())
    return serialize_state_json(get_state())

@app.post("/api/action/recall-aircraft")
def api_recall_aircraft(body: AircraftIdRequest):
    try:
        recall_aircraft(get_state(), body.aircraft_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())

@app.post("/api/action/set-phase")
def api_set_phase(body: SetPhaseRequest):
    try:
        set_phase(get_state(), body.phase)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return serialize_state_json(get_state())


# ---------------------------------------------------------------------------
# Demo script endpoints
# ---------------------------------------------------------------------------

@app.get("/api/demo/scenarios")
def api_demo_scenarios():
    """Return the full demo script so the frontend can render a scenario picker."""
    return [
        {"label": s.label, "question": s.question, "has_event": s.event_trigger is not None}
        for s in DEMO_SCRIPT
    ]


@app.post("/api/demo/run")
def api_demo_run(body: DemoRunRequest):
    """
    Execute a demo scenario step:
      1. Apply the event_trigger state mutation (if any).
      2. Return the updated state + the question to pre-fill in the chat input.
    """
    step = next((s for s in DEMO_SCRIPT if s.label == body.label), None)
    if not step:
        raise HTTPException(status_code=404, detail=f"Scenario not found: {body.label}")

    s = get_state()

    if step.event_trigger == "new_ato":
        generate_new_ato(s)

    elif step.event_trigger == "bit_fail_ge05":
        ge05 = next((a for a in s.aircraft if a.id == "GE05"), None)
        if ge05 and ge05.status == "green":
            trigger_fault(s, "GE05", fault_roll=3)  # Complex LRU, 6h repair

    elif step.event_trigger == "return_damaged_ge07":
        ge07 = next((a for a in s.aircraft if a.id == "GE07"), None)
        if ge07 and ge07.status != "red":
            if ge07.status != "on_mission":
                ge07.status = "on_mission"
                ge07.location = "on_mission"
            return_from_mission(s, "GE07", do_post_mission_roll=False)
            trigger_fault(s, "GE07", fault_roll=4)  # Direct repair (Kompositrep), 16h

    return {"state": serialize_state_json(s), "question": step.question}


# ---------------------------------------------------------------------------
# Serve frontend static files (production build)
# ---------------------------------------------------------------------------

STATIC_DIR = pathlib.Path(__file__).parent / "frontend" / "dist"

if STATIC_DIR.exists():
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/", include_in_schema=False)
    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_frontend(full_path: str = ""):
        # Let API routes take priority — this only catches non-/api paths
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404)
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        raise HTTPException(status_code=404, detail="Frontend not built. Run: cd frontend && npm run build")
