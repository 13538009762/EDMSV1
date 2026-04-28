<template>
  <div class="ai-page-container">
    <!-- Empty state with suggestions -->
    <div v-if="aiStore.globalMessages.length === 0 && !isTyping" class="empty-state">
      <div class="welcome-section">
        <el-icon class="huge-icon"><MagicStick /></el-icon>
        <h1>{{ t('aiView.welcome') }}</h1>
        <p class="subtitle">{{ t('aiView.subtitle') }}</p>
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
    <transition-group name="msg" tag="div" class="chat-main" ref="chatScroll">
      <div class="message-wrapper" v-for="(msg, i) in aiStore.globalMessages" :key="i">
        <div :class="['message-item', msg.role]">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><MagicStick /></el-icon>
          </div>
          <div class="content-box">
            <div class="role-label">{{ msg.role === 'user' ? t('aiView.userRole') : t('aiView.aiRole') }}</div>
            <div class="text-content" v-html="renderMarkdown(msg.content)"></div>
            
            <!-- Action Card inside message -->
            <div v-if="msg.action" class="inline-action-card">
              <div class="card-header">
                <el-icon><InfoFilled /></el-icon>
                <span>{{ t('aiView.suggestedAction') }}</span>
              </div>
              <div class="card-body">
                <p>{{ getActionDesc(msg.action) }}</p>
              </div>
              <div class="card-footer">
                <el-button type="primary" size="small" @click="executeAction(msg.action, i)">{{ t('aiView.executeNow') }}</el-button>
                <el-button size="small" link @click="msg.action = null">{{ t('aiView.ignore') }}</el-button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-if="isTyping" key="typing" class="message-item assistant typing">
        <div class="avatar"><el-icon><MagicStick /></el-icon></div>
        <div class="content-box">
          <div class="role-label">{{ t('aiView.aiRole') }}</div>
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </transition-group>

    <!-- Fixed Input Area -->
    <div class="input-container">
      <div class="input-wrapper">
        <el-input
          v-model="input"
          type="textarea"
          :autosize="{ minRows: 1, maxRows: 8 }"
          :placeholder="t('aiView.inputPlaceholder')"
          @keydown.enter.prevent="handleEnter"
          class="chat-textarea"
        />
        <div class="input-footer">
          <span class="hint">{{ t('aiView.inputHint') }}</span>
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
      <div class="disclaimer">{{ t('aiView.disclaimer') }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, nextTick, computed } from 'vue';
import { useI18n } from 'vue-i18n';
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

const { t } = useI18n();
const aiStore = useAiStore();
const auth = useAuthStore();
const router = useRouter();
const input = ref('');
const isTyping = ref(false);
const chatScroll = ref<HTMLElement | null>(null);

const suggestions = computed(() => [
  { 
    title: t('aiView.suggestions.summarize.title'), 
    desc: t('aiView.suggestions.summarize.desc'), 
    prompt: t('aiView.suggestions.summarize.prompt'), 
    icon: FolderOpened 
  },
  { 
    title: t('aiView.suggestions.approval.title'), 
    desc: t('aiView.suggestions.approval.desc'), 
    prompt: t('aiView.suggestions.approval.prompt'), 
    icon: DocumentChecked 
  },
  { 
    title: t('aiView.suggestions.query.title'), 
    desc: t('aiView.suggestions.query.desc'), 
    prompt: t('aiView.suggestions.query.prompt'), 
    icon: Management 
  }
]);

