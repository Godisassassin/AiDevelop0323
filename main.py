import asyncio
from manualcontrolAgent import run_agent as run_manual_agent
from checkpointerAgent import run_agent as run_checkpointer_agent

def selectmode():
        
    try:
        input_mode = input("请选择控制模式 (1: 手动控制, 2: checkpointer控制): ")
        if input_mode == "1":
            asyncio.run(run_manual_agent())
        elif input_mode == "2":
             asyncio.run(run_checkpointer_agent())
        else:
            print("无效选择，默认使用手动控制模式。")
            return "manual"
    except KeyboardInterrupt:
        print("\n程序被中断")

if __name__ == "__main__":
    selectmode()

