import re
from langchain_core.messages import HumanMessage, AIMessage
from .state import AgentState, normalize_messages, init_state_defaults
from .catalogs import CATALOGS

# Node khởi tạo
def init_state(state: AgentState) -> AgentState:
    return init_state_defaults(state)

# Node detect intent + entities
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
    text_raw = last.content or ""
    text_lc = text_raw.lower()

    # Detect intent
    intent = "general"
    if any(k in text_lc for k in ["du lịch", "tour", "lịch trình", "đi chơi"]):
        intent = "lich_trinh"
    elif any(k in text_lc for k in ["đặt vé máy bay", "mua vé máy bay", "book flight"]):
        intent = "dat_ve_may_bay"
    elif any(k in text_lc for k in ["đặt khách sạn", "booking khách sạn", "nơi ở"]):
        intent = "dat_khach_san"

    # Extract entities
    entities: dict = {}

    # Địa điểm (case-insensitive)
    location_patterns = [
        r"đi\s+([A-Za-zÀ-ỹĐđ\s]+)",
        r"([A-Za-zÀ-ỹĐđ\s]+)\s+chơi",
        r"([A-Za-zÀ-ỹĐđ\s]+)",
    ]
    for pat in location_patterns:
        m = re.findall(pat, text_raw, flags=re.IGNORECASE)
        if m:
            cand = m[0].strip()
            if len(cand) >= 2 and not re.search(r"\d", cand):
                entities["dia_diem"] = cand
                break

    # Số người
    for pat in [r"(\d+)\s*người", r"(\d+)\s*người\s*đi", r"đi\s*cùng\s*(\d+)\s*người"]:
        mm = re.search(pat, text_lc)
        if mm:
            n = int(mm.group(1))
            if "đi cùng" in text_lc:
                n += 1
            entities["so_nguoi"] = n
            break

    # Thời gian
    time_pats = [
        r"ngày\s*(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})",
        r"tháng\s*(\d{1,2})",
        r"ngày\s*(\d{1,2})",
    ]
    for pat in time_pats:
        mm = re.search(pat, text_lc)
        if mm:
            if len(mm.groups()) == 3:
                entities["thoi_gian_di"] = f"{mm.group(1)}/{mm.group(2)}/{mm.group(3)}"
            else:
                entities["thoi_gian_di"] = mm.group(1)
            break

    # Missing
    missing: list[str] = []
    if intent != "general":
        cat = next((c for c in CATALOGS if c["intent"] == intent), None)
        if cat:
            present = set(entities.keys())
            for e in cat["entities"]:
                name = e["name"]
                if e.get("required") and name not in present:
                    missing.append(name); continue
                if "required_if" in e:
                    cond = e["required_if"]
                    if entities.get(cond.get("field")) == cond.get("value") and name not in present:
                        missing.append(name)

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

    # General không xử lý ở đây nữa
    if intent == "general":
        resp = "[BUG] generate_response called with general"  # để debug nếu lạc route
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

