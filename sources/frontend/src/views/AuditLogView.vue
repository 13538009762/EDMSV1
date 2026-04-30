<template>
  <div class="audit-page">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><Monitor /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t("auditLog.title", "Operation Trail") }}</h1>
          <p class="page-sub">{{ t("dashboard.subtitle", "Review system events and security logs.") }}</p>
        </div>
      </div>
    </div>

    <div class="filters">
      <el-form :inline="true">
        <el-form-item :label="t('auditLog.documentId', 'Doc ID')">
          <el-input v-model="filters.document_id" clearable placeholder="e.g. 12" style="width: 120px"></el-input>
        </el-form-item>
        <el-form-item :label="t('auditLog.userId', 'User ID')">
          <el-input v-model="filters.user_id" clearable placeholder="e.g. 5" style="width: 120px"></el-input>
        </el-form-item>
        <el-form-item :label="t('auditLog.action', 'Action')">
          <el-select v-model="filters.action" clearable placeholder="Any Action" style="width: 150px">
            <el-option label="VIEW" value="VIEW" />
            <el-option label="EXPORT_PDF" value="EXPORT_PDF" />
            <el-option label="EXPORT_DOCX" value="EXPORT_DOCX" />
            <el-option label="DELETE" value="DELETE" />
            <el-option label="CHANGE_PERM" value="CHANGE_PERM" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadData">{{ t("common.search", "Search") }}</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="table-container" v-loading="loading">
      <el-table :data="items" border style="width: 100%" height="100%">
        <el-table-column width="60">
          <template #default="{ row }">
            <el-icon 
              class="star-icon" 
              :class="{ 'is-starred': row.is_starred }"
              @click="toggleStar(row)"
            >
              <StarFilled v-if="row.is_starred" />
              <Star v-else />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column :label="t('auditLog.colTimestamp', 'Timestamp')" width="180">
          <template #default="{ row }">
            {{ formatLocalDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="user_login" :label="t('auditLog.colUser', 'User')" width="120" />
        <el-table-column prop="action" :label="t('auditLog.colAction', 'Action')" width="160">
          <template #default="{ row }">
            <el-tag :type="getActionTagType(row.action)" class="action-tag">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="document_id" :label="t('auditLog.colDocId', 'Doc ID')" width="100" />
        <el-table-column prop="document_title" :label="t('auditLog.colDocTitle', 'Document Title')" min-width="200" show-overflow-tooltip />
        <el-table-column prop="ip_address" :label="t('auditLog.colIp', 'IP Address')" width="140" />
        <el-table-column :label="t('auditLog.colSummary', 'Summary')" min-width="300">
          <template #default="{ row }">
            <div class="summary-wrapper">
              {{ formatSummary(row) }}
            </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/api/client';
import { formatLocalDate } from '@/utils/date';
import { ElMessage } from 'element-plus';
import { Monitor, Star, StarFilled } from "@element-plus/icons-vue";

const { t } = useI18n();

const loading = ref(false);
const items = ref<any[]>([]);
const total = ref(0);
const page = ref(1);
const size = ref(20);

const filters = ref({
  document_id: "",
  user_id: "",
  action: "",
});

function getActionTagType(action: string) {
  if (!action) return "info";
  if (action === "VIEW") return "success";
  if (action.startsWith("EXPORT")) return "warning";
  if (action === "DELETE" || action === "ALERT_TAMPER") return "danger";
  return "info";
}

function formatSummary(row: any) {
  if (row.action === 'ALERT_TAMPER') {
    return t('auditLog.tamperAlert');
  }
  return row.summary;
}

async function toggleStar(row: any) {
  try {
    const { data } = await api.post(`/admin/audit-logs/${row.id}/toggle-star`);
    row.is_starred = data.is_starred;
    ElMessage.success(row.is_starred ? t('common.starred', 'Starred') : t('common.unstarred', 'Unstarred'));
  } catch (err) {
    ElMessage.error(t('common.failed', 'Action failed'));
  }
}

async function loadData() {
  loading.value = true;
  try {
    const params: any = { page: page.value, size: size.value };
    if (filters.value.document_id) params.document_id = filters.value.document_id;
    if (filters.value.user_id) params.user_id = filters.value.user_id;
    if (filters.value.action) params.action = filters.value.action;

    const { data } = await api.get('/admin/audit-logs', { params });
    items.value = data.items;
    total.value = data.total;
  } catch (err) {
    ElMessage.error(t("common.failed", "Failed to load audit logs"));
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.audit-page {
  padding: 0 0 40px;
  background-color: transparent;
  height: calc(100vh - 80px);
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* ── Page Header (Hero Style) ────────────────────────────────── */
.hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 32px 40px;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #7367f0 130%) !important;
  border-radius: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
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
  flex-shrink: 0;
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

/* 1. 给顶部搜索栏套上高透亚克力材质 */
.filters {
  background-color: rgba(255, 255, 255, 0.65) !important; 
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  border-radius: 12px;
  
  padding: 20px 20px 4px 20px;
  margin-bottom: 20px;
}

/* 2. 底部表格容器玻璃化 */
.table-container {
  flex: 1;
  min-height: 0;
  background-color: rgba(255, 255, 255, 0.65) !important; 
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  
  border: 1px solid rgba(255, 255, 255, 0.8) !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.05) !important;
  border-radius: 12px;
  padding: 20px;
}

/* 彻底砸穿 Element 表格内部的实心白底 */
:deep(.el-table),
:deep(.el-table__expanded-cell),
:deep(.el-table th),
:deep(.el-table tr),
:deep(.el-table td) {
  background-color: transparent !important; 
  background: transparent !important;
}

/* 修复表格悬浮时的颜色 */
:deep(.el-table tbody tr:hover > td) {
  background-color: rgba(255, 255, 255, 0.4) !important; 
}

/* 去掉表格底部自带的白线 */
:deep(.el-table::before) {
  display: none !important;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

/* 3. 顺手优化一下底部分页器 */
:deep(.el-pagination button:disabled),
:deep(.el-pagination .btn-next), 
:deep(.el-pagination .btn-prev), 
:deep(.el-pager li) {
  background-color: transparent !important;
}
:deep(.el-pager li.is-active) {
  background-color: var(--el-color-primary) !important;
  color: white !important;
  border-radius: 4px;
}

.action-tag {
  white-space: normal;
  height: auto;
  line-height: 1.2;
  padding: 4px;
  text-align: center;
  word-break: break-all;
  backdrop-filter: blur(4px);
}

.summary-wrapper {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.5;
  font-size: 13px;
}

.star-icon {
  font-size: 18px;
  cursor: pointer;
  color: #94a3b8;
  transition: all 0.2s ease;
}

.star-icon:hover {
  transform: scale(1.2);
  color: #f59e0b;
}

.star-icon.is-starred {
  color: #f59e0b;
}
</style>
