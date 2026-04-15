<template>
  <div class="app-container">
    <!-- 历史记录区域 -->
    <div class="chat-history" ref="chatHistoryRef">
      <div class="message-list">
        <!-- 消息列表 -->
        <div
          v-for="(msg, index) in messages"
          :key="index"
          :class="['message-item', msg.role]"
        >
          <div class="message-bubble">
            <span class="message-label">{{ msg.role === 'user' ? '你' : 'AI' }}:</span>
            <div class="message-content">
              <span v-if="msg.thinking" class="thinking-text">{{ msg.thinking }}</span>
              <span v-else-if="isThinking && index === messages.length - 1" class="thinking-text">AI正在思考中...</span>
              <span class="response-text">{{ msg.text }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 工具调用确认框 -->
    <div v-if="needsApproval" class="approval-box">
      <p>AI 请求调用工具，是否允许？</p>
      <button @click="resumeMessage" class="approve-btn">批准并继续</button>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
      <div class="input-wrapper">
        <input
          v-model="userInput"
          @keyup.enter="sendMessage('chat')"
          placeholder="输入消息..."
          :disabled="needsApproval"
          class="chat-input"
        />
        <button @click="sendMessage('chat')" :disabled="needsApproval || isThinking" class="send-btn">
          发送
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted } from 'vue';

const messages = ref([]);
const userInput = ref('');
const needsApproval = ref(false);
const threadId = ref('user_123');
const chatHistoryRef = ref(null);
const isThinking = ref(false);
let aiIndex;

const sendMessage = async (action = 'chat') => {
  if (action === 'chat' && !userInput.value) return;

  const currentQuery = userInput.value;
  if (action === 'chat') {
    messages.value.push({ role: 'user', text: currentQuery });
    userInput.value = '';
    scrollToBottom();
  }

  aiIndex = messages.value.push({ role: 'ai', text: '', thinking:'' }) - 1;
  const targetMessage = messages.value[aiIndex];

  try {
    isThinking.value = true
    const res = await fetch('http://localhost:8000/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        user_query: currentQuery,
        thread_id: threadId.value,
      })
    });

    
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while(true){
        const { done, value } = await reader.read();
        if (done) break;
    
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n').filter(line => line.trim() !== '');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '').trim();
                try {
                    const data = JSON.parse(dataStr);
                    if (data.type === 'thinking') {
                        targetMessage.thinking += data.content;
                        scrollToBottom();
                    } 
                    else if (data.type === 'text') {
                        targetMessage.text += data.content;
                        isThinking.value = false
                        needsApproval.value = false;
                    }
                    else if (data.type === 'tool_calls') {
                        isThinking.value = false;
                        needsApproval.value = true;
                    }
                    else if (data.type === 'end') {
                        isThinking.value = false
                        needsApproval.value = false;
                    }
                } 
                catch (e) {
                    console.error("解析数据失败:", e);
                }
            }
        }
    }

    // const data = await res.json();
    // messages.value.push({ role: 'ai', text: data.agent_response });
    // needsApproval.value = data.tool_calls;
    scrollToBottom();
  } catch (error) {
    isThinking.value = false
    console.error("发送失败:", error);
    targetMessage.text += '错误: 无法连接到后端服务';
    scrollToBottom();
  }
};

const resumeMessage = async () => {
  try {
    isThinking.value = true;
    needsApproval.value = false;
    const targetMessage = messages.value[aiIndex];
    const res = await fetch('http://localhost:8000/approve', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        confirm: 'approve',
        thread_id: threadId.value,
      })
    });
        
    const reader = res.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while(true){
        const { done, value } = await reader.read();
        if (done) break;
    
        const chunk = decoder.decode(value);
        const lines = chunk.split('\n\n').filter(line => line.trim() !== '');
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const dataStr = line.replace('data: ', '').trim();
                try {
                    const data = JSON.parse(dataStr);
                    if (data.type === 'thinking') {
                        targetMessage.thinking += data.content;
                        scrollToBottom();
                    } 
                    else if (data.type === 'text') {
                        targetMessage.text += data.content;
                        isThinking.value = false
                        needsApproval.value = false;
                    }
                    else if (data.type === 'tool_calls') {
                        isThinking.value = false;
                        needsApproval.value = true;
                    }
                    else if (data.type === 'end') {
                        isThinking.value = false
                        needsApproval.value = false;
                    }
                } 
                catch (e) {
                    console.error("解析数据失败:", e);
                }
            }
        }
    }

    // const data = await res.json();
    // messages.value.push({ role: 'ai', text: data.agent_response });
    // needsApproval.value = data.tool_calls;
    scrollToBottom();
  } catch (error) {
    console.error("批准失败:", error);
    messages.value.push({ role: 'ai', text: '错误: 批准请求失败' });
    scrollToBottom();
  }
};

const scrollToBottom = () => {
  nextTick(() => {
    if (chatHistoryRef.value) {
      chatHistoryRef.value.scrollTop = chatHistoryRef.value.scrollHeight;
    }
  });
};

onMounted(() => {
  scrollToBottom();
});
</script>

<style scoped>
.app-container {
  width: 100vw;
  height: 100vh;
  background-color: #ffffff;
  display: flex;
  flex-direction: column;
}

.chat-history {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.message-list {
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  gap: 12px;
  max-width: 600px;
  width: 100%;
  margin: 0 auto;
  margin-top: auto; /* 推到底部 */
}

.thinking-indicator {
  font-size: 12px;
  font-style: italic;
  color: #999;
  padding: 8px 0;
}

.message-item {
  display: flex;
  width: 100%;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.ai {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 80%;
  padding: 10px 14px;
  border-radius: 12px;
  word-break: break-word;
}

.message-item.user .message-bubble {
  background-color: #1890ff;
  color: #ffffff;
  border-bottom-right-radius: 4px;
}

.message-item.ai .message-bubble {
  background-color: #f5f5f5;
  color: #333333;
  border-bottom-left-radius: 4px;
}

.message-label {
  font-weight: bold;
  margin-right: 6px;
}

.message-text {
  white-space: pre-wrap;
}

.message-content {
  display: inline;
}

.thinking-text {
  display: block;
  font-size: 12px;
  font-style: italic;
  color: #888;
  margin-bottom: 4px;
}

.response-text {
  display: block;
  font-size: 14px;
  white-space: pre-wrap;
}

.approval-box {
  background: #fff3cd;
  padding: 12px 16px;
  margin: 0 auto 8px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: 600px;
  width: calc(100% - 32px);
}

.approval-box p {
  margin: 0;
  flex: 1;
}

.approve-btn {
  background-color: #52c41a;
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  cursor: pointer;
}

.approve-btn:hover {
  background-color: #73d13d;
}

.input-area {
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  padding: 16px;
  background-color: #ffffff;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.input-wrapper {
  display: flex;
  gap: 8px;
  max-width: 600px;
  width: 100%;
}

.chat-input {
  flex: 1;
  padding: 12px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 8px;
  font-size: 14px;
  outline: none;
  transition: border-color 0.3s;
}

.chat-input:focus {
  border-color: #1890ff;
}

.chat-input:disabled {
  background-color: #f5f5f5;
}

.send-btn {
  padding: 12px 24px;
  background-color: #1890ff;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.send-btn:hover:not(:disabled) {
  background-color: #40a9ff;
}

.send-btn:disabled {
  background-color: #d9d9d9;
  cursor: not-allowed;
}
</style>
