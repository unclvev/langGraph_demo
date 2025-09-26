from demoLangGraph.travel_bot.graph import create_travel_bot
from dotenv import load_dotenv
from demoLangGraph.rule_agent.llm_client import get_llm
from demoLangGraph.tool_based_agent_handoff.graph import (create_true_tool_handoff_bot,
                                                          create_advanced_handoff_bot,
                                                          create_simple_handoff_bot)

load_dotenv()
llm = get_llm()

# app = create_travel_bot()
app = create_true_tool_handoff_bot(llm)
print("=== GRAPH NODES ===")
print(app.get_graph().nodes)
