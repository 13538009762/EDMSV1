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
  const editorMessages = ref<AiMessage[]>([]);

  function addMessage(
    type: 'global' | 'editor',
    role: 'assistant' | 'user' | 'ai', 
    content: string, 
    action?: any, 
    hidden?: boolean
  ) {
    const target = type === 'global' ? globalMessages : editorMessages;
    target.value.push({ role, content, action, hidden });
  }

  function clearHistory(type: 'global' | 'editor') {
    if (type === 'global') globalMessages.value = [];
    else editorMessages.value = [];
  }

  return {
    globalMessages,
    editorMessages,
    addMessage,
    clearHistory
  };
});
