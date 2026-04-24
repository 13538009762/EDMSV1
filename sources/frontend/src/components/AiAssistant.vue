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
            @keyup.enter.native.prevent="sendMessage"
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
import { useAiStore } from '@/stores/ai';
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
    let assistantMessage = { role: 'assistant', content: '' };
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
.ai-sidebar-container {
  margin: 10px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  overflow: hidden;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
}

.ai-sidebar-container.collapsed {
  margin: 10px 4px;
  background: transparent;
  border: none;
  align-items: center;
}

.ai-header {
  padding: 10px 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.05);
  transition: background 0.2s;
}

.ai-header:hover {
  background: rgba(255, 255, 255, 0.1);
}

.title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
}

.magic-icon {
  font-size: 18px;
  filter: drop-shadow(0 0 5px var(--el-color-primary));
}

.expand-icon {
  font-size: 12px;
  color: #909399;
}

.ai-body {
  height: 300px;
  display: flex;
  flex-direction: column;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  background: rgba(0, 0, 0, 0.1);
}

/* Scrollbar styling for chat */
.chat-messages::-webkit-scrollbar {
  width: 4px;
}
.chat-messages::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.1);
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

.bubble {
  padding: 8px 12px;
  border-radius: 12px;
  font-size: 12px;
  line-height: 1.5;
  background: rgba(255, 255, 255, 0.08);
  color: #e5eaf3;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.message.user .bubble {
  background: var(--el-color-primary);
  color: white;
}

.chat-input-area {
  padding: 8px;
  display: flex;
  gap: 8px;
  align-items: flex-end;
  background: rgba(255, 255, 255, 0.03);
}

:deep(.el-textarea__inner) {
  background: rgba(0, 0, 0, 0.2) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
  font-size: 12px !important;
  padding: 4px 8px !important;
}

.typing-dot {
  width: 4px;
  height: 4px;
  background: #aaa;
  border-radius: 50%;
  animation: typing 1s infinite alternate;
}

@keyframes typing {
  from { opacity: 0.3; }
  to { opacity: 1; }
}

.expand-enter-active, .expand-leave-active {
  transition: all 0.3s ease;
  max-height: 400px;
}
.expand-enter-from, .expand-leave-to {
  max-height: 0;
  opacity: 0;
}

:deep(.content p) { margin: 0 0 6px 0; }
:deep(.content p:last-child) { margin-bottom: 0; }
:deep(.content pre) { 
  background: #282c34; 
  padding: 6px; 
  border-radius: 4px; 
  overflow-x: auto;
  font-size: 11px;
}
</style>
