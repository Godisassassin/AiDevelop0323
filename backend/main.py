import os
import sys
import asyncio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI,HTTPException
from pydantic import BaseModel
from typing import List,Optional
from sqlmodel import SQLModel,Session, Field, create_engine, select
from contextlib import asynccontextmanager

# 启动时创建数据表
@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

# 初始化应用
app = FastAPI(title="My Agent API",lifespan=lifespan)

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
        # current_state = await agent.aget_state(config)
        # messages = current_state.values.get("messages", []) 

        # # 将ai回复的数据清洗成简单格式  
        # fixed_messages = []    
        # for msg in messages:
        #     if isinstance(msg, AIMessage) and isinstance(msg.content, list):
        #         # 只提取 text 部分，完全丢弃 thinking 块
        #         clean_text = "".join(
        #             block.get("text", "") 
        #             for block in msg.content 
        #             if block.get("type") == "text"
        #         )
        #         fixed_messages.append(AIMessage(content=clean_text))
        #     else:
        #         fixed_messages.append(msg)
        
        # if fixed_messages:
        #     await agent.aupdate_state(config, {"messages": fixed_messages})
        # # 清洗完成，继续正常调用 Agent
   
        response = await agent.ainvoke(
            {"messages": [("user", request_in.user_query)]}, 
            config=config)
        print("--- Agent 调用成功 ---")

        state = await agent.aget_state(config)
        messages = state.values.get("messages", [])
        print(f"当前状态信息: {messages}")
        if messages:   
            # 这种方式比 hasattr 更安全
            t_calls = getattr(messages[-1], "tool_calls", None)
            if t_calls:
                print(f"检测到工具调用: {t_calls}")


        if "messages" in response:
            agent_response_content =response["messages"][-1].content
            agent_response_texts = [block['text'] for block in agent_response_content if block.get('type') == 'text']
            # agent_response_thinkings = [block['thinking'] for block in agent_response_content if block.get('type') == 'thinking']

        with Session(engine) as session:
            record = ChatRecord(
                user_query=request_in.user_query,
                # agent_thinking=str(agent_response_thinkings),
                agent_response=str(agent_response_texts)
            )
            session.add(record)
            session.commit()
            session.refresh(record)
    except Exception as e:
        print(f"❌ 后端报错详情: {str(e)}")
        # 将错误返回给前端，方便调试
        return {"detail": f"Error inside chat: {str(e)}"}
    return record

@app.post("/approve")
async def approve_tool(request: ApproveRequest):
    config = {"configurable": {"thread_id": request.thread_id}}
    # 传入 None 表示继续执行中断后的逻辑
    result = await agent.ainvoke(Command(resume={"confirm": request.confirm}),  config=config)
    return result

# 获取历史记录接口
@app.get("/history",response_model=List[ChatRecord])
def get_history():
    with Session(engine) as session:
        records = session.exec(select(ChatRecord)).all()
    return records