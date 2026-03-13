"""
FastAPI backend — SAAB Base Commander
Replaces Gradio with a REST API consumed by the React frontend.
"""
from __future__ import annotations

import copy
import os
import pathlib
import sys

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

# Ensure the project directory is on sys.path
sys.path.insert(0, str(pathlib.Path(__file__).parent))

from engine import (
    get_state, reset_state, serialize_state_json,
    trigger_fault, complete_maintenance, consume_resources,
    advance_time, return_from_mission, assign_aircraft,
    generate_random_event,
)
from llm_integration import LLMAssistant

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
    hours: int = 1

class AssignAircraftRequest(BaseModel):
    mission_id: str
    aircraft_ids: list[str]

class AircraftIdRequest(BaseModel):
    aircraft_id: str


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
    return serialize_state_json(get_state())

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

@app.post("/api/action/random-event")
def api_random_event():
    generate_random_event(get_state())
    return serialize_state_json(get_state())


# ---------------------------------------------------------------------------
# Demo scenarios
# ---------------------------------------------------------------------------

@app.post("/api/scenario/1")
def api_scenario1():
    """Scenario 1: Assign aircraft to active ATO missions."""
    s = get_state()
    try:
        dca_ac = [
            ac.id for ac in s.aircraft
            if ac.status == "green" and ac.configuration == "DCA/CAP"
        ]
        recce_ac = [
            ac.id for ac in s.aircraft
            if ac.status == "green" and ac.configuration == "RECCE"
        ]
        aist_ac = [
            ac.id for ac in s.aircraft
            if ac.status == "green" and ac.configuration == "AI/ST"
        ]
        if len(dca_ac) >= 2:
            assign_aircraft(s, "M01", dca_ac[:2])
        if len(recce_ac) >= 1:
            assign_aircraft(s, "M04", recce_ac[:1])
        if len(aist_ac) >= 2:
            assign_aircraft(s, "M05", aist_ac[:2])
        elif len(aist_ac) == 1:
            assign_aircraft(s, "M05", aist_ac[:1])
    except ValueError:
        pass
    return serialize_state_json(s)

@app.post("/api/scenario/2")
def api_scenario2():
    """Scenario 2: Fault cascade — GE05 BIT fail + returning aircraft post-mission fault."""
    s = get_state()
    trigger_fault(s, "GE05")
    returning_ac = next(
        (ac for ac in s.aircraft if ac.status == "on_mission" and ac.id != "GE05"),
        None,
    )
    if returning_ac:
        return_from_mission(s, returning_ac.id)
    return serialize_state_json(s)

@app.post("/api/scenario/3")
def api_scenario3():
    """Scenario 3: Advance time 6h, consume resources, show pressure."""
    s = get_state()
    advance_time(s, 6)
    for mission in s.ato.missions:
        if mission.assigned_aircraft:
            try:
                consume_resources(s, mission.id)
            except Exception:
                pass
    return serialize_state_json(s)


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
