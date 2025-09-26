import asyncio
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

_CLIENT = None

def _make_client_sync():
    key = os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_GENAI_API_KEY")
    if not key:
        raise RuntimeError("GOOGLE_API_KEY is missing")
    return ChatGoogleGenerativeAI(
        model=os.getenv("TRAVEL_BOT_MODEL", "gemini-1.5-flash"),
        temperature=0.2,
        api_key=key,
    )

def get_llm():
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = _make_client_sync()
    return _CLIENT

async def call_llm(msg):
    llm = get_llm()
    # chạy llm.invoke trong thread pool
    result = await asyncio.to_thread(llm.invoke, msg)
    return result.content

async def call_llm_rule_user(rule: str, user_text: str):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "{rules}"),
        ("human", "{user_utterance}")
    ])
    msg = prompt.invoke({
        "rules": (rule or "")[:3000],
        "user_utterance": (user_text or "")[:4000]
    })
    return await call_llm(msg)
