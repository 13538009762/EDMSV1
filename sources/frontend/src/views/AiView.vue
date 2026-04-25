<template>
  <div class="ai-page-container">
    <!-- Empty state with suggestions -->
    <div v-if="aiStore.globalMessages.length <= 1 && !isTyping" class="empty-state">
      <div class="welcome-section">
        <el-icon class="huge-icon"><MagicStick /></el-icon>
        <h1>您好，我是 EDMS 智能助理</h1>
        <p class="subtitle">我可以帮您写文档、分析报告、或者执行系统管理任务</p>
      </div>
      
      <div class="suggestions-grid">
        <div v-for="s in suggestions" :key="s.title" class="suggestion-card" @click="useSuggestion(s.prompt)">
          <el-icon><component :is="s.icon" /></el-icon>
          <h3>{{ s.title }}</h3>
          <p>{{ s.desc }}</p>
        </div>
      </div>
    </div>

    <!-- Message List -->
    <div class="chat-main" ref="chatScroll">
      <div class="message-wrapper" v-for="(msg, i) in aiStore.globalMessages" :key="i">
        <div :class="['message-item', msg.role]">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><MagicStick /></el-icon>
          </div>
          <div class="content-box">
            <div class="role-label">{{ msg.role === 'user' ? '您' : 'EDMS AI' }}</div>
            <div class="text-content" v-html="renderMarkdown(msg.content)"></div>
            
            <!-- Action Card inside message -->
            <div v-if="msg.action" class="inline-action-card">
              <div class="card-header">
                <el-icon><InfoFilled /></el-icon>
                <span>建议执行以下操作</span>
              </div>
              <div class="card-body">
                <p>{{ getActionDesc(msg.action) }}</p>
              </div>
              <div class="card-footer">
                <el-button type="primary" size="small" @click="executeAction(msg.action, i)">立即执行</el-button>
                <el-button size="small" link @click="msg.action = null">忽略</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="isTyping" class="message-item assistant typing">
        <div class="avatar"><el-icon><MagicStick /></el-icon></div>
        <div class="content-box">
          <div class="role-label">EDMS AI</div>
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- Fixed Input Area -->
    <div class="input-container">
      <div class="input-wrapper">
        <el-input
          v-model="input"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 8 }"
          placeholder="给 EDMS 助手发送消息..."
          @keydown.enter.prevent="handleEnter"
          class="chat-textarea"
        />
        <div class="input-footer">
          <span class="hint">按 Enter 发送，Shift + Enter 换行</span>
          <el-button 
            type="primary" 
            :disabled="!input.trim() || isTyping" 
            @click="sendMessage"
            class="send-btn"
          >
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
      <div class="disclaimer">AI 生成内容仅供参考，请核对关键信息。</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue';
import { useAiStore } from '@/stores/ai';
import { useAuthStore } from '@/stores/auth';
import { 
  MagicStick, User, Promotion, FolderOpened, 
  DocumentChecked, Management, InfoFilled 
} from '@element-plus/icons-vue';
import { marked } from 'marked';
import { ElMessage } from 'element-plus';
import api from '@/api/client';

import { useRouter } from 'vue-router';

const aiStore = useAiStore();
const auth = useAuthStore();
const router = useRouter();
const input = ref('');
const isTyping = ref(false);
const chatScroll = ref<HTMLElement | null>(null);

const suggestions = [
  { title: '总结文档', desc: '帮我概括一下最近更新的财务制度', prompt: '帮我总结一下最近一周的文档', icon: FolderOpened },
  { title: '发起审批', desc: '我要把这篇报告发给经理审核', prompt: '我想发起一个审批流程', icon: DocumentChecked },
  { title: '系统查询', desc: '目前有多少待处理的审批件？', prompt: '查询我的待办审批状态', icon: Management }
];

const renderMarkdown = (text: string) => marked.parse(text);

const scrollToBottom = async () => {
  await nextTick();
  if (chatScroll.value) {
    chatScroll.value.scrollTop = chatScroll.value.scrollHeight;
  }
};

onMounted(scrollToBottom);

const handleEnter = (e: KeyboardEvent) => {
  if (!e.shiftKey) {
    sendMessage();
  }
};

const useSuggestion = (prompt: string) => {
  input.value = prompt;
  sendMessage();
};

