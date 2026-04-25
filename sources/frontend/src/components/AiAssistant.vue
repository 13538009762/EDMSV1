<template>
  <div class="ai-sidebar-container" :class="{ 'collapsed': isSidebarCollapsed }">
    <div class="ai-header" @click="toggleExpand">
      <div class="title-wrap">
        <el-icon class="magic-icon"><MagicStick /></el-icon>
        <span v-if="!isSidebarCollapsed">AI 智能助理</span>
      </div>
      <el-icon v-if="!isSidebarCollapsed" class="expand-icon">
        <component :is="isExpanded ? ArrowDown : ArrowUp" />
      </el-icon>
    </div>

    <transition name="expand">
      <div v-if="isExpanded && !isSidebarCollapsed" class="ai-body">
        <div class="chat-messages" ref="scrollContainer">
          <div v-for="(msg, i) in aiStore.globalMessages" :key="i" :class="['message', msg.role]">
            <div class="bubble">
              <div class="content" v-html="renderMarkdown(msg.content)"></div>
            </div>
          </div>
          <div v-if="isTyping" class="message assistant">
            <div class="bubble"><div class="typing-dot"></div></div>
          </div>
        </div>

        <div class="chat-input-area">
          <el-input
            v-model="input"
            type="textarea"
            :rows="2"
            placeholder="问问 AI..."
            @keyup.enter.prevent="sendMessage"
            resize="none"
          />
          <el-button type="primary" size="small" :loading="isTyping" @click="sendMessage" circle>
            <el-icon><Promotion /></el-icon>
          </el-button>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, watch } from 'vue';
import { useRoute } from 'vue-router';
import { MagicStick, ArrowUp, ArrowDown, Promotion } from '@element-plus/icons-vue';
import { useAuthStore } from '@/stores/auth';
import { useAiStore, type AiMessage } from '@/stores/ai';
import { marked } from 'marked';

const props = defineProps({
  isSidebarCollapsed: Boolean
});

const route = useRoute();
const auth = useAuthStore();
const aiStore = useAiStore();
const input = ref('');
const isTyping = ref(false);
const isExpanded = ref(true);
const scrollContainer = ref<HTMLElement | null>(null);

const toggleExpand = () => {
  if (props.isSidebarCollapsed) return;
  isExpanded.value = !isExpanded.value;
};

const renderMarkdown = (text: string) => {
  return marked.parse(text);
};

const scrollToBottom = async () => {
  await nextTick();
  if (scrollContainer.value) {
    scrollContainer.value.scrollTop = scrollContainer.value.scrollHeight;
  }
};

onMounted(scrollToBottom);

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
        messages: aiStore.globalMessages,
        context_url: route.path
      })
    });

    if (!response.body) throw new Error('No body');
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    const assistantMessage: AiMessage = { role: 'assistant', content: '' };
    aiStore.globalMessages.push(assistantMessage);
    
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value);
      const lines = chunk.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const dataStr = line.slice(6);
          if (dataStr === '[DONE]') break;
          try {
            const data = JSON.parse(dataStr);
            assistantMessage.content += data.content;
            scrollToBottom();
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    console.error('Chat error:', error);
    aiStore.addMessage('assistant', '抱歉，我现在无法响应您的请求。');
  } finally {
    isTyping.value = false;
    scrollToBottom();
  }
};
</script>

<style scoped>
/* ==========================================
   AI 智能助手：全息悬浮毛玻璃 (HUD 质感)
========================================== */

/* 1. 外层主容器：比文档库更通透，强化悬浮感 */
.ai-sidebar-container {
  margin: 10px;
  /* 使用 60% 的白，比表格更透一点，科技感直接拉满 */
  background-color: rgba(255, 255, 255, 0.6) !important; 
  backdrop-filter: blur(30px) !important; /* 增加模糊度，让背后的光晕彻底化开 */
  -webkit-backdrop-filter: blur(30px) !important;
  
  border: 1px solid rgba(255, 255, 255, 0.7) !important;
  border-radius: 16px !important; 
  box-shadow: 0 16px 40px rgba(31, 38, 135, 0.1) !important;
  
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.ai-sidebar-container.collapsed {
  margin: 10px 4px;
  background: transparent !important;
  border: none !important;
  backdrop-filter: none !important;
  box-shadow: none !important;
  align-items: center;
}

.ai-header {
  padding: 12px 16px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.2);
  transition: background 0.2s;
  border-bottom: 1px solid rgba(255, 255, 255, 0.3);
}

.ai-header:hover {
  background: rgba(255, 255, 255, 0.3);
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: var(--el-color-primary);
}

.magic-icon {
  font-size: 20px;
  filter: drop-shadow(0 0 8px var(--el-color-primary));
}

.expand-icon {
  font-size: 14px;
  color: var(--el-text-color-secondary);
}

.ai-body {
  height: 420px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  background: rgba(0, 0, 0, 0.02);
}

.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.1);
  border-radius: 2px;
}

.message {
  display: flex;
  flex-direction: column;
  max-width: 90%;
}

.message.assistant {
  align-self: flex-start;
}

.message.user {
  align-self: flex-end;
}

/* 4. AI 的聊天气泡：带上微弱的磨砂感 */
.bubble {
  padding: 10px 14px;
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  background-color: rgba(255, 255, 255, 0.7) !important;
  backdrop-filter: blur(10px) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
  color: var(--el-text-color-primary) !important;
}

.message.user .bubble {
  background: var(--el-color-primary) !important;
  color: white !important;
  border: none !important;
  backdrop-filter: none !important;
}

/* 2. 底部输入区域：果冻质感的底座 */
.chat-input-area {
  padding: 16px;
  display: flex;
  gap: 12px;
  align-items: flex-end;
  background-color: rgba(255, 255, 255, 0.4) !important; 
  border-top: 1px solid rgba(255, 255, 255, 0.5) !important;
  border-radius: 0 0 16px 16px !important;
}

/* 3. 砸穿 Element Plus 输入框的死白底色 */
:deep(.el-textarea__inner) {
  background-color: rgba(255, 255, 255, 0.5) !important; 
  border: 1px solid rgba(255, 255, 255, 0.6) !important;
  color: var(--el-text-color-primary) !important;
  box-shadow: none !important;
  transition: all 0.3s ease !important;
  font-size: 13px !important;
  border-radius: 12px !important;
}

:deep(.el-textarea__inner:focus) {
  background-color: rgba(255, 255, 255, 0.8) !important;
  border-color: var(--el-color-primary) !important;
  box-shadow: 0 0 0 2px rgba(37, 99, 235, 0.2) !important; 
}

.typing-dot {
  width: 6px;
  height: 6px;
  background: var(--el-color-primary);
  border-radius: 50%;
  animation: typing 1s infinite alternate;
}

@keyframes typing {
  from { opacity: 0.3; transform: scale(0.8); }
  to { opacity: 1; transform: scale(1.2); }
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}

:deep(.content p) { margin: 0 0 8px 0; }
:deep(.content p:last-child) { margin-bottom: 0; }
:deep(.content pre) { 
  background: rgba(0, 0, 0, 0.05); 
  padding: 10px; 
  border-radius: 8px; 
  overflow-x: auto;
  font-size: 12px;
}
</style>
