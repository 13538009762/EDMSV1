import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface AiMessage {
  role: 'assistant' | 'user' | 'ai';
  content: string;
  action?: any;
  hidden?: boolean;
}

export const useAiStore = defineStore('ai', () => {
  const globalMessages = ref<AiMessage[]>([]);

  function addMessage(role: 'assistant' | 'user' | 'ai', content: string, action?: any, hidden?: boolean) {
    globalMessages.value.push({ role, content, action, hidden });
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
