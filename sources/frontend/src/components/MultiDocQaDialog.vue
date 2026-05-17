<template>
  <el-dialog
    v-model="visible"
    :title="t('library.multiDocQa')"
    width="600px"
    @closed="onClosed"
  >
    <div class="qa-container">
      <div class="qa-header">
        <div class="selected-docs">
          <span class="label">{{ t('library.selectedDocs') }}：</span>
          <el-tag 
            v-for="doc in displayDocs" 
            :key="doc.id" 
            size="small" 
            class="doc-tag"
            :title="doc.title"
          >
            {{ doc.doc_number || ('ID: ' + doc.id) }}
          </el-tag>
        </div>
        <div class="model-selector">
          <span class="label">{{ t('library.useModel') }}：</span>
          <el-select v-model="aiStore.selectedModel" size="small" style="width: 130px">
            <el-option label="Spark Lite" value="spark-lite" />
            <el-option label="DeepSeek Chat" value="deepseek" />
          </el-select>
        </div>
      </div>

      <div class="chat-area" ref="chatArea">
        <div v-for="(msg, index) in messages" :key="index" :class="['chat-bubble', msg.role]">
          <div v-if="msg.role === 'assistant'" class="markdown-body" v-html="renderMarkdown(msg.content)"></div>
          <div v-else class="text-body">{{ msg.content }}</div>
        </div>
        <div v-if="loading" class="chat-bubble assistant typing">
          <span class="dot"></span><span class="dot"></span><span class="dot"></span>
        </div>
      </div>

      <div class="input-area">
        <el-input
          v-model="query"
          type="textarea"
          :rows="2"
          :placeholder="t('library.multiDocQaPlaceholder')"
          @keydown.enter.prevent="askQuestion"
        />
        <el-button type="primary" :icon="ChatDotRound" @click="askQuestion" :loading="loading" class="send-btn">{{ t('common.send') }}</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick, computed } from 'vue';
import { useI18n } from 'vue-i18n';
import { ChatDotRound } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';
import { marked } from 'marked';
import { useAuthStore } from '@/stores/auth';
import { useAiStore } from '@/stores/ai';

interface SelectedDoc {
  id: number;
  doc_number?: string;
  title?: string;
}

const props = defineProps<{
  modelValue: boolean;
  docIds: number[];
  selectedDocs?: SelectedDoc[];
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void;
}>();

const { t } = useI18n();

const displayDocs = computed<SelectedDoc[]>(() => {
  if (props.selectedDocs && props.selectedDocs.length > 0) {
    return props.selectedDocs;
  }
  return props.docIds.map(id => ({ id }));
});
const authStore = useAuthStore();
const aiStore = useAiStore();
const visible = ref(props.modelValue);
const query = ref('');
const loading = ref(false);
const chatArea = ref<HTMLElement | null>(null);

const messages = ref<{role: string, content: string}[]>([]);

watch(() => props.modelValue, (val) => {
  visible.value = val;
});

watch(visible, (val) => {
  emit('update:modelValue', val);
});

function onClosed() {
  messages.value = [];
  query.value = '';
}

function renderMarkdown(text: string) {
  try {
    return marked(text);
  } catch (e) {
    return text;
  }
}

function scrollToBottom() {
  nextTick(() => {
    if (chatArea.value) {
      chatArea.value.scrollTop = chatArea.value.scrollHeight;
    }
  });
}

async function askQuestion() {
  if (!query.value.trim() || loading.value) return;
  
  const question = query.value.trim();
  messages.value.push({ role: 'user', content: question });
  query.value = '';
  loading.value = true;
  
  const aiMessageIndex = messages.value.length;
  messages.value.push({ role: 'assistant', content: '' });
  scrollToBottom();

  try {
    const response = await fetch('/api/ai/cross-qa', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${authStore.token}`
      },
      body: JSON.stringify({
        doc_ids: props.docIds,
        query: question,
        ai_model: aiStore.selectedModel || 'spark-lite'
      })
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const reader = response.body?.getReader();
    if (!reader) throw new Error("No reader");

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('data: ') && line !== 'data: [DONE]') {
          try {
            const data = JSON.parse(line.slice(6));
            if (data.content) {
              messages.value[aiMessageIndex].content += data.content;
              scrollToBottom();
            }
          } catch (e) {}
        }
      }
    }
  } catch (error: any) {
    ElMessage.error(error.message || 'QA failed');
    messages.value[aiMessageIndex].content += '\n\n**Error:** 请求失败。';
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.qa-container {
  display: flex;
  flex-direction: column;
  height: 60vh;
}
.qa-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  background: var(--el-fill-color-light);
  padding: 8px 12px;
  border-radius: 6px;
}
.selected-docs {
  display: flex;
  align-items: center;
  flex: 1;
  overflow: hidden;
}
.model-selector {
  display: flex;
  align-items: center;
  margin-left: 16px;
}
.label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
.doc-tag {
  margin-right: 4px;
}
.chat-area {
  flex: 1;
  overflow-y: auto;
  padding: 12px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
  margin-bottom: 16px;
}
.chat-bubble {
  max-width: 85%;
  margin-bottom: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  line-height: 1.5;
  word-break: break-word;
}
.chat-bubble.user {
  background-color: var(--el-color-primary);
  color: white;
  align-self: flex-end;
  margin-left: auto;
  border-bottom-right-radius: 4px;
}
.chat-bubble.assistant {
  background-color: white;
  border: 1px solid var(--el-border-color-light);
  align-self: flex-start;
  margin-right: auto;
  border-bottom-left-radius: 4px;
}
.input-area {
  display: flex;
  gap: 12px;
  align-items: flex-start;
}
.send-btn {
  height: 52px;
}
.typing .dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  background: var(--el-text-color-secondary);
  border-radius: 50%;
  margin: 0 2px;
  animation: typing 1.4s infinite ease-in-out both;
}
.typing .dot:nth-child(1) { animation-delay: -0.32s; }
.typing .dot:nth-child(2) { animation-delay: -0.16s; }
@keyframes typing {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
/* Base Markdown styles */
.markdown-body :deep(p) { margin: 0 0 10px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(ul), .markdown-body :deep(ol) { margin-top: 0; padding-left: 20px; }
.markdown-body :deep(pre) { background: #f6f8fa; padding: 10px; border-radius: 4px; overflow-x: auto; }
.markdown-body :deep(code) { background: #f6f8fa; padding: 2px 4px; border-radius: 4px; font-family: monospace; }
</style>
