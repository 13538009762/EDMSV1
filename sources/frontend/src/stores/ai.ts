import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface AiMessage {
  role: 'assistant' | 'user' | 'ai'; // 'ai' is used in EditorView, 'assistant' in global
  content: string;
  action?: any;
}

export const useAiStore = defineStore('ai', () => {
  const globalMessages = ref<AiMessage[]>([]);

  function addMessage(role: 'assistant' | 'user' | 'ai', content: string, action?: any) {
    globalMessages.value.push({ role, content, action });
  }

  function clearHistory() {
    globalMessages.value = [];
  }

  return {
    globalMessages,
    addMessage,
    clearHistory
  };
});