const renderMarkdown = (text: string) => {
  if (!text) return '';
  const cleanText = text.replace(/\[ACTION:[\s\S]*?\]/g, '').trim();
  return marked.parse(cleanText);
};

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

  // Send the last 10 messages raw for troubleshooting
  const filteredMessages = aiStore.globalMessages
    .filter(m => m.content.trim() !== '')
    .slice(-10);

  let assistantMessage = { role: 'assistant' as const, content: '', action: null };
  aiStore.globalMessages.push(assistantMessage);

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        messages: filteredMessages,
        context_url: window.location.pathname
      })
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `Server responded with ${response.status}`);
    }

    if (!response.body) throw new Error('No response body');
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    
    let buffer = '';
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep the last partial line in buffer
      
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
              // Handle NAVIGATE
              const navRegex = /\[ACTION:\s*NAVIGATE,\s*PATH:\s*([^\s\]]+)\]/i;
              const navMatch = assistantMessage.content.match(navRegex);
              if (navMatch && navMatch[1]) {
                const path = navMatch[1];
                ElMessage.success(t('aiView.messages.redirecting', { id: path }));
                router.push(path);
                assistantMessage.content = assistantMessage.content.replace(navRegex, '').trim();
              }

              // Handle OPEN_DOC (legacy support)
              const openDocRegex = /\[ACTION:\s*OPEN_DOC,\s*ID:\s*([a-zA-Z0-9_-]+)\]/i;
              const openMatch = assistantMessage.content.match(openDocRegex);
              if (openMatch && openMatch[1]) {
                const docId = openMatch[1];
                ElMessage.success(t('aiView.messages.redirecting', { id: docId }));
                router.push(`/doc/${docId}`);
                assistantMessage.content = assistantMessage.content.replace(openDocRegex, '').trim();
              }

              // Handle QUERY_DATA
              const queryDataRegex = /\[ACTION:\s*QUERY_DATA,\s*ENTITY:\s*([a-z]+),\s*QUERY:\s*([^\]]+)\]/i;
              const qMatch = assistantMessage.content.match(queryDataRegex);
              if (qMatch) {
                const entity = qMatch[1];
                const query = qMatch[2];
                assistantMessage.content = assistantMessage.content.replace(queryDataRegex, '').trim();
                
                const tempMsg = assistantMessage.content;
                assistantMessage.content = tempMsg + "\n\n⌛ *正在检索 " + entity + "...*"; 
                
                try {
                  let res;
                  let resultHtml = "";
                  if (entity === 'documents') {
                    res = await api.get('/documents', { params: { search: query } });
                    const items = res.data.items || [];
                    if (items.length > 0) {
                      resultHtml = "\n\n### 找到以下文档:\n" + items.map((d:any) => `- **[${d.doc_number}] ${d.title}** (ID: ${d.id}, 状态: ${d.status})`).join('\n');
                    } else {
                      resultHtml = "\n\n❌ 未找到相关文档。";
                    }
                  } else if (entity === 'users') {
                    res = await api.get('/users', { params: { search: query } });
                    const items = (res.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                    if (items.length > 0) {
                      resultHtml = "\n\n### 找到以下用户:\n" + items.map((u:any) => `- **${u.display_name}** (${u.login_name}, ID: ${u.id}) - ${u.department_name}`).join('\n');
                    } else {
                      resultHtml = "\n\n❌ 未找到相关用户。";
                    }
                  } else if (entity === 'approvals') {
                    res = await api.get('/approvals/inbox');
                    const items = res.data.items || [];
                    if (items.length > 0) {
                      resultHtml = "\n\n### 待处理审批:\n" + items.map((a:any) => `- **${a.title}** (来自: ${a.initiator_name}, 进度: ${a.progress.done}/${a.progress.total})`).join('\n');
                    } else {
                      resultHtml = "\n\n✅ 暂无待处理审批。";
                    }
                  }
                  
                  assistantMessage.content = tempMsg + (resultHtml || "\n\n✅ 查询完成。");
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n⚠️ 查询失败，请稍后重试。";
                }
              }

              // Handle QUERY_STATS (legacy)
              const queryStatsRegex = /\[ACTION:\s*QUERY_STATS,\s*TYPE:\s*([a-zA-Z0-9_-]+)\]/i;
              const queryMatch = assistantMessage.content.match(queryStatsRegex);
              if (queryMatch) {
                const statType = queryMatch[1];
                assistantMessage.content = assistantMessage.content.replace(queryStatsRegex, '').trim();
                const tempMsg = assistantMessage.content;
                assistantMessage.content = tempMsg + "\n\n⌛ *...*"; 
                try {
                  let resultText = "";
                  if (statType === 'user_count') {
                    const res = await api.get('/users/stats');
                    resultText = `📊 **系统统计**: 当前权限内共有 **${res.data.total_count}** 位可见成员。`;
                  } else {
                    const res = await api.get('/documents/stats'); 
                    const stats = res.data;
                    resultText = `📊 **系统统计**: 当前权限下共有 **${stats.total_count}** 份可见文档。`;
                  }
                  assistantMessage.content = tempMsg + "\n\n" + resultText;
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n" + t('aiView.messages.dbTimeout');
                }
              }

              // Handle QUERY_DASHBOARD
              const dashboardRegex = /\[ACTION:\s*QUERY_DASHBOARD,\s*TYPE:\s*([a-z]+)\]/i;
              const dMatch = assistantMessage.content.match(dashboardRegex);
              if (dMatch) {
                const dType = dMatch[1];
                assistantMessage.content = assistantMessage.content.replace(dashboardRegex, '').trim();
                const tempMsg = assistantMessage.content;
                assistantMessage.content = tempMsg + "\n\n⌛ *正在分析仪表盘数据...*";
                try {
                  const res = await api.get('/dashboard/stats');
                  const data = res.data;
                  let resultHtml = "";
                  if (dType === 'storage') {
                    resultHtml = `📊 **存储规格占比分析**:\n- 总存储量: **${data.storage_info.total_size_mb} MB**\n` + 
                                 data.storage_info.by_type.map((t:any) => `  - ${t.name}: ${t.value} MB`).join('\n');
                  } else if (dType === 'activity') {
                    const todayTrend = data.trend_data[data.trend_data.length-1];
                    resultHtml = `📈 **用户活跃度简报**:\n- 今日新增/更新文档: **${todayTrend.docs}**\n- 今日完成审批: **${todayTrend.approvals}**\n- 活跃热力指数: **${data.heatmap_data.length}** 个活跃日(近90天)`;
                  } else if (dType === 'distribution') {
                    resultHtml = `🏢 **部门分布**: \n` + data.dept_data.map((d:any) => `- ${d.name}: ${d.count} 份`).join('\n') + 
                                 `\n\n📂 **空间分布**: \n` + data.space_data.map((s:any) => `- ${s.name}: ${s.count} 份`).join('\n');
                  } else if (dType === 'security') {
                    resultHtml = `🛡️ **安全合规监控**:\n- 已上链确权: **${data.blockchain_stats.on_chain_count}** 份\n- 零信任拦截次数: **${data.blockchain_stats.tamper_alerts}** 次\n- 模拟区块高度: **${data.blockchain_stats.block_height}**`;
                  } else {
                    resultHtml = `📑 **系统总体概览**:\n- 总成员数: **${data.total_users}**\n- 权限内可见文档: **${data.total_docs}**\n- 待我审批: **${data.my_stats.pending}** 份`;
                  }
                  assistantMessage.content = tempMsg + "\n\n" + resultHtml;
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n⚠️ 仪表盘数据获取失败。";
                }
              }
            }
            scrollToBottom();
          } catch (e) {}
        }
      }
    }
  } catch (error: any) {
    ElMessage.error(t('aiView.messages.serviceError'));
    assistantMessage.content = t('aiView.messages.unstable') + (error.message ? ` (${error.message})` : '');
  } finally {
    isTyping.value = false;
    scrollToBottom();
  }
};

