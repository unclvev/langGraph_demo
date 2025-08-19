from langgraph.graph import StateGraph, START, END
from .state import AgentState
from .nodes import init_state, detect_intent_and_entities, generate_response

def create_travel_bot():
    g = StateGraph(AgentState)
    g.add_node("init_state", init_state)
    g.add_node("detect_intent", detect_intent_and_entities)
    g.add_node("generate_response", generate_response)

    g.add_edge(START, "init_state")
    g.add_edge("init_state", "detect_intent")
    g.add_edge("detect_intent", "generate_response")

    def should_continue(state: AgentState) -> str:
        return "generate_response" if state.get("current_step") == "intent_detected" else END

    g.add_conditional_edges("generate_response", should_continue)
    return g.compile()
