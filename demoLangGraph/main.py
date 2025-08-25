from demoLangGraph.travel_bot.graph import create_travel_bot
from dotenv import load_dotenv

load_dotenv()
app = create_travel_bot()
# app.invoke("du lich ha noi 3 ngay 2 dem")


# if __name__ == '__main__':
#     result = app.invoke({"messages": [{"type": "human", "content": "du lich ha noi 3 nay 2 dem"}]})
#     result = app.invoke({"messages": [{"type": "human", "content": "du lich ha noi 10 nay 2 dem"}]})
#     print("Final state:", result)