const getActionDesc = (action: any) => {
  if (action.confirm_prompt) return action.confirm_prompt;
  if (action.action === 'start_approval') {
    const docText = action.params?.doc_id ? `文档 ID ${action.params.doc_id}` : '';
    return `确认对 ${docText} 发起 ${action.params?.type === 'sequential' ? '顺序' : '并行'} 审批吗？`;
  }
  if (action.action === 'delete_doc') return `确认删除文档 ID: ${action.params?.id}`;
  if (action.action === 'update_doc') return `确认更新文档 ID: ${action.params?.id}`;
  if (action.action === 'update_user') return `确认更新用户信息 ID: ${action.params?.id}`;
  if (action.action === 'create_user') return `确认创建新用户: ${action.params?.data?.login_name}`;
  return t('aiView.suggestedAction');
};

const executeAction = async (action: any, idx: number) => {
  try {
    if (action.action === 'delete_doc') {
      await api.delete(`/documents/${action.params.id}`);
      ElMessage.success("文档已成功删除");
    } else if (action.action === 'update_doc') {
      await api.patch(`/documents/${action.params.id}`, action.params.data);
      ElMessage.success("文档已成功更新");
    } else if (action.action === 'update_user') {
      await api.patch(`/users/${action.params.id}`, action.params.data);
      ElMessage.success("用户信息已更新");
    } else if (action.action === 'create_user') {
      await api.post('/users', action.params.data);
      ElMessage.success("用户创建成功");
    } else if (action.action === 'create_doc') {
      const res = await api.post('/documents', action.params);
      ElMessage.success("文档创建成功");
      router.push(`/doc/${res.data.id}`);
    } else if (action.action === 'start_approval') {
      await api.post(`/documents/${action.params.doc_id}/approvals`, {
        type: action.params.type || 'parallel',
        approvers: action.params.approvers
      });
      ElMessage.success("审批流程已成功发起");
    } else {
      ElMessage.warning("未知的操作类型");
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || "执行操作失败");
  }
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
  font-size: 11px;
  color: var(--el-text-color-placeholder);
  margin-top: 8px;
}

/* Message Animations */
.msg-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(15px);
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
