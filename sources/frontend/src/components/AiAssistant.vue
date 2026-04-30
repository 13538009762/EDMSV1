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
        <transition-group name="msg" tag="div" class="chat-messages" ref="scrollContainer">
          <div v-for="(msg, i) in aiStore.globalMessages" :key="i" :class="['message', msg.role]">
            <div v-if="msg.role === 'assistant'" class="avatar-mini"><el-icon><MagicStick /></el-icon></div>
            <div class="bubble">
              <div class="content" v-html="renderMarkdown(msg.content)"></div>
              
              <!-- Action Card in Sidebar -->
              <div v-if="msg.action" class="sidebar-action-card">
                <div class="card-desc">{{ getActionDesc(msg.action) }}</div>
                <div class="card-btns">
                  <el-button type="primary" size="small" @click="executeAction(msg.action, i)">执行</el-button>
                  <el-button size="small" link @click="msg.action = null">忽略</el-button>
                </div>
              </div>

              <!-- Quick Insert Button -->
              <div v-if="msg.role === 'assistant' && isEditorPage" class="bubble-footer">
                <el-button size="small" link type="primary" @click="insertToDoc(msg.content)">
                  <el-icon><MagicStick /></el-icon> 插入到文档
                </el-button>
              </div>
            </div>
          </div>
          <div v-if="isTyping" key="typing" class="message assistant typing">
            <div class="avatar-mini"><el-icon><MagicStick /></el-icon></div>
            <div class="bubble" style="display: flex; justify-content: center; align-items: center; min-height: 50px;">
              <ThinkingNineLoader />
            </div>
          </div>
        </transition-group>

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
import { ElMessage } from 'element-plus';
import { computed } from 'vue';
import api from '@/api/client';
import { useRouter } from 'vue-router';
import ThinkingNineLoader from './ThinkingNineLoader.vue';

const props = defineProps({
  isSidebarCollapsed: Boolean
});

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const aiStore = useAiStore();
const input = ref('');
const isTyping = ref(false);
const isExpanded = ref(true);
const scrollContainer = ref<HTMLElement | null>(null);

const isEditorPage = computed(() => route.path.startsWith('/doc/'));

function insertToDoc(content: string) {
  // Clean up content: remove [ACTION:...] tags
  const cleanContent = content.replace(/\[ACTION:[\s\S]*?\]/g, '').trim();
  if (!cleanContent) return;
  
  // Dispatch a custom event that EditorView.vue listens to
  window.dispatchEvent(new CustomEvent('edms:insert_content', { detail: { content: cleanContent } }));
  ElMessage.success("内容已发送至编辑器");
}

const getActionDesc = (action: any) => {
  if (action.confirm_prompt) return action.confirm_prompt;
  if (action.action === 'start_approval') {
    // 💡 优先显示人名而非 ID
    const names = action.params?.approver_names || action.params?.approvers?.join(', ') || '选中人员';
    return `发起审批流程: ${names}`;
  }
  return "建议操作";
};

const executeAction = async (action: any, idx: number) => {
  try {
    if (action.action === 'start_approval') {
      console.log("[DEBUG] Sidebar Dispatching edms:trigger_approval", action.params);
      // 💡 优化：不再直接调接口，而是弹出带预选人的弹窗供用户确认
      window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
        detail: { 
          approvers: action.params.approvers, 
          type: action.params.type || 'parallel'
        } 
      }));
    } else if (action.action === 'navigate') {
      router.push(action.params.path);
    }
  } catch (e: any) {
    ElMessage.error("执行失败");
  }
  aiStore.globalMessages[idx].action = null;
};

const toggleExpand = () => {
  if (props.isSidebarCollapsed) return;
  isExpanded.value = !isExpanded.value;
};

const renderMarkdown = (text: string) => {
  if (!text) return '';
  // 💡 Hide internal action tags from the user to keep the chat clean
  const cleanText = text.replace(/\[ACTION:[\s\S]*?\]/g, '').trim();
  return marked.parse(cleanText);
};

