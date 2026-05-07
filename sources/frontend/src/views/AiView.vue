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
      <template v-for="(msg, i) in aiStore.globalMessages" :key="i">
        <div v-if="!msg.hidden" class="message-wrapper">
        <div :class="['message-item', msg.role]">
          <div class="avatar">
            <el-icon v-if="msg.role === 'user'"><User /></el-icon>
            <el-icon v-else><MagicStick /></el-icon>
          </div>
          <div class="content-box">
            <div class="role-label">{{ msg.role === 'user' ? t('aiView.userRole') : t('aiView.aiRole') }}</div>
            <div class="text-content">
              <template v-if="msg.content">
                <div v-html="renderMarkdown(msg.content)"></div>
              </template>
              <template v-else-if="isTyping && i === aiStore.globalMessages.length - 1">
                <div style="display: flex; justify-content: flex-start; align-items: center; min-height: 50px;">
                  <ThinkingNineLoader />
                </div>
              </template>
            </div>
            
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
      </template>
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
          <div class="footer-left">
            <el-select v-model="aiStore.selectedModel" size="small" class="model-select-mini">
              <el-option label="Spark Lite" value="spark-lite" />
              <el-option label="DeepSeek Chat" value="deepseek" />
            </el-select>
            <span class="hint">{{ t('aiView.inputHint') }}</span>
          </div>
          <el-button 
            type="primary" 
            :disabled="!input.trim() || isTyping" 
            @click="() => sendMessage()"
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
import { ref, onMounted, nextTick, computed, watch } from 'vue';
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
import ThinkingNineLoader from '@/components/ThinkingNineLoader.vue';

const { t } = useI18n();
const aiStore = useAiStore();
const auth = useAuthStore();
const router = useRouter();
const input = ref('');
const typingCount = ref(0);
const isTyping = computed(() => typingCount.value > 0);
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

// 💡 Robust Tag Parser for AI Actions
const parseTagParams = (text: string, actionType: string) => {
  const regex = new RegExp(`\\[ACTION:\\s*${actionType}(?:,\\s*([^\\]]+))?\\]`, 'i');
  const match = text.match(regex);
  if (!match) return null;
  
  const fullTag = match[0];
  const paramsStr = match[1] || '';
  const params: Record<string, string> = {};
  
  // Parse KEY: VALUE pairs
  const pairRegex = /([A-Z_]+):\s*([^,\]]+)/gi;
  let pairMatch;
  while ((pairMatch = pairRegex.exec(paramsStr)) !== null) {
    params[pairMatch[1].toUpperCase()] = pairMatch[2].trim();
  }
  
  return { fullTag, params };
};

const renderMarkdown = (text: string) => {
  if (!text) return '';
  const cleanText = text.replace(/\[ACTION:[\s\S]*?\]/g, '').trim();
  return marked.parse(cleanText);
};

const scrollToBottom = async (force = false) => {
  await nextTick();
  if (chatScroll.value) {
    const el = chatScroll.value;
    // 💡 Improved logic: 
    // 1. If force is true, scroll immediately.
    // 2. If it's the first message (scrollTop is 0), scroll.
    // 3. If user is within 300px of bottom, keep scrolling.
    const isAtTop = el.scrollTop === 0;
    const isNearBottom = el.scrollHeight - el.scrollTop <= el.clientHeight + 300;
    
    if (force || isNearBottom || (el.scrollHeight > el.clientHeight && isAtTop)) {
      el.scrollTop = el.scrollHeight;
    }
  }
};

// 💡 监听消息变化自动滚动
watch(() => aiStore.globalMessages, () => {
  scrollToBottom();
}, { deep: true });

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

