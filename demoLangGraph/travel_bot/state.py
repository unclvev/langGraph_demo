from typing import TypedDict, Annotated, Sequence, List
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

class AgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], "The messages in the conversation"]
    session_id: Annotated[str, "The session ID"]
    intent: Annotated[str, "The detected intent"]
    entities: Annotated[dict, "The extracted entities"]
    missing_entities: Annotated[List[str], "List of missing entities"]
    current_step: Annotated[str, "Current step in the conversation"]

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
    state.setdefault("messages", [])
    state.setdefault("session_id", "studio")
    state.setdefault("intent", "")
    state.setdefault("entities", {})
    state.setdefault("missing_entities", [])
    state.setdefault("current_step", "")
    return state
