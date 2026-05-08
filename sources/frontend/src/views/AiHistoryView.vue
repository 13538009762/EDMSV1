<template>
  <div class="ai-history-page">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><MagicStick /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t("aiHistory.title") }}</h1>
          <p class="page-sub">{{ t("aiHistory.subtitle") }}</p>
        </div>
      </div>
      <div class="header-right">
        <el-button type="primary" :icon="Refresh" circle @click="loadData" />
      </div>
    </div>

    <div class="table-container" v-loading="loading">
      <el-table :data="items" border style="width: 100%" height="100%">
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="detail-expand">
              <div class="detail-section">
                <h4>{{ t("aiHistory.colQuestion") }}</h4>
                <div class="content-box question">{{ row.question }}</div>
              </div>
              <div class="detail-section">
                <h4>{{ t("aiHistory.colAnswer") }}</h4>
                <div class="content-box answer" v-html="renderMarkdown(row.answer)"></div>
              </div>
              <div v-if="row.context_url" class="detail-section">
                <h4>Context URL</h4>
                <code>{{ row.context_url }}</code>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="id" label="ID" width="70" />
        
        <el-table-column :label="t('aiHistory.colTime')" width="180">
          <template #default="{ row }">
            {{ formatLocalDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column prop="user_name" :label="t('aiHistory.colUser')" width="140">
          <template #default="{ row }">
            <el-tag size="small" effect="plain">{{ row.user_name }}</el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="action_type" :label="t('aiHistory.colType')" width="120">
          <template #default="{ row }">
            <el-tag :type="row.action_type === 'chat' ? 'success' : 'warning'" size="small">
              {{ row.action_type === 'chat' ? t('aiHistory.chat') : t('aiHistory.editor') }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="ai_model" :label="t('aiHistory.colModel')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.ai_model" size="small" effect="dark" :type="row.ai_model === 'deepseek' ? 'info' : 'primary'">
              {{ row.ai_model }}
            </el-tag>
            <span v-else>-</span>
          </template>
        </el-table-column>
        
        <el-table-column :label="t('aiHistory.colQuestion')" min-width="300">
          <template #default="{ row }">
            <div class="question-cell">
              <div class="truncated-text">{{ row.question }}</div>
              <el-button 
                v-if="row.question && row.question.length > 80" 
                link 
                type="primary" 
                size="small" 
                @click="showDetail(row.question)"
              >
                {{ t('common.details') }}
              </el-button>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column :label="t('common.actions')" width="100" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleDelete(row.id)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <div class="pagination">
      <el-pagination
        v-model:current-page="page"
        v-model:page-size="size"
        :total="total"
        size="small"
        layout="total, prev, pager, next"
        @current-change="loadData"
      />
    </div>
    <el-dialog
      v-model="detailVisible"
      :title="t('aiHistory.colQuestion')"
      width="50%"
      append-to-body
      destroy-on-close
    >
      <div class="full-question-text">{{ detailText }}</div>
      <template #footer>
        <el-button @click="detailVisible = false">{{ t('common.ok') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/api/client';
import { formatLocalDate } from '@/utils/date';
import { ElMessage, ElMessageBox } from 'element-plus';
import { MagicStick, Refresh } from "@element-plus/icons-vue";
import { marked } from 'marked';

const { t } = useI18n();

const loading = ref(false);
const items = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);

const detailVisible = ref(false);
const detailText = ref('');

function showDetail(text: string) {
  detailText.value = text;
  detailVisible.value = true;
}

const renderMarkdown = (text: string) => {
  if (!text) return '';
  return marked.parse(text);
};

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get('/ai/history', { 
      params: { page: page.value, per_page: size.value } 
    });
    items.value = data.data.items;
    total.value = data.data.total;
  } catch (err) {
    ElMessage.error(t("common.failed"));
  } finally {
    loading.value = false;
  }
}

async function handleDelete(id: number) {
  try {
    await ElMessageBox.confirm(t('editor.actions.deleteUserConfirm'), t('common.warning'), {
      type: 'warning'
    });
    await api.delete(`/ai/history/${id}`);
    ElMessage.success(t("common.success"));
    loadData();
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(t("common.failed"));
    }
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.ai-history-page {
  padding: 0 0 40px;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 32px 40px;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #7367f0 130%) !important;
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-ring {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: rgba(255,255,255,0.18);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  color: #fff;
}

.page-title {
  margin: 0 0 4px !important;
  font-size: 1.5rem !important;
  font-weight: 800 !important;
  color: #fff !important;
}

.page-sub {
  margin: 0 !important;
  font-size: 0.9rem !important;
  color: rgba(255,255,255,0.8) !important;
}

.table-container {
  flex: 1;
  min-height: 0;
  background-color: rgba(255, 255, 255, 0.65) !important; 
  backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  border-radius: 12px;
  padding: 20px;
}

:deep(.el-table) {
  background: transparent !important;
}

.detail-expand {
  padding: 20px 40px;
  background: rgba(255, 255, 255, 0.3);
}

.detail-section {
  margin-bottom: 20px;
}

.detail-section h4 {
  margin: 0 0 10px 0;
  color: var(--el-text-color-primary);
  font-size: 14px;
  border-left: 3px solid var(--el-color-primary);
  padding-left: 8px;
}

.content-box {
  padding: 16px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.content-box.question {
  background: var(--el-fill-color-lighter);
  color: var(--el-text-color-regular);
}

.content-box.answer {
  background: var(--el-color-primary-light-9);
  color: var(--el-text-color-primary);
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.question-cell {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.truncated-text {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: ellipsis;
  line-height: 1.5;
  margin-bottom: 4px;
  white-space: pre-wrap;
}

.full-question-text {
  white-space: pre-wrap;
  line-height: 1.6;
  font-size: 15px;
  color: var(--el-text-color-primary);
  max-height: 60vh;
  overflow-y: auto;
  padding: 10px;
  background: var(--el-fill-color-lighter);
  border-radius: 8px;
}
</style>
