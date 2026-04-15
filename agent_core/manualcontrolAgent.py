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

# 确保模型版本支持工具调用
llm = ChatAnthropic(
    model="claude-3-5-sonnet-20240620", # 或者使用最新的 "claude-4-sonnet"
    temperature=0,
    max_tokens=1024,
    timeout=None,
    max_retries=2,
    # anthropic_api_key="..." # 也可以在这里显式传入
)

from langchain.agents import create_agent 
from langchain.agents.middleware import AgentMiddleware
# from langgraph.checkpoint.memory import MemorySaver
# from langgraph.types import Command

# memory : MemorySaver = MemorySaver() # 这里可以配置你的存储方式，比如本地文件系统、数据库等

class MyCustomGuardrail(AgentMiddleware):
    def before_agent(self, input_data):
        # 在 Agent 运行前检查输入是否包含敏感词
        print("正在进行安全合规检查...")
        return input_data
# 挂载中间件
agent = create_agent (
    llm, 
    tools=tools, 
    middleware=[MyCustomGuardrail()],
    # interrupt_before=["tools"], # 在调用工具前中断，等待人工确认
    # checkpointer=memory
    )

config = {"configurable": {"thread_id": "user_123"}}

MAX_TURNS : int = 5

conversation_history : list[tuple[str, str]]= []

async def run_agent():
    while True:
            global conversation_history
            full_response = ""
            # 假设你的 agent 已经定义好
            try:
                user_input = input("\n你: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n再见！")
                break
            if user_input.lower() in ["quit", "退出"]:
                print("再见！")
                break
            conversation_history.append(("user", user_input))

            inputs = {"messages": conversation_history}

            # 方式 A：一次性获取结果
            # response = agent.invoke(inputs)
            # print(response["messages"][-1].content)
            # print(response.keys()) 

            # 方式 B：流式输出（像 ChatGPT 那样一个字一个字出来，2026年主流用法）
            async for chunk in agent.astream(inputs, config=config):
                print(f"收到 chunk: {chunk.keys() if isinstance(chunk, dict) else type(chunk)}")
                print(chunk)
                
                # 从 chunk 里找 AI 的回复文本
                if 'model' in chunk:
                    print(f"  model keys: {chunk['model'].keys()}")
                    messages = chunk['model'].get('messages', [])
                    print(f"  messages 数量: {len(messages)}")
                    model_data = chunk['model']
                    if 'messages' in model_data:
                        messages = model_data['messages']
                        for msg in model_data['messages']:
                            print(f"    msg type: {msg.type}, content: {msg.content[:100] if hasattr(msg, 'content') else 'N/A'}")
                            if hasattr(msg, 'tool_calls') and msg.tool_calls:
                                tool_name = msg.tool_calls[0]['name']
                                tool_args = msg.tool_calls[0]['args']
                        
                                # 弹出确认框
                                confirm = input(f"\n🛑 即将执行工具: {tool_name}\n参数: {tool_args}\n确认执行? (y/n): ")
                                if confirm.lower() != 'y':
                                    print("已取消本次工具调用")
                                    # 跳过本次 agent.astream 调用
                                    break
                        # 找最后一条 AI 消息
                        for msg in reversed(messages):
                            if hasattr(msg, 'content') and msg.type == 'ai':
                                # content 可能是列表
                                content = msg.content
                                if isinstance(content, list):
                                    for item in content:
                                        if isinstance(item, dict) and item.get('type') == 'text':
                                            full_response = item['text']
                                else:
                                    full_response = str(content)
                                break
                        if full_response:
                            print(f"找到回复: {full_response}")
                            break
                        else:
                            print("本轮未找到AI回复，继续...")  # 加这行看是否走到这里
            conversation_history.append(("ai", full_response))
            # state = agent.get_state(config)

            # while state.next:        
            #     # 模拟人工介入：你可以修改数据，或者只是单纯敲个回车确认
            #     user_feedback = input("请输入您的指令（直接回车表示允许 Agent 继续总结，或输入新的要求）：")
                
            #     resume_value = user_feedback if user_feedback.strip() else "yes"

            #     # 3. 恢复运行
            #     # resume 传 None 表示“按原计划继续”，传字符串表示“给 Agent 的补充指令”
            #     for chunk in agent.stream(Command(resume=resume_value), config=config):
            #         print(chunk)
            #     state = agent.get_state(config)

            if len(conversation_history) > MAX_TURNS * 2:
                conversation_history = conversation_history[-MAX_TURNS * 2:]
