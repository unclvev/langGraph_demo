# demoLangGraph/service_agent/general.py
import os, requests
from typing import List, Dict
from langchain_core.messages import AIMessage
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import ChatGoogleGenerativeAI

from demoLangGraph.travel_bot.state import AgentState, normalize_messages

# ---------- SerpAPI (tùy chọn) ----------
def _serpapi_search(q: str, num: int = 5) -> List[Dict]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []
    try:
        r = requests.get(
            "https://serpapi.com/search.json",
            params={"engine": "google", "q": q, "num": num, "api_key": api_key},
            timeout=8,
        )
        data = r.json()
        out = []
        for item in (data.get("organic_results") or [])[:num]:
            out.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "") or (item.get("snippet_highlighted_words") or [""])[0]
            })
        ab = data.get("answer_box") or {}
        if ab.get("answer"):
            out.insert(0, {"title": "Tóm tắt", "link": "", "snippet": ab["answer"]})
        return out
    except Exception:
        return []

# ---------- LLM (Gemini) ----------
def _llm():
    # Lấy model từ env, mặc định dùng gemini-1.5-flash (nhanh, rẻ)
    model = os.getenv("TRAVEL_BOT_MODEL", "gemini-1.5-flash")
    # GOOGLE_API_KEY phải có trong env/.env
    return ChatGoogleGenerativeAI(model=model, temperature=0.3)

_RULES = """## Prompt Chatbot Du Lịch (Thân thiện)
Bạn là một trợ lý AI thân thiện, dí dỏm, vui tính chuyên hỗ trợ về du lịch.
- Nếu người dùng chào hỏi, hãy chào lại thân thiện và hỏi xem họ cần giúp gì về du lịch.
- Nếu người dùng hỏi về địa danh/điểm vui chơi/tour/khách sạn/ẩm thực/di chuyển,… hãy trả lời rõ ràng, chi tiết và thân thiện.
- Nếu có kết quả từ SerpAPI (SERP_CONTEXT), hãy diễn giải tự nhiên; chỉ nêu link khi thật cần.
- Nếu ngoài du lịch: “Mình là trợ lý du lịch, nên chỉ có thể hỗ trợ các thông tin, tư vấn liên quan đến du lịch thôi nhé.”
- Luôn giữ văn phong tự nhiên, nhiệt tình.
"""

_PROMPT = ChatPromptTemplate.from_messages([
    ("system", _RULES),
    ("system", "SERP_CONTEXT (nếu có):\n{serp_context}"),
    ("human", "{user_query}")
])

def _call_llm_travel(user_query: str, serp_results: List[Dict]) -> str:
    serp_ctx = ""
    if serp_results:
        lines = []
        for r in serp_results[:3]:
            line = f"- {r.get('title','')}: {r.get('snippet','')}"
            if r.get("link"):
                line += f" ({r['link']})"
            lines.append(line)
        serp_ctx = "\n".join(lines)
    chain_input = {"user_query": user_query, "serp_context": serp_ctx}

    # LangChain style: prompt.invoke(...) -> Message, rồi llm.invoke(Message)
    msg = _PROMPT.invoke(chain_input)
    return _llm().invoke(msg).content

# ---------- Node GENERAL (router + LLM) ----------
def general_router(state: AgentState) -> AgentState:
    print("[DEBUG] entered general_router")
    messages = normalize_messages(state.get("messages", []))
    user_text = (messages[-1].content or "").strip() if messages else ""
    txt = user_text.lower()

    # 1) chào hỏi → trả lời nhanh (không cần LLM)
    if any(k in txt for k in ["xin chào", "chào", "hello", "hi"]):
        resp = ("Chào bạn! Mình là trợ lý du lịch "
                "Bạn muốn tìm hiểu địa điểm hay lên kế hoạch chuyến đi nào không?")
    # 2) ngoài du lịch → từ chối nhẹ
    elif any(k in txt for k in ["chứng khoán","coin","crypto","bất động sản","lập trình","ai model"]):
        resp = ("Mình là trợ lý du lịch, nên chỉ có thể hỗ trợ thông tin, tư vấn liên quan đến du lịch thôi nhé. "
                "Nếu bạn cần gợi ý địa điểm, lịch trình, khách sạn hay cách di chuyển, mình sẵn sàng giúp! 🌏")
    # 3) còn lại → gọi SerpAPI (nếu có) + LLM (Gemini)
    else:
        serp = _serpapi_search(user_text, num=5)
        resp = _call_llm_travel(user_text, serp)

    state["messages"] = messages + [AIMessage(content=resp)]
    state["current_step"] = "responded"
    return state
