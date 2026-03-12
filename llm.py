# llm.py — adapter
# ui.py expects: from llm import chat(state, message, history) -> str
# llm_integration.py provides: LLMAssistant().chat(user_message, state) -> str
from llm_integration import LLMAssistant

_assistant = LLMAssistant()


def chat(state, message, history):
    return _assistant.chat(message, state)
