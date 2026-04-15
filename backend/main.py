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

# 核心接口：接收用户输入并返回 Agent 的回复
@app.post("/chat")
async def chat(request_in: ChatRequest):
    config = {"configurable": {"thread_id": f"{request_in.thread_id}"}}
    try:     
        async def event_generator():
            async for event in agent.astream_events(
                {"messages": [("user", request_in.user_query)]}, 
                config, 
                version="v2"
            ):
                kind = event.get("event")

                if kind == "agent_thought":
                    thinking = event.get("thinking", "")
                    yield f"data: {thinking}\n\n"
                elif kind == "on_chat_model_stream":
                    content = event["data"]["chunk"].content
                    if content:
                    # SSE 格式要求以 "data: " 开头，以 "\n\n" 结尾
                        yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
                elif kind == "on_chain_end" and event["name"] == "LangGraph":
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"
        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        print(f"❌ 后端报错详情: {str(e)}")
        # 将错误返回给前端，方便调试
        return {"detail": f"Error inside chat: {str(e)}"}

@app.post("/approve")
async def approve_tool(request: ApproveRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        # 传入 None 表示继续执行中断后的逻辑
        response = await agent.astream(Command(resume={"confirm": request.confirm}),  config=config)
    
        state = await agent.aget_state(config)
        messages = state.values.get("messages", [])
        agent_response = datahandler(response)

        with Session(engine) as session:
            record = ChatRecord(
            user_query=f"Tool approval: {request.confirm}",
            # agent_thinking=str(agent_response_thinkings),
            agent_response=agent_response,
            tool_calls=False
        )
        session.add(record)
        session.commit()
        session.refresh(record)  
    except Exception as e:       
        print(f"❌ 后端报错详情: {str(e)}")
        # 将错误返回给前端，方便调试
        return {"detail": f"Error inside chat: {str(e)}"}
    return record

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