const sendMessage = async (isFeedback = false) => {
  if (!isFeedback && (!input.value.trim() || isTyping.value)) return;

  const userQuery = input.value.trim();
  if (!isFeedback) {
    if (userQuery.toLowerCase() === 'clear' || userQuery === '清屏') {
      aiStore.clearHistory('global');
      input.value = '';
      return;
    }
    aiStore.addMessage('global', 'user', userQuery);
    input.value = '';
  }
  typingCount.value++;
  scrollToBottom(true);

  // Send the last 15 messages for better context
  const filteredMessages = aiStore.globalMessages
    .filter(m => m.content && m.content.trim() !== '')
    .slice(-15);

  let assistantMessage: any;
  const lastMsg = aiStore.globalMessages[aiStore.globalMessages.length - 1];
  if (isFeedback && lastMsg && lastMsg.role === 'assistant') {
    assistantMessage = lastMsg;
    // Spacing between turns in same bubble
    if (assistantMessage.content && !assistantMessage.content.endsWith('\n\n')) {
      assistantMessage.content += '\n\n';
    }
  } else {
    assistantMessage = { role: 'assistant' as const, content: '', action: null };
    aiStore.globalMessages.push(assistantMessage);
  }

  try {
    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        messages: filteredMessages,
        context_url: window.location.pathname,
        ai_model: aiStore.selectedModel
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
              // 1. Intercept JSON actions (Sensitive, need confirmation)
              const jsonMatch = assistantMessage.content.match(/```json\s*(\{[\s\S]*?\})\s*```/);
              if (jsonMatch) {
                try {
                  const actionData = JSON.parse(jsonMatch[1]);
                  const aType = String(actionData.action || '').toUpperCase();
                  const rawKeys = Object.keys(actionData).join(',').toUpperCase();
                  
                  // 💡 Aggressive Auto-execute: catch ANY read-only or query action
                  const safeKeywords = ['QUERY', 'SEARCH', 'STATS', 'COUNT', 'GET', 'LIST', 'VIEW', 'SHOW', 'READ', 'DASHBOARD', 'ORG'];
                  const isSafe = safeKeywords.some(k => aType.includes(k) || rawKeys.includes(k));
                  
                  if (isSafe) {
                    console.log("[AI] Auto-executing safe action:", aType || 'CUSTOM_QUERY');
                    assistantMessage.content = assistantMessage.content.replace(/```json\s*\{[\s\S]*?\}\s*```/, "").trim();
                    const msgIdx = aiStore.globalMessages.indexOf(assistantMessage);
                    await executeAction(actionData, msgIdx);
                    return; 
                  }

                  assistantMessage.action = actionData;
                  assistantMessage.content = assistantMessage.content.replace(/```json\s*\{[\s\S]*?\}\s*```/, "").trim();
                } catch(e) {}
              }

              // 2. Intercept Tags (Automatic actions)
              // Handle NAVIGATE
              const nav = parseTagParams(assistantMessage.content, 'NAVIGATE');
              if (nav && nav.params.PATH) {
                const path = nav.params.PATH;
                ElMessage.success(t('aiView.messages.redirecting', { id: path }));
                router.push(path);
                assistantMessage.content = assistantMessage.content.replace(nav.fullTag, '').trim();
              }

              // Handle OPEN_DOC (legacy support)
              const open = parseTagParams(assistantMessage.content, 'OPEN_DOC');
              if (open && open.params.ID) {
                const docId = open.params.ID;
                ElMessage.success(t('aiView.messages.redirecting', { id: docId }));
                router.push(`/doc/${docId}`);
                assistantMessage.content = assistantMessage.content.replace(open.fullTag, '').trim();
              }

              // Handle QUERY_DATA
              const qData = parseTagParams(assistantMessage.content, 'QUERY_DATA');
              if (qData && qData.params.ENTITY && qData.params.QUERY) {
                const entity = qData.params.ENTITY.toLowerCase();
                const query = qData.params.QUERY;
                assistantMessage.content = assistantMessage.content.replace(qData.fullTag, '').trim();
                
                const tempMsg = assistantMessage.content;
                assistantMessage.content = tempMsg + "\n\n⌛ *正在检索 " + entity + "...*"; 
                
                try {
                  let res;
                  let resultHtml = "";
                  if (entity === 'documents') {
                    res = await api.get('/documents', { params: { search: query } });
                    const items = res.data.items || [];
                    if (items.length > 0) {
                      resultHtml = "\n\n### 找到以下文档:\n" + items.map((d:any) => `- **[${d.doc_number}] ${d.title}** (状态: ${d.status})`).join('\n');
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

                  // 💡 Reflexive feedback: Send the results back to AI so it can "read and output" properly
                  if (resultHtml) {
                    const isError = resultHtml.includes('❌') || resultHtml.includes('⚠️');
                    const feedbackPrompt = isError 
                      ? `[SYSTEM]: Search for ${entity} (${query}) returned no results or failed. Briefly notify user and ask for clarification.`
                      : `[SYSTEM]: Search results for ${entity} (${query}):\n${resultHtml}\nSummarize and present to user.`;
                    
                    aiStore.addMessage('global', 'system', feedbackPrompt, null, true); 
                    await sendMessage(true); 
                  }
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n⚠️ 查询失败，请稍后重试。";
                }
              }

              // Handle QUERY_STATS (legacy)
              const qStats = parseTagParams(assistantMessage.content, 'QUERY_STATS');
              if (qStats && qStats.params.TYPE) {
                const statType = qStats.params.TYPE.toLowerCase();
                assistantMessage.content = assistantMessage.content.replace(qStats.fullTag, '').trim();
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
                  
                  // Feed back to AI using system role
                  aiStore.addMessage('global', 'system', `[SYSTEM]: Statistical data retrieved:\n${resultText}\nPlease inform the user.`, null, true);
                  await sendMessage(true);
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n" + t('aiView.messages.dbTimeout');
                }
              }

              // Handle QUERY_DASHBOARD
              const qDash = parseTagParams(assistantMessage.content, 'QUERY_DASHBOARD');
              if (qDash && qDash.params.TYPE) {
                const dType = qDash.params.TYPE.toLowerCase();
                assistantMessage.content = assistantMessage.content.replace(qDash.fullTag, '').trim();
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
                  
                  // Feed back to AI using system role
                  aiStore.addMessage('global', 'system', `[SYSTEM]: Dashboard ${dType} analysis results:\n${resultHtml}\nPlease summarize for the user.`, null, true);
                  await sendMessage(true);
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
    typingCount.value = Math.max(0, typingCount.value - 1);
    scrollToBottom();
  }
};

const getActionDesc = (action: any) => {
  if (!action) return "";
  if (action.confirm_prompt) return action.confirm_prompt;
  
  const type = String(action.action || '').toUpperCase();
  const p = action.params || {};

  if (type.includes('START_APPROVAL')) {
    const docText = p.doc_id ? `文档 ID ${p.doc_id}` : '';
    return `确认对 ${docText} 发起 ${p.type === 'sequential' ? '顺序' : '并行'} 审批吗？`;
  }
  if (type.includes('RECALL_APPROVAL')) {
    const docText = p.doc_id ? `文档 ID ${p.doc_id}` : '';
    return `确认撤销 ${docText} 的审批申请吗？`;
  }
  if (type.includes('QUERY_DATA') || type.includes('SEARCH') || type.includes('GET') || type.includes('LIST')) {
    return `检索 ${p.ENTITY || p.entity || '系统数据'}: ${p.QUERY || p.query || ''}`;
  }
  if (type.includes('STATS') || type.includes('COUNT')) {
    return `统计查询: ${p.TYPE || p.type || '数据指标'}`;
  }
  if (type.includes('QUERY_DASHBOARD') || type.includes('DASHBOARD')) {
    return `立即分析仪表盘实时数据: ${p.TYPE || '概览'}`;
  }
  if (type === 'DELETE_DOC') return `确认删除文档 ID: ${p.id}`;
  if (type === 'UPDATE_DOC') return `确认更新文档 ID: ${p.id}`;
  if (type === 'UPDATE_USER') return `确认更新用户信息 ID: ${p.id}`;
  if (type === 'CREATE_USER') return `确认创建新用户: ${p.data?.login_name}`;
  
  return t('aiView.suggestedAction');
};

const executeAction = async (action: any, idx: number) => {
  const type = String(action.action || '').toUpperCase();
  const p = action.params || {};
  
  try {
    const isQuery = ['QUERY', 'SEARCH', 'STATS', 'DASHBOARD', 'GET', 'LIST', 'COUNT', 'VIEW', 'SHOW', 'READ'].some(k => type.includes(k));
    if (isQuery) {
       // 💡 Handle any variation of query/search/stats/dashboard/get/list
       if (type.includes('DATA') || type.includes('SEARCH') || type.includes('GET') || type.includes('LIST')) {
          const entity = (p.ENTITY || p.entity || '').toLowerCase();
          const q = p.QUERY || p.query || 'all';
          const res = await api.get(entity.includes('approval') ? '/approvals/inbox' : (entity.includes('user') ? '/users' : '/documents'), { params: { search: q } });
          const result = JSON.stringify(res.data.items || res.data);
          aiStore.addMessage('global', 'system', `[SYSTEM]: Data retrieved: ${result}. Summarize for user.`, null, true);
          await sendMessage(true);
       } else if (type.includes('STATS') || type.includes('COUNT') || p.document_count !== undefined || p.user_count !== undefined) {
          const sType = (type.includes('USER') || p.user_count !== undefined) ? 'user_count' : 'document_count';
          const res = await api.get(sType === 'user_count' ? '/users/stats' : '/documents/stats');
          const result = sType === 'user_count' ? `👥 **当前成员总数**: **${res.data.total_count}**` : `📄 **当前文档总数**: **${res.data.total_count}**`;
          
          const msg = aiStore.globalMessages[idx];
          if (msg) {
            // 流式打字输出
            let i = 0;
            const timer = setInterval(() => {
              if (i < result.length) {
                msg.content += result.charAt(i);
                i++;
                scrollToBottom();
              } else { clearInterval(timer); }
            }, 15);
          }
       } else if (type.includes('DASHBOARD')) {
          const res = await api.get('/dashboard/stats');
          aiStore.addMessage('global', 'system', `[SYSTEM]: Dashboard results: ${JSON.stringify(res.data)}. Summarize for user.`, null, true);
          await sendMessage(true);
       } else if (type.includes('ORG')) {
          const msg = aiStore.globalMessages[idx];
          if (msg) {
             msg.content += "\n\n⌛ *正在检索组织架构...*";
             try {
                const res = await api.get('/users/org');
                const data = res.data;
                let resultHtml = `\n\n### 🏢 组织架构 (${data.department})\n\n`;
                
                if (data.manager) {
                  resultHtml += `👤 **直属主管**:\n- **${data.manager.display_name}** (${data.manager.position || '主管'})\n\n`;
                } else {
                  resultHtml += `👤 **直属主管**: 未设定\n\n`;
                }
                
                if (data.peers && data.peers.length > 0) {
                  resultHtml += `👥 **同部门同事**:\n` + data.peers.map((p:any) => `- **${p.display_name}** (${p.position || '员工'})`).join('\n');
                } else {
                  resultHtml += `👥 **同部门同事**: 暂无其他同事`;
                }
                
                msg.content = msg.content.replace("\n\n⌛ *正在检索组织架构...*", "");
                
                // 💡 流式输出结果
                let i = 0;
                const speed = 15;
                const timer = setInterval(() => {
                  if (i < resultHtml.length) {
                    msg.content += resultHtml.charAt(i);
                    i++;
                    scrollToBottom();
                  } else {
                    clearInterval(timer);
                    import('element-plus').then(({ ElNotification }) => {
                      ElNotification({
                        title: '组织架构已更新',
                        message: `已自动为您获取 ${data.department} 的成员信息`,
                        type: 'success',
                        position: 'bottom-right',
                        duration: 3000
                      });
                    });
                  }
                }, speed);
             } catch (e) {
                msg.content = msg.content.replace("\n\n⌛ *正在检索组织架构...*", "") + "\n\n⚠️ 组织架构获取失败。";
             }
          }
       }
    } else if (type.includes('DELETE_DOC')) {
      await api.delete(`/documents/${p.id}`);
      ElMessage.success("文档已成功删除");
    } else if (type === 'UPDATE_DOC') {
      await api.patch(`/documents/${p.id}`, p.data);
      ElMessage.success("文档已成功更新");
    } else if (type === 'UPDATE_USER') {
      await api.patch(`/users/${p.id}`, p.data);
      ElMessage.success("用户信息已更新");
    } else if (type === 'CREATE_USER') {
      await api.post('/users', p.data);
      ElMessage.success("用户创建成功");
    } else if (type === 'CREATE_DOC') {
      const res = await api.post('/documents', p);
      ElMessage.success("文档创建成功");
      router.push(`/doc/${res.data.id}`);
    } else if (type === 'START_APPROVAL') {
      const docId = p.doc_id || p.id;
      if (!docId) return ElMessage.warning("未指定文档 ID");
      
      let approvers = p.approvers || [];
      // 💡 尝试解析姓名到 ID
      if (approvers.length > 0 && typeof approvers[0] === 'string') {
        const loading = ElMessage({ message: '正在解析审批人...', duration: 0 });
        try {
          const res = await api.get('/users', { params: { search: approvers[0] } });
          const items = (res.data.items || []).filter((u: any) => u.id !== auth.user?.id);
          if (items.length === 1) {
            approvers = [items[0].id];
          }
        } catch (e) {} finally { loading.close(); }
      }

      if (approvers.length > 0 && typeof approvers[0] === 'number') {
        await api.post(`/documents/${docId}/approvals`, {
          type: p.type || 'parallel',
          approvers: approvers
        });
        ElMessage.success("审批流程已成功发起");
      } else {
        // Fallback to dialog
        window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
          detail: { approvers, type: p.type || 'parallel' } 
        }));
      }
    } else if (type === 'RECALL_APPROVAL') {
      await api.post(`/approvals/recall`, { doc_id: p.doc_id });
      ElMessage.success("审批申请已成功撤销");
    } else {
      ElMessage.warning("未知的操作类型: " + type);
    }
  } catch (e: any) {
    ElMessage.error(e.response?.data?.error || "执行操作失败");
  }
  if (aiStore.globalMessages[idx]) {
    aiStore.globalMessages[idx].action = null;
  }
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

.footer-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.model-select-mini :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.4) !important;
  box-shadow: none !important;
  border: 1px solid rgba(0, 0, 0, 0.05) !important;
  padding: 0 8px !important;
  height: 24px !important;
  border-radius: 6px !important;
}

.model-select-mini :deep(.el-input__inner) {
  font-size: 11px !important;
  color: var(--el-text-color-secondary) !important;
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
