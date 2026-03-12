"""
Dev 2: Gradio UI — SAAB Base Commander
=======================================
Runs standalone (python app.py) with inline mock data.
Auto-integrates when teammates add:
  - state.py  (Dev 1: real game state engine)
  - llm.py    (Dev 3: OpenRouter/Gemini chat)
"""

import copy
import random
from datetime import datetime, timedelta

import gradio as gr
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Integration: try teammates' modules, fall back to inline stubs ─────────────

try:
    from state import (
        BaseState, Aircraft, ResourceInventory, Mission, ATO, MaintenanceSlot,
    )
    from engine import (
        create_initial_state,
        trigger_fault, complete_maintenance, consume_resources,
        advance_time, return_from_mission, assign_aircraft,
    )
    # Extra event helpers — stub locally if Dev 1 hasn't added them yet
    try:
        from state import trigger_resupply_delay, trigger_bredduppgift
    except ImportError:
        def trigger_resupply_delay(state):
            s = copy.deepcopy(state)
            weapon = random.choice(list(s.resources.weapons.keys()))
            reduction = random.randint(2, 4)
            s.resources.weapons[weapon] = max(0, s.resources.weapons[weapon] - reduction)
            s.event_log.append(f"[H{s.current_hour:02d}] RESUPPLY DELAY: {weapon} −{reduction} units")
            return s

        def trigger_bredduppgift(state):
            s = copy.deepcopy(state)
            new_id = f"M{len(s.ato.missions) + 1:02d}"
            dep = (s.current_hour + 2) % 24
            ret = (s.current_hour + 6) % 24
            mtype = random.choice(["DCA", "RECCE", "AI/ST", "QRA"])
            config_map = {"DCA": "DCA/CAP", "RECCE": "RECCE", "AI/ST": "AI/ST", "QRA": "DCA/CAP"}
            s.ato.missions.append(Mission(new_id, mtype, 2, config_map[mtype], dep, ret, []))
            s.event_log.append(f"[H{s.current_hour:02d}] BREDDUPPGIFT: {new_id} {mtype} H{dep:02d}–H{ret:02d}")
            return s

    try:
        from llm import chat as _llm_chat
        def chat(state, message, history):
            return _llm_chat(state, message, history)
    except ImportError:
        def chat(state, message, history):
            return (
                f"[LLM not connected — Dev 3's llm.py not found]\n\n"
                f"Your question: *'{message}'*\n\n"
                f"Fleet: {len(state.aircraft)} aircraft | "
                f"Day {state.current_day} H{state.current_hour:02d}:00 | "
                f"Phase: {state.ato.phase}"
            )

    USING_STUBS = False