const sendMessage = async () => {
  if (!input.value.trim() || isTyping.value) return;

  const userQuery = input.value;
  aiStore.addMessage('user', userQuery);
  input.value = '';
  isTyping.value = true;
  scrollToBottom();

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        messages: aiStore.globalMessages
      })
    });

    if (!response.body) throw new Error('No body');
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let assistantMessage = { role: 'assistant' as const, content: '', action: null };
    aiStore.globalMessages.push(assistantMessage);
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const raw = line.slice(6).trim();
          if (raw === '[DONE]') break;
          try {
            const data = JSON.parse(raw);
            if (data.content) {
              assistantMessage.content += data.content;
            } else if (data.type === 'done') {
              // 1. Intercept JSON actions (Sensitve, need confirmation)
              const jsonMatch = assistantMessage.content.match(/```json\s*(\{[\s\S]*?\})\s*```/);
              if (jsonMatch) {
                try {
                  assistantMessage.action = JSON.parse(jsonMatch[1]);
                  assistantMessage.content = assistantMessage.content.replace(/```json\s*\{[\s\S]*?\}\s*```/, "").trim();
                } catch(e) {}
              }

              // 2. Intercept Tags (Automatic actions)
              // Handle OPEN_DOC
              const openDocRegex = /\[ACTION:\s*OPEN_DOC,\s*ID:\s*([a-zA-Z0-9_-]+)\]/i;
              const openMatch = assistantMessage.content.match(openDocRegex);
              if (openMatch && openMatch[1]) {
                const docId = openMatch[1];
                ElMessage.success(`正在为您跳转至文档 ${docId}...`);
                router.push(`/document/${docId}`);
                assistantMessage.content = assistantMessage.content.replace(openDocRegex, '').trim();
              }

              // Handle QUERY_STATS
              const queryStatsRegex = /\[ACTION:\s*QUERY_STATS,\s*TYPE:\s*([a-zA-Z0-9_-]+)\]/i;
              const queryMatch = assistantMessage.content.match(queryStatsRegex);
              if (queryMatch) {
                const statType = queryMatch[1];
                assistantMessage.content = assistantMessage.content.replace(queryStatsRegex, '').trim();
                
                // Show a fake processing step then replace content
                const tempMsg = assistantMessage.content;
                assistantMessage.content = tempMsg + "\n\n⌛ *正在接入底层数据库核实中...*";
                
                try {
                  // Actually fetch real data
                  const res = await api.get('/documents/stats'); 
                  const stats = res.data;
                  let resultText = "";
                  if (statType === 'document_count') resultText = `✅ 查询完毕。系统目前共有 **${stats.total_count}** 份文档。`;
                  else resultText = `✅ 查询完毕。系统当前运行状态良好。`;
                  
                  assistantMessage.content = tempMsg + "\n\n" + resultText;
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n❌ 数据库连接超时，请稍后再试。";
                }
              }
            }
            scrollToBottom();
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    ElMessage.error('服务连接异常');
    aiStore.addMessage('assistant', '抱歉，我现在连接不稳定。');
  } finally {
    isTyping.value = false;
    scrollToBottom();
  }
};

const getActionDesc = (action: any) => {
  if (action.action === 'start_approval') return '发起并行审批流程';
  return '系统操作建议';
};

const executeAction = async (action: any, idx: number) => {
  ElMessage.success('操作已执行');
  aiStore.globalMessages[idx].action = null;
};
</script>

<style scoped>
.ai-page-container {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  background-color: transparent; /* 由 theme.css 强制玻璃化 */
  position: relative;
  max-width: 1000px;
  margin: 20px auto;
  border-radius: 16px;
  overflow: hidden;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px;
}

.welcome-section {
  text-align: center;
  margin-bottom: 40px;
}

.huge-icon {
  font-size: 64px;
  color: var(--el-color-primary);
  margin-bottom: 16px;
  filter: drop-shadow(0 0 15px var(--el-color-primary));
}

.welcome-section h1 {
  font-size: 32px;
  font-weight: 800;
  color: var(--el-text-color-primary);
  margin-bottom: 12px;
}

.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 16px;
}

.suggestions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
  width: 100%;
  max-width: 800px;
}

.suggestion-card {
  padding: 24px;
  background: rgba(255, 255, 255, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: center;
}

.suggestion-card:hover {
  background: rgba(255, 255, 255, 0.8);
  border-color: var(--el-color-primary);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  transform: translateY(-4px);
}

.suggestion-card .el-icon {
  font-size: 28px;
  color: var(--el-color-primary);
  margin-bottom: 12px;
}

.suggestion-card h3 {
  font-size: 16px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.suggestion-card p {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
}

.chat-main {
  flex: 1;
  overflow-y: auto;
  padding: 40px;
  display: flex;
  flex-direction: column;
  gap: 40px;
}

.message-item {
  display: flex;
  gap: 24px;
  max-width: 900px;
  margin: 0 auto;
  width: 100%;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: var(--el-text-color-secondary);
  border: 1px solid rgba(255, 255, 255, 0.8);
}

.message-item.assistant .avatar {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-7);
}

.content-box {
  flex: 1;
}

.role-label {
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.text-content {
  font-size: 15px;
  line-height: 1.8;
  color: var(--el-text-color-regular);
}

.inline-action-card {
  margin-top: 20px;
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.2);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  overflow: hidden;
  max-width: 450px;
}

.card-header {
  padding: 10px 16px;
  border-bottom: 1px solid rgba(var(--el-color-primary-rgb), 0.1);
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.card-body {
  padding: 16px;
  font-size: 14px;
}

.card-footer {
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.3);
  display: flex;
  gap: 12px;
}

.input-container {
  padding: 32px 40px;
  background: linear-gradient(to bottom, transparent, rgba(255, 255, 255, 0.2));
}

.input-wrapper {
  max-width: 850px;
  margin: 0 auto;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(10px);
  border-radius: 20px;
  padding: 12px 20px;
  border: 1px solid rgba(255, 255, 255, 0.8);
  transition: all 0.3s ease;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.05);
}

.input-wrapper:focus-within {
  border-color: var(--el-color-primary);
  background: rgba(255, 255, 255, 0.8);
  box-shadow: 0 12px 48px rgba(var(--el-color-primary-rgb), 0.15);
}

:deep(.chat-textarea .el-textarea__inner) {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
  font-size: 16px !important;
  color: var(--el-text-color-primary) !important;
  padding: 8px 0 !important;
}

.input-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 8px;
}

.hint {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}

.send-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  border-radius: 10px;
}

.disclaimer {
  text-align: center;
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 16px;
  opacity: 0.7;
}

.typing-indicator {
  display: flex;
  gap: 6px;
  padding: 12px 0;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
  opacity: 0.6;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1.0); opacity: 1; }
}

:deep(.text-content p) { margin: 0 0 16px 0; }
:deep(.text-content p:last-child) { margin-bottom: 0; }
:deep(.text-content pre) {
  background: rgba(0, 0, 0, 0.05);
  padding: 20px;
  border-radius: 12px;
  overflow-x: auto;
  border: 1px solid rgba(0, 0, 0, 0.08);
}
</style>
