"""
Tool-based Agent Handoff System

This module implements a true tool-based agent handoff pattern where agents
can transfer to each other using tools, rather than relying on a supervisor.

Key Features:
- Multi-skilled agents with work tools + handoff tools
- Agents can decide to work or transfer independently  
- True peer-to-peer handoff (not supervisor-based)
- Flexible routing based on tool calls and content

Architecture:
User → Agent1 → Agent2 → Agent3 → Agent1 → END
       ↑        ↑        ↑        ↑  
     Tools    Tools    Tools    Tools

Each agent has:
- Work tools (for their specialty: flights, hotels, general info)
- Handoff tools (to transfer to other agents)
- Decision-making capability (LLM + tools)

Usage:
    from demoLangGraph.tool_based_agent_handoff.graph import create_tool_handoff_bot
    
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
    bot = create_tool_handoff_bot(llm, mode="true")
    
    state = {"messages": [HumanMessage(content="Tôi muốn đặt vé máy bay")]}
    result = bot.invoke(state)
"""

from .state import AgentState, normalize_messages, init_state_defaults
from .state_manager import StateManager
from .conversation_controller import ConversationController
from .tools import (
    transfer_to_flight_specialist,
    transfer_to_hotel_specialist, 
    transfer_to_general_assistant,
    search_flights,
    search_hotels,
    book_flight,
    book_hotel,
    get_travel_info,
    FLIGHT_TOOLS,
    HOTEL_TOOLS,
    GENERAL_TOOLS
)
from .agents import BaseAgent, FlightSpecialistAgent, HotelSpecialistAgent, GeneralAssistantAgent
from .routing import route_based_on_state_and_transfer, route_with_continuation_check
from .graph import create_true_tool_handoff_bot, create_simple_handoff_bot, create_advanced_handoff_bot

__all__ = [
    # State
    "AgentState",
    "normalize_messages", 
    "init_state_defaults",
    
    # State Management
    "StateManager",
    "ConversationController",
    
    # Tools
    "transfer_to_flight_specialist",
    "transfer_to_hotel_specialist",
    "transfer_to_general_assistant", 
    "search_flights",
    "search_hotels",
    "book_flight",
    "book_hotel",
    "get_travel_info",
    "FLIGHT_TOOLS",
    "HOTEL_TOOLS", 
    "GENERAL_TOOLS",
    
    # Agents
    "BaseAgent",
    "FlightSpecialistAgent",
    "HotelSpecialistAgent", 
    "GeneralAssistantAgent",
    
    # Routing
    "route_based_on_state_and_transfer",
    "route_based_on_transfer",
    "route_with_continuation_check",
    
    # Graph
    "create_true_tool_handoff_bot",
    "create_simple_handoff_bot",
    "create_advanced_handoff_bot"
]