except ImportError:
    # ── Inline dataclasses (mirrors PROJECT_BRIEF.md exactly) ────────────────
    from dataclasses import dataclass, field
    from typing import Optional

    @dataclass
    class Aircraft:
        id: str
        type: str
        status: str                      # "green", "red", "grey", "on_mission"
        remaining_life: int
        total_flight_hours: int
        configuration: str
        current_payload: list = field(default_factory=list)
        location: str = "flight_line"
        maintenance_eta: Optional[int] = None
        fault: Optional[str] = None

    @dataclass
    class ResourceInventory:
        fuel: int
        weapons: dict = field(default_factory=dict)
        exchange_units: dict = field(default_factory=dict)
        spare_parts: int = 0
        personnel: dict = field(default_factory=dict)
        tools: dict = field(default_factory=dict)

    @dataclass
    class Mission:
        id: str
        type: str
        required_aircraft: int
        required_config: str
        departure_hour: int
        return_hour: int
        assigned_aircraft: list = field(default_factory=list)

    @dataclass
    class ATO:
        day: int
        phase: str
        missions: list = field(default_factory=list)

    @dataclass
    class MaintenanceSlot:
        id: str
        type: str
        capacity: int
        current_occupants: list = field(default_factory=list)

    @dataclass
    class BaseState:
        current_hour: int
        current_day: int
        aircraft: list
        resources: ResourceInventory
        ato: ATO
        maintenance_slots: list
        event_log: list = field(default_factory=list)

    def create_initial_state() -> BaseState:
        aircraft = [
            Aircraft("GE01", "GripenE",   "green",      145, 855, "DCA/CAP", ["Robot-1", "Robot-5"],  "flight_line"),
            Aircraft("GE02", "GripenE",   "green",      112, 888, "DCA/CAP", ["Robot-1", "Robot-5"],  "flight_line"),
            Aircraft("GE03", "GripenE",   "red",         78, 922, "RECCE",   ["ReconPod"],             "service_bay",  6, "Radar fault (LRU, 6h)"),
            Aircraft("GE04", "GripenE",   "green",      167, 833, "AI/ST",   ["GBU-49", "DWS39"],      "flight_line"),
            Aircraft("GE05", "GripenE",   "on_mission",  95, 905, "DCA/CAP", ["Robot-1", "Robot-5"],  "on_mission"),
            Aircraft("GE06", "GripenE",   "green",       34, 966, "DCA/CAP", ["Robot-1"],              "flight_line"),
            Aircraft("GE07", "GripenF",   "grey",        22, 978, "DCA/CAP", [],                       "maint_workshop"),
            Aircraft("GE08", "GripenF",   "green",      155, 845, "AI/ST",   ["GBU-49", "DWS39"],      "flight_line"),
            Aircraft("GE09", "GripenF",   "on_mission",  88, 912, "RECCE",   ["ReconPod"],             "on_mission"),
            Aircraft("LO21", "GlobalEye", "green",      190, 310, "AEW&C",   [],                       "flight_line"),
        ]
        resources = ResourceInventory(
            fuel=18000,
            weapons={"Robot-1": 8, "Robot-5": 14, "GBU-49": 6, "DWS39": 4},
            exchange_units={"Radar": 1, "SignalProcessor": 2, "EjectionSeat": 1, "FCS": 2},
            spare_parts=23,
            personnel={"klargoring_crew": 4, "maintenance_tech": 3, "pilots": 8, "avionics_tech": 2},
            tools={"test_equipment": 2, "heavy_lift": 1, "diagnostic_kit": 3},
        )
        ato = ATO(day=2, phase="Kris", missions=[
            Mission("M01", "DCA",   2, "DCA/CAP", 6,  10, ["GE05"]),
            Mission("M02", "RECCE", 1, "RECCE",   8,  12, ["GE09"]),
            Mission("M03", "DCA",   2, "DCA/CAP", 14, 18, []),
            Mission("M04", "AEW",   1, "AEW&C",   12, 20, []),
            Mission("M05", "AI/ST", 2, "AI/ST",   16, 22, []),
        ])
        slots = [
            MaintenanceSlot("SB-01", "service_bay",    2, ["GE03"]),
            MaintenanceSlot("MW-01", "minor_workshop", 1, ["GE07"]),
            MaintenanceSlot("MW-02", "major_workshop", 1, []),
        ]
        return BaseState(
            current_hour=8,
            current_day=2,
            aircraft=aircraft,
            resources=resources,
            ato=ato,
            maintenance_slots=slots,
            event_log=[
                "[H06:00] M01 (DCA) departed — GE05",
                "[H08:00] M02 (RECCE) departed — GE09",
                "[H08:00] GE03 BIT failed — Radar fault, 6h repair started",
            ],
        )

    # ── Inline stub mutations ─────────────────────────────────────────────────
    _FAULTS = [
        "Radar fault (LRU, 6h)",
        "FCS anomaly (LRU, 2h)",
        "Hydraulic fault (direct, 4h)",
        "Ejection seat flag (workshop, 16h)",
        "Signal processor fault (LRU, 2h)",
    ]

    def trigger_fault(state, aircraft_id):
        s = copy.deepcopy(state)
        fault = random.choice(_FAULTS)
        for ac in s.aircraft:
            if ac.id == aircraft_id:
                ac.status = "red"
                ac.fault = fault
                ac.location = "service_bay"
                try:
                    ac.maintenance_eta = int(fault.split(", ")[1].split("h)")[0])
                except Exception:
                    ac.maintenance_eta = 4
        s.event_log.append(f"[H{s.current_hour:02d}] FAULT {aircraft_id}: {fault}")
        return s

    def complete_maintenance(state, aircraft_id):
        s = copy.deepcopy(state)
        for ac in s.aircraft:
            if ac.id == aircraft_id:
                ac.status = "green"
                ac.fault = None
                ac.location = "flight_line"
                ac.maintenance_eta = None
        for slot in s.maintenance_slots:
            if aircraft_id in slot.current_occupants:
                slot.current_occupants.remove(aircraft_id)
        s.event_log.append(f"[H{s.current_hour:02d}] MAINT COMPLETE: {aircraft_id} returned to flight line")
        return s

    def consume_resources(state, mission_id):
        s = copy.deepcopy(state)
        s.resources.fuel = max(0, s.resources.fuel - random.randint(800, 2000))
        s.event_log.append(f"[H{s.current_hour:02d}] Resources consumed for {mission_id}")
        return s

    def advance_time(state, hours):
        s = copy.deepcopy(state)
        new_hour = s.current_hour + hours
        s.current_day += new_hour // 24
        s.current_hour = new_hour % 24
        s.event_log.append(f"[H{s.current_hour:02d}] Time advanced +{hours}h → Day {s.current_day}")
        return s

    def return_from_mission(state, aircraft_id):
        s = copy.deepcopy(state)
        for ac in s.aircraft:
            if ac.id == aircraft_id:
                ac.status = "green"
                ac.location = "flight_line"
                ac.remaining_life = max(0, ac.remaining_life - random.randint(3, 8))
        s.event_log.append(f"[H{s.current_hour:02d}] {aircraft_id} returned from mission")
        return s

    def trigger_resupply_delay(state):
        s = copy.deepcopy(state)
        weapon = random.choice(list(s.resources.weapons.keys()))
        reduction = random.randint(2, 4)
        s.resources.weapons[weapon] = max(0, s.resources.weapons[weapon] - reduction)
        s.event_log.append(f"[H{s.current_hour:02d}] RESUPPLY DELAY: {weapon} −{reduction} units")
        return s

    def trigger_bredduppgift(state):
        s = copy.deepcopy(state)
        new_id = f"M{len(s.ato.missions) + 1:02d}"
        dep = (s.current_hour + 2) % 24
        ret = (s.current_hour + 6) % 24
        mtype = random.choice(["DCA", "RECCE", "AI/ST", "QRA"])
        config_map = {"DCA": "DCA/CAP", "RECCE": "RECCE", "AI/ST": "AI/ST", "QRA": "DCA/CAP"}
        s.ato.missions.append(Mission(new_id, mtype, 2, config_map[mtype], dep, ret, []))
        s.event_log.append(f"[H{s.current_hour:02d}] BREDDUPPGIFT: {new_id} {mtype} H{dep:02d}–H{ret:02d}")
        return s

    def assign_aircraft(state, mission_id, aircraft_ids):
        s = copy.deepcopy(state)
        for m in s.ato.missions:
            if m.id == mission_id:
                for ac_id in aircraft_ids:
                    for ac in s.aircraft:
                        if ac.id == ac_id:
                            if ac.status != "green":
                                raise ValueError(f"{ac_id} is not available (status: {ac.status})")
                            ac.status = "on_mission"
                            ac.location = "on_mission"
                m.assigned_aircraft = list(aircraft_ids)
                break
        s.event_log.append(
            f"[H{s.current_hour:02d}] ASSIGN: {', '.join(aircraft_ids)} → {mission_id}"
        )
        return s

    def chat(state, message, history):
        return (
            f"[LLM not connected — Dev 3's llm.py not found]\n\n"
            f"Your question: *'{message}'*\n\n"
            f"Fleet: {len(state.aircraft)} aircraft | "
            f"Day {state.current_day} H{state.current_hour:02d}:00 | "
            f"Phase: {state.ato.phase}"
        )

    USING_STUBS = True


