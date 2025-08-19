# travel_bot/graph.py
from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import init_state, detect_intent_and_entities, generate_response
from ..rule_agent.general import general_router

def create_travel_bot():
    g = StateGraph(AgentState)
    g.add_node("init_state", init_state)
    g.add_node("detect_intent", detect_intent_and_entities)
    g.add_node("general_router", general_router)
    g.add_node("generate_response", generate_response)

    g.add_edge(START, "init_state")
    g.add_edge("init_state", "detect_intent")

    def route_after_detect(state: AgentState) -> str:
        intent = (state.get("intent") or "").strip().lower()
        print("[DEBUG] route_after_detect intent=", repr(intent))
        return "general_router" if intent in ("", "general", "chitchat") else "generate_response"

    g.add_conditional_edges(
        "detect_intent",
        route_after_detect,
        ["general_router", "generate_response"],
    )

    g.add_edge("general_router", END)
    g.add_edge("generate_response", END)
    return g.compile()
