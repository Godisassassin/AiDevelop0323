from langchain.tools import tool
from langchain_anthropic import ChatAnthropic
from langchain_core.agents import AgentExecutor
from langchain import hub

@tool
def get_weather(city: str) -> str:
    return f"{city} 的天气是晴天，25°C。"

@tool
def search_database(query: str) -> str:
    return "找到关于 'Agent 开发' 的 3 条记录。"

tools = [get_weather, search_database]

llm = ChatAnthropic(model="claude-3-5-sonnet-20240620", temperature=0, max_tokens=1024, timeout=30)

# 正确的方式：从 hub 拉取 agent
agent = hub.pull("hwchase17/react-agent")
agent_executor = AgentExecutor(agent=agent, tools=tools)

response = agent_executor.invoke({"input": "北京天气怎么样？"})
print(response["output"])