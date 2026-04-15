import os
import asyncio
import httpx
from dotenv import load_dotenv

# 这一步会搜索 .env 文件并将其内容注入到 os.environ 中
load_dotenv()

# 现在可以像获取普通环境变量一样获取它
api_key = os.getenv("ANTHROPIC_API_KEY")

from langchain.tools import tool


WMO_CODE_MAP = {
    0: "Clear sky (晴朗)",
    1: "Mainly clear (大部晴朗)",
    2: "Partly cloudy (多云)",
    3: "Overcast (阴天)",
    45: "Fog (雾)",
    48: "Depositing rime fog (雾凇)",
    51: "Light drizzle (毛毛细雨)",
    61: "Slight rain (小雨)",
    63: "Moderate rain (中雨)",
    65: "Heavy rain (大雨)",
    71: "Slight snow fall (小雪)",
    73: "Moderate snow fall (中雪)",
    75: "Heavy snow fall (大雪)",
    95: "Thunderstorm (雷阵雨)",
}

async def get_weather1(city: str) -> str:
    try:
        async with httpx.AsyncClient() as client:
        # 1. 地名解析
            geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
            geo_resp = await client.get(geo_url)
            geo_data = geo_resp.json()

            if not geo_data.get("results"):
                return "未找到城市"

            result = geo_data["results"][0]
            lat, lon = result["latitude"], result["longitude"]

            # 2. 获取天气
            weather_url = "https://api.open-meteo.com/v1/forecast"
            params = {"latitude": lat, "longitude": lon, "current_weather": True}
            weather_resp = await client.get(weather_url, params=params)
            current = weather_resp.json()["current_weather"]
            weather_desc = WMO_CODE_MAP.get(current["weathercode"], f"Unknown (Code: {current['weathercode']})")

            return {
                "location": result["name"],
                "country": result.get("country"),
                "temperature": f"{current['temperature']}°C",
                "windspeed": f"{current['windspeed']} m/s",
                "description": weather_desc,
                "time": current['time']
            }
    except Exception as e:
        return f"API1 请求失败: {str(e)}"

async def get_weather2(city: str) -> str:
    # 这里接入实际的 API
    await asyncio.sleep(20)
    return f"[API2] {city} 的天气是晴天，25°C。"

@tool
async def fetch_weather(city: str) -> str:
    """查询天气，自动选用最快返回的API，但要注意city为英文城市名，如上海:。"""
    task1 = asyncio.create_task(get_weather1(city))
    task2 = asyncio.create_task(get_weather2(city))

    done, pending = await asyncio.wait(
        [task1, task2],
        return_when=asyncio.FIRST_COMPLETED
    )

    # 取消还未完成的任务
    for task in pending:
        task.cancel()

    # 获取已完成任务的结果
    winner = done.pop()
    return winner.result()

@tool
def search_database(query: str) -> str:
    """在公司内部数据库中搜索相关文档。"""
    return "找到关于 'Agent 开发' 的 3 条记录。"

tools = [fetch_weather, search_database]

from langchain_anthropic import ChatAnthropic

# # 确保模型版本支持工具调用
# llm = ChatAnthropic(
#     model="claude-3-5-sonnet-latest", # 或者使用最新的 "claude-4-sonnet"
#     # model="MiniMax-M2.7",
#     temperature=0,
#     max_tokens=1024,
#     timeout=None,
#     max_retries=2,
#     # anthropic_api_key="..." # 也可以在这里显式传入
# )

from typing_extensions import TypedDict
from typing import Annotated, Sequence
from langchain.agents import create_agent 
from langchain.agents.middleware import AgentMiddleware
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from langgraph.types import Command
from langchain_core.messages import BaseMessage

memory : MemorySaver = MemorySaver() # 这里可以配置你的存储方式，比如本地文件系统、数据库等

def manage_memory_reducer(left: list, right: list) -> list:
    # 使用官方的 add_messages 合并新旧消息
    all_messages = add_messages(left, right)
    
    # 逻辑：只保留最后 10 条（5 轮对话）
    # 注意：如果第一条是 SystemMessage，建议特殊处理保留它
    if len(all_messages) > 10:
        return all_messages[-10:]
    return all_messages

class AgentState(TypedDict):
    # 关键：这里指定使用你定义的 manage_memory_reducer
    messages: Annotated[Sequence[BaseMessage], manage_memory_reducer]

class MyCustomGuardrail(AgentMiddleware):
    def before_agent(self, input_data):
        # 在 Agent 运行前检查输入是否包含敏感词
        print("正在进行安全合规检查...")
        return input_data
# 挂载中间件
agent = create_agent (
    # model="claude-3-5-sonnet-20240620",
    model="anthropic:claude-sonnet-4-6",
    tools=tools, 
    middleware=[MyCustomGuardrail()],
    interrupt_before=["tools"], # 在调用工具前中断，等待人工确认
    checkpointer=memory,
    state_schema=AgentState
    )


if __name__ == "__main__":
    config = {"configurable": {"thread_id": "user_123"}}

    async def run_agent():
        while True:
            try:
                user_input = input("请输入你的问题 (输入 'exit' 退出): ")
                if user_input.lower() == "exit":
                    print("退出程序。")
                    break
                inputs = {"messages": [("user", user_input)]}
                async for chunk in agent.astream(inputs, config=config):
                    print(chunk)
                    if'__interrupt__' in chunk:
                        confirm = input("🛑 即将执行工具，确认继续? (直接回车确认，输入 'n' 取消): ")
                        if confirm.lower() == 'n':
                            print("已取消")
                            break
                        async for chunk in agent.astream(Command(resume=confirm), config=config):
                            print(chunk)
                        state = agent.get_state(config)
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
    asyncio.run(run_agent())