# ── CSS ────────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
/* ── Global: force every element dark bg + light text ── */
*, *::before, *::after {
    color: #e6edf3 !important;
    border-color: #3d444d !important;
    box-sizing: border-box;
}
body, .gradio-container, .main, .contain {
    background-color: #0d1117 !important;
    font-family: 'Courier New', monospace !important;
}
footer { display: none !important; }

/* ── All panels, blocks, rows, columns ── */
.block, .form, .panel, .wrap, .gap, .padded,
.tabitem, [role="tabpanel"],
.svelte-1ipelgc, .svelte-vt1mxs {
    background-color: #0d1117 !important;
    border-color: #3d444d !important;
}

/* ── Tab nav ── */
.tab-nav {
    background-color: #161b22 !important;
    border-bottom: 1px solid #3d444d !important;
}
.tab-nav button {
    background-color: #161b22 !important;
    color: #8b949e !important;
    border: none !important;
    border-bottom: 2px solid transparent !important;
    font-family: 'Courier New', monospace !important;
    text-transform: uppercase;
    letter-spacing: 2px;
    font-size: 10px;
    padding: 8px 16px !important;
}
.tab-nav button.selected {
    color: #e6edf3 !important;
    border-bottom: 2px solid #1f6feb !important;
    background-color: #161b22 !important;
}

/* ── Inputs, textareas ── */
textarea, input, select {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border: 1px solid #3d444d !important;
}
textarea::placeholder, input::placeholder {
    color: #6e7681 !important;
}

/* ── Dropdowns ── */
.dropdown-arrow, .options, ul[role="listbox"], li[role="option"] {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
    border-color: #3d444d !important;
}
li[role="option"]:hover {
    background-color: #21262d !important;
}

/* ── Chatbot ── */
.chatbot, [data-testid="chatbot"] {
    background-color: #0d1117 !important;
    border: 1px solid #3d444d !important;
}
.chatbot .message, .message-bubble-border {
    border-color: #3d444d !important;
}
.chatbot .bot.message, .chatbot [data-testid="bot"] {
    background-color: #161b22 !important;
    color: #e6edf3 !important;
}
.chatbot .user.message, .chatbot [data-testid="user"] {
    background-color: #1a2332 !important;
    color: #e6edf3 !important;
}

