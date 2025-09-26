print("[USING NODES]", __file__)

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from .state import AgentState, normalize_messages, init_state_defaults
from demoLangGraph.memory.ShortTerm import ShortTermMemory

def _safe_last(messages: list[BaseMessage], typ):
    """Get last message of specific type"""
    for m in reversed(messages):
        if isinstance(m, typ):
            return m
    return None

def _get_stm(state: AgentState) -> ShortTermMemory:
    """Get ShortTermMemory instance"""
    user_id = state.get("session_id") or "studio"
    return ShortTermMemory(user_id=user_id)

def init_state(state: AgentState) -> AgentState:
    """Initialize state with defaults and load STM context"""
    print("Initializing state:", state)
    state = init_state_defaults(state)
    
    # Load context from STM for better prompts
    try:
        stm = _get_stm(state)
        state["stm_context"] = stm.get_conversation_context(limit=5) or ""
    except Exception as e:
        state["stm_context"] = ""
        print("[STM] init_state error:", e)
    
    return state

def write_short_term(state: AgentState) -> AgentState:
    """Write conversation to short-term memory"""
    try:
        stm = _get_stm(state)
        msgs = normalize_messages(state.get("messages", []))
        last_user = _safe_last(msgs, HumanMessage)
        last_ai = _safe_last(msgs, AIMessage)
        
        if last_user and last_ai:
            stm.add_turn(
                user_input=last_user.content or "",
                bot_response=last_ai.content or "",
                ttl=300
            )
    except Exception as e:
        print("[STM] write_short_term error:", e)
    
    return state
