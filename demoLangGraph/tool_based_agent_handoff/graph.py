try:
    from langgraph.graph import StateGraph, START, END
except ImportError:
    # Fallback for when langgraph is not available
    StateGraph = None
    START = "__start__"
    END = "__end__"
from .state import AgentState
from .nodes import init_state
from .agents import FlightSpecialistAgent, HotelSpecialistAgent, GeneralAssistantAgent
from .routing import route_based_on_state_and_transfer, route_with_continuation_check


def create_true_tool_handoff_bot(llm):
    """True tool-based agent handoff - agents transfer to each other"""

    # Create agents
    flight_agent = FlightSpecialistAgent(llm)
    hotel_agent = HotelSpecialistAgent(llm)
    general_agent = GeneralAssistantAgent(llm)

    # Create graph
    g = StateGraph(AgentState)

    # Add nodes
    g.add_node("init_state", init_state)
    g.add_node("flight_specialist", flight_agent.process)
    g.add_node("hotel_specialist", hotel_agent.process)
    g.add_node("general_assistant", general_agent.process)

    # Start with initialization
    g.add_edge(START, "init_state")
    g.add_edge("init_state", "general_assistant")

    # Each agent can transfer to others OR end using state-based routing
    g.add_conditional_edges(
        "flight_specialist",
        route_based_on_state_and_transfer,
        ["hotel_specialist", "general_assistant", END]
    )

    g.add_conditional_edges(
        "hotel_specialist",
        route_based_on_state_and_transfer,
        ["flight_specialist", "general_assistant", END]
    )

    g.add_conditional_edges(
        "general_assistant",
        route_based_on_state_and_transfer,
        ["flight_specialist", "hotel_specialist", END]
    )

    return g.compile()


def create_simple_handoff_bot(llm):
    """Simplified version for testing"""

    # Create agents
    flight_agent = FlightSpecialistAgent(llm)
    hotel_agent = HotelSpecialistAgent(llm)
    general_agent = GeneralAssistantAgent(llm)

    # Create graph
    g = StateGraph(AgentState)

    # Add nodes
    g.add_node("init_state", init_state)
    g.add_node("flight_specialist", flight_agent.process)
    g.add_node("hotel_specialist", hotel_agent.process)
    g.add_node("general_assistant", general_agent.process)

    # Simple routing - start with general assistant
    g.add_edge(START, "init_state")
    g.add_edge("init_state", "general_assistant")

    # All agents can go to END (end conversation)
    g.add_edge("flight_specialist", END)
    g.add_edge("hotel_specialist", END)
    g.add_edge("general_assistant", END)

    return g.compile()


def create_advanced_handoff_bot(llm):
    """Advanced version with conversation continuation"""

    # Create agents
    flight_agent = FlightSpecialistAgent(llm)
    hotel_agent = HotelSpecialistAgent(llm)
    general_agent = GeneralAssistantAgent(llm)

    # Create graph
    g = StateGraph(AgentState)

    # Add nodes
    g.add_node("init_state", init_state)
    g.add_node("flight_specialist", flight_agent.process)
    g.add_node("hotel_specialist", hotel_agent.process)
    g.add_node("general_assistant", general_agent.process)

    # Start with initialization
    g.add_edge(START, "init_state")
    g.add_edge("init_state", "general_assistant")

    g.add_conditional_edges(
        "flight_specialist",
        route_with_continuation_check,
        {
            "hotel_specialist": "hotel_specialist",
            "general_assistant": "general_assistant",
            END: END
        }
    )

    g.add_conditional_edges(
        "hotel_specialist",
        route_with_continuation_check,
        {
            "flight_specialist": "flight_specialist",
            "general_assistant": "general_assistant",
            END: END
        }
    )

    g.add_conditional_edges(
        "general_assistant",
        route_with_continuation_check,
        {
            "flight_specialist": "flight_specialist",
            "hotel_specialist": "hotel_specialist",
            END: END
        }
    )

    return g.compile()