const scrollToBottom = async () => {
  await nextTick();
  if (scrollContainer.value) {
    const el = (scrollContainer.value as any).$el || scrollContainer.value;
    el.scrollTop = el.scrollHeight;
  }
};

// 💡 监听消息变化自动滚动
watch(() => aiStore.globalMessages, () => {
  scrollToBottom();
}, { deep: true });

onMounted(scrollToBottom);

const sendMessage = async () => {
  if (!input.value.trim() || isTyping.value) return;

  const userQuery = input.value;
  aiStore.addMessage('global', 'user', userQuery);
  input.value = '';
  isTyping.value = true;
  scrollToBottom();
  try {
    // Scoped RAG for Sidebar if in Editor
    let doc_context = "";
    if (isEditorPage.value) {
       const docId = route.params.id;
       const editorEl = document.querySelector('.tiptap.ProseMirror');
       if (editorEl && (editorEl as any).textContent) {
         doc_context = `[当前编辑文档信息] ID: ${docId}, 路径: ${route.path}\n\n内容摘要: ${(editorEl as any).textContent.slice(0, 3000)}`;
       }
    }

    const response = await fetch('/api/ai/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${auth.token}`
      },
      body: JSON.stringify({
        messages: aiStore.globalMessages,
        context_url: route.path,
        doc_context: doc_context
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
            if (data.content) {
              assistantMessage.content += data.content;
            } else if (data.type === 'done') {
              // Handle Tags
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
                    if (items.length > 1) {
                      // 多个匹配结果：列出让用户选择
                      resultHtml = "\n\n### 找到以下用户（请告知确认发给哪位）:\n" + items.map((u:any) => `- **${u.display_name}** (${u.login_name}) - ${u.department_name}`).join('\n');
                    } else if (items.length === 1) {
                      // 💡 只有1个结果：显示成功信息并直接触发弹窗
                      const foundUser = items[0];
                      const docIdStr = route.path.match(/\/doc\/(\d+)/)?.[1];
                      resultHtml = `\n\n✅ 已定位到用户: **${foundUser.display_name}**`;
                      
                      // 构建 action 对象供界面展示（备用）
                      assistantMessage.action = {
                        action: 'start_approval',
                        confirm_prompt: `立即发起审批：${foundUser.display_name}？`,
                        params: {
                          doc_id: docIdStr ? Number(docIdStr) : null,
                          approvers: [foundUser.id],
                          approver_names: foundUser.display_name,
                          type: 'sequential'
                        }
                      };

                      // 💡 自动触发：直接分发事件弹出标准审批窗口
                      console.log("[DEBUG] Auto-triggering approval dialog for:", foundUser.display_name);
                      window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
                        detail: { 
                          approvers: [foundUser.id], 
                          type: 'sequential'
                        } 
                      }));
                    } else {
                      resultHtml = "\n\n❌ 未找到相关用户。";
                    }
                  }
                  if (resultHtml !== undefined) {
                    assistantMessage.content = tempMsg + (resultHtml || "");
                  }
                } catch (e) {
                  assistantMessage.content = tempMsg + "\n\n⚠️ 查询失败。";
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

              // Handle JSON actions (fallback for AI-generated action blocks)
              const jsonMatch = assistantMessage.content.match(/```json\s*(\{[\s\S]*?\})\s*```/);
              if (jsonMatch && !assistantMessage.action) {
                try {
                  let actionData = JSON.parse(jsonMatch[1]);
                  
                  // 💡 兼容性处理：支持 { start_approval: { ... } } 格式
                  if (actionData.start_approval && !actionData.action) {
                    actionData = { action: 'start_approval', params: actionData.start_approval };
                  }

                  if (actionData.action === 'start_approval') {
                    const params = actionData.params || actionData;

                    // 💡 强力补全：从加粗文字或 approvers 列表中提取人名
                    if (!params.approver_names) {
                      const nameMatch = assistantMessage.content.match(/\*\*([^\*]{2,10})\*\*/);
                      if (nameMatch) {
                        params.approver_names = nameMatch[1];
                      } else if (params.approvers && Array.isArray(params.approvers)) {
                        const nameList = params.approvers.filter((p: any) => typeof p === 'string');
                        if (nameList.length > 0) params.approver_names = nameList.join(', ');
                      }
                    }

                    // 💡 核心改进：如果只有姓名没有 ID，自动尝试匹配并弹出窗口
                    if (params.approver_names && (!params.approvers || params.approvers.length === 0 || typeof params.approvers[0] === 'string')) {
                      const searchName = params.approver_names.split(',')[0].trim();
                      api.get('/users', { params: { search: searchName } }).then(res => {
                        let matchedUsers = (res.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                        
                        // 💡 容错处理：如果没搜到，尝试去掉所有空格再搜一次
                        if (matchedUsers.length === 0 && searchName.includes(' ')) {
                          return api.get('/users', { params: { search: searchName.replace(/\s/g, '') } }).then(res2 => {
                            matchedUsers = (res2.data.items || []).filter((u: any) => u.id !== auth.user?.id);
                            return matchedUsers;
                          });
                        }
                        return matchedUsers;
                      }).then(foundList => {
                        if (foundList && foundList.length === 1) {
                          const foundUser = foundList[0];
                          params.approvers = [foundUser.id];
                          params.approver_names = foundUser.display_name;
                          
                          // 自动弹出窗口 (Dispatch to EditorView)
                          window.dispatchEvent(new CustomEvent('edms:trigger_approval', { 
                            detail: { approvers: [foundUser.id], type: params.type || 'sequential' } 
                          }));
                        } else {
                          console.log("[AI Assistant] Search for " + searchName + " returned " + (foundList?.length || 0) + " items");
                        }
                      }).catch(err => {
                        console.error("[AI Assistant] User search failed", err);
                      });
                    }

                    // 更新 confirm_prompt 确保显示名字
                    const displayName = params.approver_names || '目标用户';
                    actionData.confirm_prompt = `立即发起审批：${displayName}？`;
                    
                    assistantMessage.action = actionData;
                  }
                  assistantMessage.content = assistantMessage.content.replace(/```json\s*\{[\s\S]*?\}\s*```/, "").trim();
                } catch(e) {
                   console.error("AiAssistant action parse failed", e);
                }
              }
            }
            scrollToBottom();
          } catch (e) {}
        }
      }
    }
  } catch (error) {
    console.error('Chat error:', error);
    aiStore.addMessage('global', 'assistant', '抱歉，我现在无法响应您的请求。');
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
  scroll-behavior: smooth;
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
  flex-direction: row;
  gap: 8px;
}

.avatar-mini {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  flex-shrink: 0;
  border: 1px solid var(--el-color-primary-light-7);
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

.sidebar-action-card {
  margin-top: 10px;
  padding: 8px;
  background: rgba(var(--el-color-primary-rgb), 0.05);
  border: 1px solid rgba(var(--el-color-primary-rgb), 0.2);
  border-radius: 8px;
}

.card-desc {
  font-size: 12px;
  margin-bottom: 8px;
  color: var(--el-text-color-primary);
}

.card-btns {
  display: flex;
  gap: 8px;
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



.expand-enter-active, .expand-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 500px;
}
.expand-enter-from, .expand-leave-to {
  height: 0;
  opacity: 0;
}

/* Message Animations */
.msg-enter-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.msg-enter-from {
  opacity: 0;
  transform: translateY(12px) scale(0.95);
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
.bubble-footer {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px dashed var(--el-border-color-lighter);
  display: flex;
  justify-content: flex-end;
}
</style>
