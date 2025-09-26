print("[USING NODES]", __file__)
import os, asyncio
from typing import List, Dict
from langchain_core.messages import AIMessage
from demoLangGraph.travel_bot.state import AgentState, normalize_messages
from demoLangGraph.rule_agent.llm_client import call_llm,call_llm_rule_user
import aiohttp

# ---------- SerpAPI (async, tránh blocking) ----------
async def _serpapi_search(q: str, num: int = 5) -> List[Dict]:
    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        return []
    url = "https://serpapi.com/search.json"
    params = {"engine": "google", "q": q, "num": num, "api_key": api_key}
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, params=params) as resp:
                data = await resp.json()
        out: List[Dict] = []
        for item in (data.get("organic_results") or [])[:num]:
            out.append({
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", "")
                          or (item.get("snippet_highlighted_words") or [""])[0]
            })
        ab = data.get("answer_box") or {}
        if ab.get("answer"):
            out.insert(0, {"title": "Tóm tắt", "link": "", "snippet": ab["answer"]})
        return out
    except Exception:
        return []

# ---------- RULES cho general ----------
_RULES = """## Prompt Chatbot Du Lịch (Thân thiện)
Bạn là một trợ lý AI thân thiện, dí dỏm, vui tính chuyên hỗ trợ về du lịch.
- Nếu người dùng chào hỏi, hãy chào lại thân thiện và hỏi xem họ cần giúp gì về du lịch.
- Nếu người dùng hỏi về địa danh/điểm vui chơi/tour/khách sạn/ẩm thực/di chuyển,… hãy trả lời rõ ràng, chi tiết và thân thiện.
- Nếu có kết quả từ SerpAPI (SERP_CONTEXT), hãy diễn giải tự nhiên; chỉ nêu link khi thật cần.
- Nếu ngoài du lịch: “Mình là trợ lý du lịch, nên chỉ có thể hỗ trợ các thông tin, tư vấn liên quan đến du lịch thôi nhé.”
- Luôn giữ văn phong tự nhiên, nhiệt tình.
"""

# ---------- Node GENERAL (router + LLM qua llm_client) ----------
async def general_router(state: AgentState) -> AgentState:
    print("[DEBUG] entered general_router")
    messages = normalize_messages(state.get("messages", []))
    user_text = (messages[-1].content or "").strip() if messages else ""
    txt = user_text.lower()

    # 1) chào hỏi → trả lời nhanh (không cần LLM)
    if any(k in txt for k in ["xin chào", "chào", "hello", "hi"]):
        resp = ("Chào bạn! Mình là trợ lý du lịch. "
                "Bạn muốn tìm hiểu địa điểm hay lên kế hoạch chuyến đi nào không?")
    # 2) ngoài du lịch → từ chối nhẹ
    elif any(k in txt for k in ["chứng khoán","coin","crypto","bất động sản","lập trình","ai model"]):
        resp = ("Mình là trợ lý du lịch, nên chỉ có thể hỗ trợ thông tin, tư vấn liên quan đến du lịch thôi nhé. "
                "Nếu bạn cần gợi ý địa điểm, lịch trình, khách sạn hay cách di chuyển, mình sẵn sàng giúp! 🌏")
    # 3) còn lại → gọi SerpAPI (nếu có) + LLM chung
    else:
        # serp = _serpapi_search(user_text, num=5)
        # if serp:
        #     lines = []
        #     for r in serp[:3]:
        #         line = f"- {r.get('title','')}: {r.get('snippet','')}"
        #         if r.get('link'):
        #             line += f" ({r['link']})"
        #         lines.append(line)
        #     serp_ctx = "\n".join(lines)
        #     rules = _RULES + "\n\nSERP_CONTEXT:\n" + serp_ctx
        # else:
        rules = _RULES
        resp =  await call_llm_rule_user(rules, user_text)

    state["messages"] = messages + [AIMessage(content=resp)]
    state["current_step"] = "responded"
    return state