/* ── Buttons ── */
button {
    background-color: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #3d444d !important;
}
button.primary { background-color: #1f6feb !important; border-color: #1f6feb !important; }
button.stop    { background-color: #6e1717 !important; border-color: #f85149 !important; }
button:hover   { border-color: #d29922 !important; }

/* ── Event buttons ── */
.evt-btn button {
    background-color: #21262d !important;
    color: #e6edf3 !important;
    font-family: 'Courier New', monospace !important;
    text-transform: uppercase;
    font-size: 9px;
    letter-spacing: 1px;
}
.evt-btn button:hover { border-color: #d29922 !important; color: #d29922 !important; }

/* ── Accordion ── */
details, details > summary {
    background-color: #161b22 !important;
    border-color: #3d444d !important;
    color: #e6edf3 !important;
}

/* ── Status bar ── */
.status-bar {
    font-family: 'Courier New', monospace;
    font-size: 11px;
    background-color: #161b22 !important;
    border: 1px solid #3d444d;
    border-radius: 6px;
    padding: 10px 16px;
    display: flex;
    gap: 20px;
    align-items: center;
    flex-wrap: wrap;
}

/* ── Aircraft grid & cards ── */
.aircraft-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(178px, 1fr));
    gap: 10px;
    padding: 14px;
    background-color: #0d1117;
}
.ac-card {
    border-radius: 5px;
    padding: 11px 13px;
    font-family: 'Courier New', monospace;
    font-size: 11px;
    border-left: 4px solid;
    background-color: #161b22;
    color: #e6edf3;
    line-height: 1.55;
}
.ac-card.s-green      { border-left-color: #3fb950; }
.ac-card.s-red        { border-left-color: #f85149; background-color: #1c1010; }
.ac-card.s-grey       { border-left-color: #484f58; opacity: 0.7; }
.ac-card.s-on_mission { border-left-color: #d29922; background-color: #1c1a0f; }

/* ── Event log ── */
.event-log {
    font-family: 'Courier New', monospace;
    font-size: 10px;
    background-color: #0d1117;
    color: #3fb950;
    padding: 8px 10px;
    height: 120px;
    overflow-y: auto;
    border: 1px solid #3d444d;
    border-radius: 4px;
    line-height: 1.7;
}

/* ── Chat column separator ── */
.chat-col { border-left: 1px solid #3d444d; padding-left: 12px; }
"""

# ── Render helpers ─────────────────────────────────────────────────────────────

_STATUS_META = {
    "green":      ("READY",        "#3fb950"),
    "red":        ("MAINTENANCE",  "#f85149"),
    "grey":       ("CANNIBALIZED", "#484f58"),
    "on_mission": ("ON MISSION",   "#d29922"),
}

_DARK = dict(paper_bgcolor="#0d1117", plot_bgcolor="#161b22",
             font=dict(color="#c9d1d9", family="Courier New"))


def render_status_bar(state) -> str:
    counts = {s: 0 for s in _STATUS_META}
    for ac in state.aircraft:
        counts[ac.status] = counts.get(ac.status, 0) + 1
    phase_color = {"Fred": "#3fb950", "Kris": "#d29922", "Krig": "#f85149"}.get(state.ato.phase, "#888")
    stub_badge = (
        '&nbsp;<span style="color:#d29922;font-size:9px;border:1px solid #d29922;'
        'padding:1px 5px;border-radius:3px">MOCK DATA</span>'
    ) if USING_STUBS else ""
    return f"""
    <div class="status-bar">
      <span style="color:#e6edf3;font-size:13px;font-weight:bold">&#9654; BASE COMMANDER</span>
      <span style="color:#3fb950">&#9632; READY: {counts.get('green', 0)}</span>
      <span style="color:#d29922">&#9632; ON MISSION: {counts.get('on_mission', 0)}</span>
      <span style="color:#f85149">&#9632; MAINTENANCE: {counts.get('red', 0)}</span>
      <span style="color:#484f58">&#9632; CANNIBALIZED: {counts.get('grey', 0)}</span>
      <span style="margin-left:auto">
        DAY {state.current_day} &nbsp;|&nbsp; H{state.current_hour:02d}:00
        &nbsp;|&nbsp; <span style="color:{phase_color};font-weight:bold">PHASE: {state.ato.phase.upper()}</span>
        {stub_badge}
      </span>
    </div>
    """


def render_missions_html(state) -> str:
    rows = []
    for m in state.ato.missions:
        n_assigned = len(m.assigned_aircraft)
        n_req = m.required_aircraft
        if n_assigned >= n_req:
            status_color = "#3fb950"
            status_label = "FULL"
        elif n_assigned > 0:
            status_color = "#d29922"
            status_label = f"{n_assigned}/{n_req}"
        else:
            status_color = "#f85149"
            status_label = "UNASSIGNED"
        assigned_str = ", ".join(m.assigned_aircraft) if m.assigned_aircraft else "—"
        desc = getattr(m, "description", "")
        rows.append(f"""
        <tr style="border-bottom:1px solid #21262d">
          <td style="padding:5px 8px;color:#e6edf3;font-weight:bold">{m.id}</td>
          <td style="padding:5px 8px">{m.type}</td>
          <td style="padding:5px 8px;color:#8b949e">H{m.departure_hour:02d}:00 — H{m.return_hour:02d}:00</td>
          <td style="padding:5px 8px;color:#a371f7">{m.required_config}</td>
          <td style="padding:5px 8px;font-weight:bold;color:{status_color}">{status_label}</td>
          <td style="padding:5px 8px;color:#c9d1d9">{assigned_str}</td>
          <td style="padding:5px 8px;color:#484f58;font-size:10px">{desc}</td>
        </tr>""")
    return f"""
    <div style="overflow-x:auto">
    <table style="width:100%;font-family:'Courier New',monospace;font-size:11px;border-collapse:collapse;background:#0d1117">
      <thead>
        <tr style="color:#8b949e;border-bottom:2px solid #30363d;text-transform:uppercase;letter-spacing:1px;font-size:9px">
          <th style="text-align:left;padding:5px 8px">ID</th>
          <th style="text-align:left;padding:5px 8px">Type</th>
          <th style="text-align:left;padding:5px 8px">Time Window</th>
          <th style="text-align:left;padding:5px 8px">Config Required</th>
          <th style="text-align:left;padding:5px 8px">Status</th>
          <th style="text-align:left;padding:5px 8px">Assigned Aircraft</th>
          <th style="text-align:left;padding:5px 8px">Description</th>
        </tr>
      </thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    </div>"""


def render_fleet_html(state) -> str:
    # Build lookup: aircraft_id -> mission
    ac_mission_map = {}
    for m in state.ato.missions:
        for ac_id in m.assigned_aircraft:
            ac_mission_map[ac_id] = m

    cards = []
    for ac in state.aircraft:
        label, color = _STATUS_META.get(ac.status, ("UNKNOWN", "#888"))
        life_pct = min(100, max(0, (ac.remaining_life / 200) * 100))
        bar_color = "#f85149" if ac.remaining_life < 50 else "#d29922" if ac.remaining_life < 100 else "#3fb950"
        fault_html = (
            f'<div style="color:#f85149;font-size:10px;margin-top:3px">&#9888; {ac.fault}</div>'
            if ac.fault else ""
        )
        eta_html = (
            f'<div style="color:#d29922;font-size:10px">Repair ETA: {ac.maintenance_eta}h</div>'
            if ac.maintenance_eta else ""
        )
        mission = ac_mission_map.get(ac.id)
        mission_html = (
            f'<div style="color:#d29922;font-size:10px;margin-top:2px">&#9658; {mission.id}: {mission.type}</div>'
            if mission else ""
        )
        payload_str = ", ".join(ac.current_payload[:3]) if ac.current_payload else "—"
        loc_str = ac.location.replace("_", " ").title()
        life_warn = ' style="color:#f85149"' if ac.remaining_life < 50 else (' style="color:#d29922"' if ac.remaining_life < 100 else '')
        cards.append(f"""
        <div class="ac-card s-{ac.status}">
          <div style="display:flex;justify-content:space-between;align-items:baseline">
            <span style="font-size:15px;font-weight:bold;color:#e6edf3">{ac.id}</span>
            <span style="font-size:9px;color:#484f58">{ac.type}</span>
          </div>
          <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;margin:2px 0 5px 0;color:{color}">{label}</div>
          <div style="height:3px;border-radius:2px;background:#30363d;margin-bottom:5px" title="Life remaining">
            <div style="height:100%;border-radius:2px;width:{life_pct:.0f}%;background:{bar_color}"></div>
          </div>
          <div{life_warn} style="font-size:10px">{ac.remaining_life}h until heavy service</div>
          <div style="font-size:10px;margin-top:3px;color:#c9d1d9">{ac.configuration}</div>
          <div style="font-size:10px;color:#8b949e">Load: {payload_str}</div>
          <div style="font-size:10px;color:#484f58">{loc_str}</div>
          {mission_html}{fault_html}{eta_html}
        </div>""")
    return f'<div class="aircraft-grid">{"".join(cards)}</div>'


def render_wear_chart(state) -> go.Figure:
    acs = sorted(state.aircraft, key=lambda a: a.remaining_life)
    ids   = [ac.id for ac in acs]
    lives = [ac.remaining_life for ac in acs]
    colors = ["#f85149" if l < 50 else "#d29922" if l < 100 else "#3fb950" for l in lives]
    fig = go.Figure(go.Bar(
        y=ids, x=lives, orientation="h",
        marker_color=colors,
        text=[f"{l}h" for l in lives],
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Remaining: %{x}h<extra></extra>",
    ))
    fig.add_vline(x=50,  line_dash="dash", line_color="#f85149",
                  annotation_text="Critical", annotation_font_color="#f85149", annotation_position="top")
    fig.add_vline(x=100, line_dash="dot",  line_color="#d29922",
                  annotation_text="Caution",  annotation_font_color="#d29922", annotation_position="top")
    fig.update_layout(
        **_DARK,
        xaxis=dict(range=[0, 230], gridcolor="#21262d", title="Hours Until Heavy Service"),
        yaxis=dict(gridcolor="#21262d"),
        height=300, margin=dict(l=55, r=70, t=20, b=40),
        showlegend=False,
    )
    return fig


def render_timeline_chart(state) -> go.Figure:
    BASE_DATE = datetime(2026, 3, 14)
    day_off = timedelta(days=state.current_day - 1)
    mission_colors = {
        "DCA": "#1f6feb", "RECCE": "#d29922", "AI/ST": "#3fb950",
        "QRA": "#f85149", "AEW": "#a371f7",
    }
    rows = []
    for m in state.ato.missions:
        start_dt = BASE_DATE + day_off + timedelta(hours=m.departure_hour)
        end_dt   = BASE_DATE + day_off + timedelta(hours=m.return_hour)
        if end_dt <= start_dt:
            end_dt += timedelta(hours=24)
        rows.append(dict(
            Mission=f"{m.id}: {m.type}",
            Start=start_dt, Finish=end_dt,
            Type=m.type,
            Aircraft=", ".join(m.assigned_aircraft) or "UNASSIGNED",
            Status="ASSIGNED" if m.assigned_aircraft else "UNASSIGNED",
        ))
    if not rows:
        fig = go.Figure()
        fig.update_layout(**_DARK, height=260)
        fig.add_annotation(text="No missions in ATO", x=0.5, y=0.5,
                           showarrow=False, font=dict(color="#8b949e", size=14))
        return fig
    df = pd.DataFrame(rows)
    fig = px.timeline(
        df, x_start="Start", x_end="Finish", y="Mission",
        color="Type", color_discrete_map=mission_colors,
        hover_data=["Aircraft", "Status"],
    )
    now_dt = BASE_DATE + day_off + timedelta(hours=state.current_hour)
    fig.add_vline(
        x=now_dt.timestamp() * 1000, line_color="#ffffff",
        line_dash="dash", line_width=2,
        annotation_text=f"NOW H{state.current_hour:02d}",
        annotation_font_color="#ffffff",
    )
    fig.update_layout(
        **_DARK,
        xaxis=dict(gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
        height=280, margin=dict(l=140, r=20, t=30, b=40),
        legend=dict(bgcolor="#161b22", bordercolor="#21262d", title_text="Type"),
        title=dict(
            text=f"ATO Day {state.ato.day} — Phase {state.ato.phase}",
            font=dict(color="#c9d1d9", size=12),
        ),
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def render_maint_chart(state) -> go.Figure:
    labels   = [f"{s.id}<br>{s.type.replace('_', ' ')}" for s in state.maintenance_slots]
    occupied = [len(s.current_occupants) for s in state.maintenance_slots]
    avail    = [max(0, s.capacity - len(s.current_occupants)) for s in state.maintenance_slots]
    oc_text  = [", ".join(s.current_occupants) or "Empty" for s in state.maintenance_slots]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Occupied",  x=labels, y=occupied, marker_color="#f85149",
                         text=oc_text, textposition="auto"))
    fig.add_trace(go.Bar(name="Available", x=labels, y=avail,    marker_color="#3fb950"))
    fig.update_layout(
        **_DARK,
        barmode="stack",
        height=200, margin=dict(l=40, r=20, t=30, b=60),
        title=dict(text="Maintenance Slot Utilization", font=dict(color="#c9d1d9", size=12)),
        legend=dict(bgcolor="#161b22"),
        yaxis=dict(dtick=1, gridcolor="#21262d"),
    )
    return fig


def render_weapons_chart(state) -> go.Figure:
    names  = list(state.resources.weapons.keys())
    counts = list(state.resources.weapons.values())
    colors = ["#f85149" if c < 4 else "#d29922" if c < 8 else "#3fb950" for c in counts]
    fig = go.Figure(go.Bar(
        x=counts, y=names, orientation="h",
        marker_color=colors,
        text=counts, textposition="outside",
    ))
    fig.update_layout(
        **_DARK,
        title=dict(text="Weapons Inventory", font=dict(color="#c9d1d9", size=12)),
        xaxis=dict(range=[0, max(counts, default=1) + 4], gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
        height=230, margin=dict(l=90, r=60, t=40, b=20),
        showlegend=False,
    )
    return fig


def render_personnel_chart(state) -> go.Figure:
    p     = state.resources.personnel
    roles = [r.replace("_", " ").title() for r in p.keys()]
    avail = list(p.values())
    req_map = {"Klargoring Crew": 3, "Maintenance Tech": 2, "Pilots": 6, "Avionics Tech": 2}
    reqs  = [req_map.get(r, 2) for r in roles]
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Available",    x=roles, y=avail,
                         marker_color="#1f6feb", text=avail, textposition="auto"))
    fig.add_trace(go.Bar(name="Min. Required", x=roles, y=reqs,
                         marker_color="#f85149", opacity=0.45))
    fig.update_layout(
        **_DARK,
        barmode="overlay",
        title=dict(text="Personnel", font=dict(color="#c9d1d9", size=12)),
        height=230, margin=dict(l=40, r=20, t=40, b=80),
        legend=dict(bgcolor="#161b22"),
        yaxis=dict(gridcolor="#21262d"),
    )
    return fig


def render_fuel_chart(state) -> go.Figure:
    fuel_max = 30000
    fuel_cur = state.resources.fuel
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=fuel_cur,
        number=dict(suffix=" L", font=dict(color="#c9d1d9", family="Courier New", size=22)),
        gauge=dict(
            axis=dict(range=[0, fuel_max], tickcolor="#c9d1d9", tickfont=dict(size=9)),
            bar=dict(color="#1f6feb"),
            bgcolor="#161b22",
            bordercolor="#21262d",
            steps=[
                dict(range=[0, fuel_max * 0.25], color="#3d0f0f"),
                dict(range=[fuel_max * 0.25, fuel_max * 0.5], color="#3d2b0f"),
            ],
            threshold=dict(
                line=dict(color="#f85149", width=3),
                thickness=0.75,
                value=fuel_max * 0.25,
            ),
        ),
        title=dict(text="Fuel Level", font=dict(color="#c9d1d9", family="Courier New", size=12)),
    ))
    fig.update_layout(
        paper_bgcolor="#0d1117",
        font=dict(color="#c9d1d9"),
        height=230, margin=dict(l=20, r=20, t=50, b=10),
    )
    return fig


def render_eu_chart(state) -> go.Figure:
    eu     = state.resources.exchange_units
    names  = list(eu.keys())
    counts = list(eu.values())
    colors = ["#f85149" if c == 0 else "#d29922" if c == 1 else "#3fb950" for c in counts]
    fig = go.Figure(go.Bar(
        x=counts, y=names, orientation="h",
        marker_color=colors,
        text=counts, textposition="outside",
    ))
    fig.update_layout(
        **_DARK,
        title=dict(text="Exchange Units (UE)", font=dict(color="#c9d1d9", size=12)),
        xaxis=dict(range=[0, max(counts, default=1) + 2], gridcolor="#21262d"),
        yaxis=dict(gridcolor="#21262d"),
        height=230, margin=dict(l=130, r=60, t=40, b=20),
        showlegend=False,
    )
    return fig


def render_event_log(state) -> str:
    recent = state.event_log[-15:]
    lines = "".join(f"<div>{line}</div>" for line in reversed(recent))
    placeholder = "<div style='color:#484f58'>No events yet</div>"
    return f'<div class="event-log">{lines or placeholder}</div>'


# ── Main UI builder ────────────────────────────────────────────────────────────

def build_ui():
    def refresh_all(state):
        ac_ids = [ac.id for ac in state.aircraft]
        mission_choices = [
            f"{m.id}: {m.type} — H{m.departure_hour:02d}→H{m.return_hour:02d} "
            f"({len(m.assigned_aircraft)}/{m.required_aircraft} assigned, needs {m.required_config})"
            for m in state.ato.missions
        ]
        avail_ac_choices = [
            f"{ac.id} | {ac.type} | {ac.configuration} | {ac.remaining_life}h remaining"
            for ac in state.aircraft if ac.status == "green"
        ]
        return (
            render_status_bar(state),
            render_fleet_html(state),
            render_wear_chart(state),
            render_missions_html(state),
            render_timeline_chart(state),
            render_maint_chart(state),
            render_weapons_chart(state),
            render_personnel_chart(state),
            render_fuel_chart(state),
            render_eu_chart(state),
            render_event_log(state),
            gr.update(choices=ac_ids, value=None),
            gr.update(choices=mission_choices, value=None),
            gr.update(choices=avail_ac_choices, value=None),
            state,
        )

    with gr.Blocks(title="SAAB Base Commander") as demo:

        state = gr.State(value=create_initial_state())

        # ── Status bar ───────────────────────────────────────────────────────
        status_html = gr.HTML()

        # ── Main: tabs (left) + chat (right) ─────────────────────────────────
        with gr.Row():
            with gr.Column(scale=3):
                with gr.Tabs():

                    # ── Fleet Status tab ──────────────────────────────────
                    with gr.Tab("Fleet Status"):
                        gr.Markdown("**Aircraft cards** — colour-coded by status: green = ready, amber = on mission, red = maintenance, grey = cannibalized. Bar shows hours until next heavy service.")
                        fleet_html = gr.HTML()
                        gr.Markdown("**Wear chart** — sorted by remaining flight hours. Red line = critical (<50h), amber = caution (<100h).")
                        wear_plot  = gr.Plot(show_label=False)

                    # ── Timeline tab ──────────────────────────────────────
                    with gr.Tab("Timeline / ATO"):
                        gr.Markdown("**ATO Mission List** — shows all planned sorties, required config, and current assignments.")
                        missions_html = gr.HTML()
                        gr.Markdown("**Timeline** — horizontal bars show departure and return windows. White dashed line = current time.")
                        timeline_plot = gr.Plot(show_label=False)
                        gr.Markdown("**Maintenance Slots** — capacity vs current occupancy per bay type.")
                        maint_plot    = gr.Plot(show_label=False)

                    # ── Resources tab ─────────────────────────────────────
                    with gr.Tab("Resources & Logistics"):
                        with gr.Row():
                            weapons_plot   = gr.Plot(show_label=False)
                            personnel_plot = gr.Plot(show_label=False)
                        with gr.Row():
                            fuel_plot = gr.Plot(show_label=False)
                            eu_plot   = gr.Plot(show_label=False)

            # ── Chat (always visible on the right) ───────────────────────────
            with gr.Column(scale=2, elem_classes=["chat-col"]):
                gr.Markdown("### Base Commander AI")
                chatbot = gr.Chatbot(
                    label="",
                    height=420,
                )
                chat_input = gr.Textbox(
                    placeholder='e.g. "Which aircraft should we send on the next DCA sortie?"',
                    label="",
                    lines=2,
                )
                with gr.Row():
                    chat_btn  = gr.Button("SEND",  size="sm", variant="primary")
                    clear_btn = gr.Button("CLEAR", size="sm")

        # ── Aircraft Assignment ────────────────────────────────────────────────
        gr.Markdown("---\n### Aircraft Assignment\nSelect a mission and one or more available (green) aircraft, then click **Assign** to commit.")
        with gr.Row():
            mission_assign_dd = gr.Dropdown(
                choices=[], label="Mission", interactive=True, scale=3,
                info="Pick the mission to assign aircraft to",
            )
            aircraft_assign_dd = gr.Dropdown(
                choices=[], label="Available Aircraft (select one or more)", multiselect=True,
                interactive=True, scale=4,
                info="Only green / ready aircraft are shown",
            )
            assign_btn = gr.Button("ASSIGN", variant="primary", scale=1)

        # ── Event injection ───────────────────────────────────────────────────
        gr.Markdown("---\n### Event Injection\nSelect a target aircraft from the dropdown, then trigger an event. *Bredduppgift* and *Resupply Delay* act on the whole base.")
        with gr.Row():
            ac_selector  = gr.Dropdown(choices=[], label="Target Aircraft", interactive=True, scale=1)
            bit_btn      = gr.Button("BIT Fault Check",   elem_classes=["evt-btn"], scale=1)
            returns_btn  = gr.Button("Aircraft Returns",  elem_classes=["evt-btn"], scale=1)
            breddup_btn  = gr.Button("Bredduppgift (New Mission)", elem_classes=["evt-btn"], scale=2)
            resupply_btn = gr.Button("Resupply Delay",    elem_classes=["evt-btn"], scale=1)
            advance_btn  = gr.Button("Advance +2h",       elem_classes=["evt-btn"], scale=1)

        event_log_html = gr.HTML()

        # ── Demo scenario shortcuts ───────────────────────────────────────────
        with gr.Accordion("Demo Scenarios", open=False):
            gr.Markdown("*Pre-staged events from the demo script — click to trigger instantly.*")
            with gr.Row():
                sc1_btn = gr.Button("Scenario 1 — New ATO (4× DCA + 2× RECCE)", variant="secondary")
                sc2_btn = gr.Button("Scenario 2 — GE05 BIT Fail + On-Mission Aircraft Returns Damaged", variant="stop")
                sc3_btn = gr.Button("Scenario 3 — Advance +12h + Resupply Disruption", variant="secondary")

        # ── ALL_OUTPUTS list (defined after all components) ───────────────────
        ALL_OUTPUTS = [
            status_html, fleet_html, wear_plot,
            missions_html, timeline_plot, maint_plot,
            weapons_plot, personnel_plot, fuel_plot, eu_plot,
            event_log_html, ac_selector,
            mission_assign_dd, aircraft_assign_dd,
            state,
        ]

        # ── Callbacks ─────────────────────────────────────────────────────────

        def on_bit_check(ac_id, s):
            if not ac_id:
                return refresh_all(s)
            return refresh_all(trigger_fault(s, ac_id))

        def on_returns(ac_id, s):
            if not ac_id:
                return refresh_all(s)
            return refresh_all(return_from_mission(s, ac_id))

        def on_bredduppgift(s):
            return refresh_all(trigger_bredduppgift(s))

        def on_resupply(s):
            return refresh_all(trigger_resupply_delay(s))

        def on_advance(s):
            return refresh_all(advance_time(s, 2))

        def on_scenario1(s):
            ns = copy.deepcopy(s)
            dep = (ns.current_hour + 1) % 24
            for mtype, config in [
                ("DCA", "DCA/CAP"), ("DCA", "DCA/CAP"), ("DCA", "DCA/CAP"), ("DCA", "DCA/CAP"),
                ("RECCE", "RECCE"), ("RECCE", "RECCE"),
            ]:
                mid = f"M{len(ns.ato.missions) + 1:02d}"
                ns.ato.missions.append(Mission(mid, mtype, 1, config, dep, dep + 4, []))
            ns.event_log.append(
                f"[H{ns.current_hour:02d}] DEMO SC1: New ATO — 4× DCA, 2× RECCE added"
            )
            return refresh_all(ns)

        def on_scenario2(s):
            ns = copy.deepcopy(s)
            ns = trigger_fault(ns, "GE05")
            # Find whichever aircraft is currently on_mission (other than GE05)
            returning_ac = next(
                (ac for ac in ns.aircraft if ac.status == "on_mission" and ac.id != "GE05"),
                None,
            )
            if returning_ac:
                ns = return_from_mission(ns, returning_ac.id)
                # Guarantee the returning aircraft is damaged
                ac_after = next((a for a in ns.aircraft if a.id == returning_ac.id), None)
                if ac_after and ac_after.status == "green":
                    ns = trigger_fault(ns, returning_ac.id)
                ns.event_log.append(
                    f"[H{ns.current_hour:02d}] DEMO SC2: GE05 BIT fail + {returning_ac.id} returned damaged"
                )
            else:
                ns.event_log.append(
                    f"[H{ns.current_hour:02d}] DEMO SC2: GE05 BIT fail (no aircraft currently on mission)"
                )
            return refresh_all(ns)

        def on_scenario3(s):
            ns = advance_time(s, 12)
            ns = trigger_resupply_delay(ns)
            ns = trigger_resupply_delay(ns)
            ns.event_log.append(
                f"[H{ns.current_hour:02d}] DEMO SC3: +12h advance + double resupply disruption"
            )
            return refresh_all(ns)

        def on_assign_aircraft(mission_choice, aircraft_choices, s):
            if not mission_choice or not aircraft_choices:
                return refresh_all(s)
            mission_id = mission_choice.split(":")[0].strip()
            ac_ids = [ac.split("|")[0].strip() for ac in aircraft_choices]
            try:
                ns = copy.deepcopy(s)
                ns = assign_aircraft(ns, mission_id, ac_ids)
            except Exception as e:
                ns = copy.deepcopy(s)
                ns.event_log.append(f"[H{ns.current_hour:02d}] ERROR: Assignment failed — {e}")
            return refresh_all(ns)

        def on_chat(message, history, s):
            if not message or not message.strip():
                return history, ""
            response = chat(s, message, history)
            return history + [{"role": "user", "content": message}, {"role": "assistant", "content": response}], ""

        def on_clear_chat():
            return [], ""

        # ── Wire buttons ──────────────────────────────────────────────────────

        assign_btn.click(fn=on_assign_aircraft, inputs=[mission_assign_dd, aircraft_assign_dd, state], outputs=ALL_OUTPUTS)

        bit_btn.click(fn=on_bit_check,   inputs=[ac_selector, state], outputs=ALL_OUTPUTS)
        returns_btn.click(fn=on_returns, inputs=[ac_selector, state], outputs=ALL_OUTPUTS)
        breddup_btn.click(fn=on_bredduppgift, inputs=[state], outputs=ALL_OUTPUTS)
        resupply_btn.click(fn=on_resupply,    inputs=[state], outputs=ALL_OUTPUTS)
        advance_btn.click(fn=on_advance,      inputs=[state], outputs=ALL_OUTPUTS)

        sc1_btn.click(fn=on_scenario1, inputs=[state], outputs=ALL_OUTPUTS)
        sc2_btn.click(fn=on_scenario2, inputs=[state], outputs=ALL_OUTPUTS)
        sc3_btn.click(fn=on_scenario3, inputs=[state], outputs=ALL_OUTPUTS)

        chat_btn.click(fn=on_chat,    inputs=[chat_input, chatbot, state], outputs=[chatbot, chat_input])
        chat_input.submit(fn=on_chat, inputs=[chat_input, chatbot, state], outputs=[chatbot, chat_input])
        clear_btn.click(fn=on_clear_chat, outputs=[chatbot, chat_input])

        # ── Initial load (populate all charts on page load) ───────────────────
        demo.load(
            fn=lambda s: refresh_all(s)[:-1],
            inputs=[state],
            outputs=ALL_OUTPUTS[:-1],
        )

    return demo
