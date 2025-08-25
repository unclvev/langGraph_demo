# nodes.py
import re
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from .state import AgentState, normalize_messages, init_state_defaults
from .catalogs import CATALOGS
from demoLangGraph.rule_agent.detech_intent import detect_and_extract
from demoLangGraph.memory.ShortTerm import ShortTermMemory            # <= NEW

def _safe_last(messages: list[BaseMessage], typ):
    for m in reversed(messages):
        if isinstance(m, typ):
            return m
    return None

def _get_stm(state: AgentState) -> ShortTermMemory:
    user_id = state.get("user_id") or state.get("session_id") or "studio"
    return ShortTermMemory(user_id=user_id)

# Node khởi tạo
def init_state(state: AgentState) -> AgentState:
    print("day la :", state)
    state = init_state_defaults(state)
    # Nạp context gần từ STM (để dùng cho prompt detect)
    try:
        stm = _get_stm(state)
        state["stm_context"] = stm.get_conversation_context(limit=5) or ""
        # Gia hạn TTL nhẹ để tránh rơi context giữa phiên
        stm.extend_ttl(extend_seconds=180)
    except Exception as e:
        # Không chặn flow nếu Redis lỗi
        state["stm_context"] = ""
        print("[STM] init_state error:", e)
    return state

# Node detect intent + entities (dùng STM context)
def detect_intent_and_entities(state: AgentState) -> AgentState:
    messages = normalize_messages(state.get("messages", []))

    if not messages:
        raw = state.get("input")
        if isinstance(raw, str) and raw.strip():
            messages = [HumanMessage(content=raw.strip())]
        else:
            state.update({
                "intent": "general",
                "entities": {},
                "missing_entities": [],
                "current_step": "intent_detected",
                "messages": messages,
            })
            return state

    last = messages[-1]
    user_text = (last.content or "").strip()

    # Ghép STM context (nếu có) để detect mạnh hơn
    stm_ctx = state.get("stm_context") or ""
    detect_text = (
        f"{user_text}"
        + (f"\n\n[Ngữ cảnh gần]\n{stm_ctx}" if stm_ctx else "")
    )

    # 🔁 Gọi LLM ở rule_agent để detect intent & extract entities
    intent, entities, missing = detect_and_extract(detect_text)

    state.update({
        "messages": messages,
        "intent": intent,
        "entities": entities,
        "missing_entities": missing,
        "current_step": "intent_detected",
    })
    return state

# Node trả lời
def generate_response(state: AgentState) -> AgentState:
    messages = normalize_messages(state.get("messages", []))
    intent = (state.get("intent") or "").lower()
    entities = state.get("entities", {})
    missing = state.get("missing_entities", [])

    if intent == "general":
        resp = "[BUG] generate_response called with general"
    else:
        if missing:
            q = []
            ASK = {
                "dia_diem": "Bạn muốn đi đâu?",
                "diem_di": "Bạn khởi hành từ đâu?",
                "thoi_gian_di": "Bạn muốn đi khi nào?",
                "so_nguoi": "Có bao nhiêu người đi?",
                "chi_phi": "Ngân sách của bạn là bao nhiêu?",
                "khu_hoi": "Bạn đi một chiều hay khứ hồi?",
                "hang_ve": "Bạn muốn hạng vé gì?",
                "gia_ve_may_bay": "Ngân sách vé máy bay của bạn là bao nhiêu?",
                "checkin": "Bạn muốn check-in khi nào?",
                "checkout": "Bạn muốn check-out khi nào?",
                "kieu_loai": "Bạn muốn loại phòng gì?",
                "gia_khach_san": "Ngân sách khách sạn của bạn là bao nhiêu?",
            }
            for name in missing:
                if name in ASK:
                    q.append(ASK[name])
            resp = f"Tôi hiểu bạn muốn {intent.replace('_', ' ')}. " + " ".join(q[:2])
        else:
            resp = (
                f"Tuyệt vời! Tôi đã hiểu yêu cầu của bạn về {intent.replace('_', ' ')}. "
                f"Địa điểm: {entities.get('dia_diem', 'N/A')}, "
            )
            if "so_nguoi" in entities:
                resp += f"Số người: {entities['so_nguoi']}, "
            if "thoi_gian_di" in entities:
                resp += f"Thời gian: {entities['thoi_gian_di']}"
            resp += "\nBạn có muốn tôi tiếp tục hỗ trợ không?"

    state["messages"] = messages + [AIMessage(content=resp)]
    state["current_step"] = "responded"
    return state

# NEW: Node ghi STM cho mọi nhánh
def write_short_term(state: AgentState) -> AgentState:
    try:
        stm = _get_stm(state)
        msgs = normalize_messages(state.get("messages", []))
        last_user = _safe_last(msgs, HumanMessage)
        last_ai   = _safe_last(msgs, AIMessage)
        if last_user and last_ai:
            stm.add_turn(user_input=last_user.content or "",
                         bot_response=last_ai.content or "",
                         ttl=300)
    except Exception as e:
        print("[STM] write_short_term error:", e)
    return state
