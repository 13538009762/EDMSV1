import { defineStore } from 'pinia';
import { ref } from 'vue';

export interface AiMessage {
  role: 'assistant' | 'user' | 'ai'; // 'ai' is used in EditorView, 'assistant' in global
  content: string;
  action?: any;
}

export const useAiStore = defineStore('ai', () => {
  const globalMessages = ref<AiMessage[]>([
    { role: 'assistant', content: '您好！我是您的 EDMS 智能管家。您可以直接在这里问我问题，或者在编辑器中针对文档内容与我讨论。' }
  ]);

  function addMessage(role: 'assistant' | 'user' | 'ai', content: string, action?: any) {
    globalMessages.value.push({ role, content, action });
  }

  function clearHistory() {
    globalMessages.value = [
      { role: 'assistant', content: '您好！我是您的 EDMS 智能管家。您可以直接在这里问我问题，或者在编辑器中针对文档内容与我讨论。' }
    ];
  }

  return {
    globalMessages,
    addMessage,
    clearHistory
  };
});
