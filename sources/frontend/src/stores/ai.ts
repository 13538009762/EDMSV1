import { defineStore } from 'pinia';
import { ref, watch } from 'vue';



export interface AiMessage {
  role: 'assistant' | 'user' | 'ai' | 'system';
  content: string;
  action?: any;
  hidden?: boolean;
}

export const useAiStore = defineStore('ai', () => {
  const globalMessages = ref<AiMessage[]>([]);
  const editorMessages = ref<AiMessage[]>([]);

  // Selected AI model, persisted in localStorage
  const selectedModel = ref<string>(localStorage.getItem('aiModel') || 'spark-lite');

  watch(selectedModel, (val) => {
    localStorage.setItem('aiModel', val);
  });

  function setModel(model: string) {
    selectedModel.value = model;
  }

  function addMessage(
    type: 'global' | 'editor',
    role: 'assistant' | 'user' | 'ai' | 'system',
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
    selectedModel,
    setModel,
    addMessage,
    clearHistory,
  };
});
