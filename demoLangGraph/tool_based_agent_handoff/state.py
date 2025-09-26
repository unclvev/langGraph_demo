from typing import TypedDict, Annotated, Sequence, List, Dict, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    # Core conversation data
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    session_id: Annotated[str, "The session ID"]
    
    # Intent and entity management
    intent: Annotated[str, "The detected intent"]
    entities: Annotated[dict, "The extracted entities"]
    missing_entities: Annotated[List[str], "List of missing entities"]
    current_step: Annotated[str, "Current step in the conversation"]
    
    # Agent network state management
    current_agent: Annotated[str, "Current active agent"]
    agent_history: Annotated[List[str], "History of agents that processed the request"]
    conversation_phase: Annotated[str, "Current phase: collecting, processing, finalizing, completed"]
    
    # Domain-specific collected data
    collected_data: Annotated[Dict[str, Any], "Data collected by each agent"]
    flight_info: Annotated[Dict[str, Any], "Flight information collected"]
    hotel_info: Annotated[Dict[str, Any], "Hotel information collected"]
    general_info: Annotated[Dict[str, Any], "General travel information"]
    
    # Completion status tracking
    completion_status: Annotated[Dict[str, bool], "What each agent has completed"]
    required_agents: Annotated[List[str], "List of agents that need to process this request"]
    
    # Context and memory
    stm_context: Annotated[str, "Short-term memory context"]
    user_preferences: Annotated[Dict[str, Any], "User preferences and requirements"]

def normalize_messages(raw_msgs) -> list[BaseMessage]:
    out: list[BaseMessage] = []
    for m in raw_msgs or []:
        if isinstance(m, BaseMessage):
            out.append(m)
        elif isinstance(m, dict):
            t = (m.get("type") or m.get("_type") or "").lower()
            c = m.get("content", "")
            if t in ("human", "human_message", "humanmessage"):
                out.append(HumanMessage(content=c))
            elif t in ("ai", "assistant", "ai_message"):
                out.append(AIMessage(content=c))
            else:
                out.append(HumanMessage(content=str(c)))
        else:
            out.append(HumanMessage(content=str(m)))
    return out

def init_state_defaults(state: AgentState) -> AgentState:
    # Core conversation data
    state.setdefault("messages", [])
    state.setdefault("session_id", "studio")
    
    # Intent and entity management
    state.setdefault("intent", "")
    state.setdefault("entities", {})
    state.setdefault("missing_entities", [])
    state.setdefault("current_step", "")
    
    # Agent network state management
    state.setdefault("current_agent", "general_assistant")
    state.setdefault("agent_history", [])
    state.setdefault("conversation_phase", "collecting")
    
    # Domain-specific collected data
    state.setdefault("collected_data", {})
    state.setdefault("flight_info", {})
    state.setdefault("hotel_info", {})
    state.setdefault("general_info", {})
    
    # Completion status tracking
    state.setdefault("completion_status", {
        "flight_specialist": False,
        "hotel_specialist": False,
        "general_assistant": False
    })
    state.setdefault("required_agents", [])
    
    # Context and memory
    state.setdefault("stm_context", "")
    state.setdefault("user_preferences", {})
    
    return state
