"""
app.py — Entry point for the Saab Smart Air Base AI Assistant
Team: blacksaabathsaaboteurs

Dev 1 writes this skeleton.
Dev 2 fills in the Gradio UI (tabs: Fleet, Timeline, Resources).
Dev 3 wires up the LLM chatbot.

Run with:  python app.py
"""

import gradio as gr
from engine import reset_state, get_state  # noqa: F401 — Dev 2/3 import more from here

# ---------------------------------------------------------------------------
# Initialize game state on startup
# ---------------------------------------------------------------------------
reset_state()

# ---------------------------------------------------------------------------
# Dev 2: Build the Gradio Blocks UI here
# All engine imports Dev 2 needs:
#
#   from engine import (
#       get_state, reset_state,
#       assign_aircraft, trigger_fault, complete_maintenance,
#       advance_time, return_from_mission, consume_resources,
#       roll_bit_check, generate_random_event,
#   )
#
# Key state fields:
#   get_state().aircraft          — list[Aircraft]  for fleet table/cards
#   get_state().resources         — ResourceInventory  for charts
#   get_state().ato.missions      — list[Mission]  for Gantt
#   get_state().event_log         — list[str]  for event log panel
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Dev 3: Wire up the LLM chatbot here
# All engine imports Dev 3 needs:
#
#   from engine import get_state, serialize_state, serialize_state_json
#
# Usage:
#   context = serialize_state(get_state())   # inject as {state_json} in system prompt
#   data    = serialize_state_json(get_state())  # raw dict if preferred
# ---------------------------------------------------------------------------

with gr.Blocks(title="Smart Air Base — AI Base Commander") as demo:
    gr.Markdown("# Smart Air Base — AI Base Commander Assistant")
    gr.Markdown("*Saab Hackathon 2026 — Team blacksaabathsaaboteurs*")

    with gr.Tabs():
        with gr.Tab("Fleet Status"):
            gr.Markdown("### Fleet Status\n*Dev 2: implement aircraft cards/table here*")

        with gr.Tab("Timeline"):
            gr.Markdown("### ATO Timeline\n*Dev 2: implement Gantt chart here*")

        with gr.Tab("Resources"):
            gr.Markdown("### Resource Inventory\n*Dev 2: implement charts here*")

        with gr.Tab("Chat"):
            gr.Markdown("### AI Base Commander Chat\n*Dev 3: implement chatbot here*")

if __name__ == "__main__":
    demo.launch()
