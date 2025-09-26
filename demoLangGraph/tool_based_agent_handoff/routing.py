# Enhanced routing.py with state-based decision making
from langchain_core.messages import AIMessage, HumanMessage
try:
    from .state import AgentState, normalize_messages
    from .state_manager import StateManager
except ImportError:
    from state import AgentState, normalize_messages
    from state_manager import StateManager
try:
    from langgraph.graph import END
except ImportError:
    # Fallback for when langgraph is not available
    END = "__end__"


def route_based_on_state_and_transfer(state: AgentState):
    """Route based on state analysis and agent transfer decisions"""

    messages = normalize_messages(state.get("messages", []))
    if not messages:
        return END

    last_message = messages[-1]
    conversation_phase = state.get("conversation_phase", "collecting")
    
    print(f"[ROUTING] Current phase: {conversation_phase}")
    print(f"[ROUTING] Last message: {last_message.content if hasattr(last_message, 'content') else last_message}")
    
    # Priority 1: Content-based transfer signals from agents
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'content'):
        content = last_message.content or ""
        print(f"[ROUTING] Checking content: {content[:100]}...")

        # Look for structured handoff signals
        if "TRANSFER_TO_FLIGHT:" in content:
            print("[ROUTING] -> flight_specialist")
            return "flight_specialist"
        elif "TRANSFER_TO_HOTEL:" in content:
            print("[ROUTING] -> hotel_specialist")
            return "hotel_specialist"
        elif "TRANSFER_TO_GENERAL:" in content:
            print("[ROUTING] -> general_assistant")
            return "general_assistant"
        elif "CONVERSATION_COMPLETE:" in content:
            print("[ROUTING] -> END")
            return END

    # Priority 2: Tool calls from agents
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name', '').lower()

            if 'transfer_to_flight' in tool_name:
                print("[ROUTING] Tool -> flight_specialist")
                return "flight_specialist"
            elif 'transfer_to_hotel' in tool_name:
                print("[ROUTING] Tool -> hotel_specialist")
                return "hotel_specialist"
            elif 'transfer_to_general' in tool_name:
                print("[ROUTING] Tool -> general_assistant")
                return "general_assistant"
            elif 'complete_conversation' in tool_name:
                print("[ROUTING] Tool -> END")
                return END

    # Priority 3: State-based routing
    next_agent = StateManager.determine_next_agent(state)
    print(f"[ROUTING] State-based next agent: {next_agent}")
    
    if next_agent == "finalizing":
        print("[ROUTING] -> general_assistant (finalizing)")
        return "general_assistant"  # Let general assistant finalize
    elif next_agent in ["flight_specialist", "hotel_specialist", "general_assistant"]:
        print(f"[ROUTING] -> {next_agent}")
        return next_agent

    # Fallback: end conversation
    print("[ROUTING] -> END (fallback)")
    return END


def route_based_on_agent_transfer_only(state: AgentState):
    """Route ONLY based on agent's transfer decisions - NO user input analysis"""

    messages = normalize_messages(state.get("messages", []))
    if not messages:
        return END

    last_message = messages[-1]

    # ONLY check agent decisions, NOT user input
    # Priority 1: Tool calls from agents
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name', '').lower()

            if 'transfer_to_flight' in tool_name:
                return "flight_specialist"
            elif 'transfer_to_hotel' in tool_name:
                return "hotel_specialist"
            elif 'transfer_to_general' in tool_name:
                return "general_assistant"
            elif 'complete_conversation' in tool_name:
                return END

    # Priority 2: Content-based transfer signals from agents
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'content'):
        content = last_message.content or ""

        # Look for structured handoff signals
        if "HANDOFF_TO_FLIGHT:" in content:
            return "flight_specialist"
        elif "HANDOFF_TO_HOTEL:" in content:
            return "hotel_specialist"
        elif "HANDOFF_TO_GENERAL:" in content:
            return "general_assistant"
        elif "CONVERSATION_COMPLETE:" in content:
            return END

    # NO FALLBACK to user input analysis!
    # If agent didn't decide to transfer → END (wait for user)
    return END


def route_with_continuation_check(state: AgentState):
    """Route with continuation check - similar to state-based routing but with different logic"""
    
    messages = normalize_messages(state.get("messages", []))
    if not messages:
        return END

    last_message = messages[-1]
    conversation_phase = state.get("conversation_phase", "collecting")
    
    # Check if conversation should end
    if not StateManager.should_continue_conversation(state):
        return END

    # Priority 1: Tool calls from agents
    if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
        for tool_call in last_message.tool_calls:
            tool_name = tool_call.get('name', '').lower()

            if 'transfer_to_flight' in tool_name:
                return "flight_specialist"
            elif 'transfer_to_hotel' in tool_name:
                return "hotel_specialist"
            elif 'transfer_to_general' in tool_name:
                return "general_assistant"
            elif 'complete_conversation' in tool_name:
                return END

    # Priority 2: Content-based transfer signals from agents
    if isinstance(last_message, AIMessage) and hasattr(last_message, 'content'):
        content = last_message.content or ""

        # Look for structured handoff signals
        if "TRANSFER_TO_FLIGHT:" in content:
            return "flight_specialist"
        elif "TRANSFER_TO_HOTEL:" in content:
            return "hotel_specialist"
        elif "TRANSFER_TO_GENERAL:" in content:
            return "general_assistant"
        elif "CONVERSATION_COMPLETE:" in content:
            return END

    # Priority 3: State-based routing with continuation logic
    next_agent = StateManager.determine_next_agent(state)
    if next_agent == "finalizing":
        return "general_assistant"  # Let general assistant finalize
    elif next_agent in ["flight_specialist", "hotel_specialist", "general_assistant"]:
        return next_agent

    # Fallback: end conversation
    return END