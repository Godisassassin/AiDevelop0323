import os
import sys
import asyncio
import json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI,HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List,Optional,Any
from sqlmodel import SQLModel,Session, Field, create_engine, select
from contextlib import asynccontextmanager

# 启动时创建数据表
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# 初始化应用
app = FastAPI(title="My Agent API",lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["*"],  # 确保包含 "OPTIONS" 和 "POST"
    allow_headers=["*"],
)

# 定义数据模型（模拟前端发来的数据格式）
class ChatRequest(BaseModel):
    user_query: str
    thread_id: str

class ApproveRequest(BaseModel):
    thread_id: str
    confirm: str

# 定义数据库模型
class ChatRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_query: str
    # agent_thinking: str
    agent_response: str
    tool_calls : bool

# 数据库连接设置
sqlite_file_name = "database.db"
sqlitee_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlitee_url, connect_args={"check_same_thread": False})

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)



# --- 接口部分 ---

from agent_core.checkpointerAgent import agent,Command
from langchain_core.messages import AIMessage


# kind（事件类型）汇总：
# 1.模型层
# - on_chat_model_start: 模型开始接收输入
# - on_chat_model_stream：模型生成新 token 时触发，包含增量内容
# - on_chat_model_end: 模型生成完毕，此时可以拿到总消耗的 Token 数
# 2.工具层
# - on_tool_start: 工具开始执行
# - on_tool_end: 工具执行结束
# 3.编排层
# - on_chain_start: 整个 Graph 启动，或者某个 Node（节点）启动。
# - on_chain_stream: Graph 内部有新的输出时触发，包含增量内容。比如某个 Node 有新的输出，或者工具调用结果出来了等。
# - on_chain_end: 整个 Graph 结束，或者某个 Node 结束。Node 的 on_chain_end 事件中会包含该 Node 的输出结果，可以用来判断工具调用结果等。
# 4. 原始层 (Retriever/Parser) —— 底层处理
# - on_retriever_start: 检索开始
# - on_retriever_end: 检索结束
# - on_parser_start: 解析开始
# - on_parser_end: 解析结束

# 核心接口：接收用户输入并返回 Agent 的回复
@app.post("/chat")
async def chat(request: ChatRequest):
    config = {"configurable": {"thread_id": f"{request.thread_id}"}}
    try:     
        async def event_generator():
            async for event in agent.astream_events(
                {"messages": [("user", request.user_query)]}, 
                config, 
                version="v2"
            ):
                kind = event.get("event")
                print(f"🔔 事件类型: {kind}, 事件内容: {event}")

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        for data in content:
                            if data.get("type") == "text" and data.get("text"):
                                 # SSE 格式要求以 "data: " 开头，以 "\n\n" 结尾
                                yield f"data: {json.dumps({'type': 'text', 'content': data.get('text')})}\n\n"
                            if data.get("type") == "thinking" and data.get("thinking"):
                                yield f"data: {json.dumps({'type': 'thinking', 'content': data.get('thinking')})}\n\n"
                elif kind == "on_chain_end" and event["name"] == "LangGraph":
                    with Session(engine) as session:
                        record = ChatRecord(
                            user_query=request.user_query,
                            agent_response=datahandler(event["data"]),
                            tool_calls=any(
                                hasattr(msg, "tool_calls") and msg.tool_calls 
                                for msg in event["data"].get("output", {}).get("messages", [])
                            )
                        )
                        session.add(record)
                        session.commit()
                        session.refresh(record)
                    messages = event["data"].get("output", {}).get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            yield f"data: {json.dumps({'type': 'tool_calls'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'end'})}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"❌ 后端报错详情: {str(e)}")
        # 将错误返回给前端，方便调试
        return {"detail": f"Error inside chat: {str(e)}"}

@app.post("/approve")
async def approve_tool(request: ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    try:     
        async def event_generator():
            async for event in agent.astream_events(
                Command(resume = {"confirm":request.confirm}), 
                config, 
                version="v2"
            ):
                kind = event.get("event")
                print(f"🔔 事件类型: {kind}, 事件内容: {event}")

                if kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                        for data in content:
                            if data.get("type") == "text" and data.get("text"):
                                 # SSE 格式要求以 "data: " 开头，以 "\n\n" 结尾
                                yield f"data: {json.dumps({'type': 'text', 'content': data.get('text')})}\n\n"
                            if data.get("type") == "thinking" and data.get("thinking"):
                                yield f"data: {json.dumps({'type': 'thinking', 'content': data.get('thinking')})}\n\n"
                elif kind == "on_chain_end" and event["name"] == "LangGraph":
                    messages = event["data"].get("output", {}).get("messages", [])
                    with Session(engine) as session:
                        record = ChatRecord(
                            user_query="Tool Call Approval: " + request.confirm,
                            agent_response=datahandler(event["data"]),
                            tool_calls=any(
                                hasattr(msg, "tool_calls") and msg.tool_calls 
                                for msg in event["data"].get("output", {}).get("messages", [])
                            )
                        )
                        session.add(record)
                        session.commit()
                        session.refresh(record)
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                            yield f"data: {json.dumps({'type': 'tool_calls'})}\n\n"
                        else:
                            yield f"data: {json.dumps({'type': 'end'})}\n\n"
                    else:
                        yield f"data: {json.dumps({'type': 'end'})}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"❌ 后端报错详情: {str(e)}")
        # 将错误返回给前端，方便调试
        return {"detail": f"Error inside chat: {str(e)}"}          

def datahandler(data:dict[str,Any]|Any)->str:
    if "messages" in data:
        agent_response_content =data["messages"][-1].content
        agent_response_texts = [block['text'] for block in agent_response_content if block.get('type') == 'text']
        # agent_response_thinkings = [block['thinking'] for block in agent_response_content if block.get('type') == 'thinking']
        return ' '.join(agent_response_texts)
    return ""        
    

# 获取历史记录接口
@app.get("/history",response_model=List[ChatRecord])
def get_history():
    with Session(engine) as session:
        records = session.exec(select(ChatRecord)).all()
    return records