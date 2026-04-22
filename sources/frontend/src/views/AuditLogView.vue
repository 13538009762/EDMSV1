<template>
  <div class="audit-page">
    <div class="header">
      <h2>{{ t("auditLog.title", "Operation Trail") }}</h2>
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
        <el-table-column prop="summary" :label="t('auditLog.colSummary', 'Summary')" min-width="250" show-overflow-tooltip />
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
  padding: 24px;
  background-color: var(--el-bg-color-page);
  height: calc(100vh - 80px); /* Adjust based on your header height */
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.header {
  margin-bottom: 24px;
}

.header h2 {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.filters {
  background: white;
  padding: 16px 16px 0 16px;
  margin-bottom: 16px;
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
}

.table-container {
  flex: 1;
  background: white;
  min-height: 0; /* important for flex overflow */
  border-radius: 8px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.05);
  padding: 16px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}

.action-tag {
  white-space: normal;
  height: auto;
  line-height: 1.2;
  padding: 4px;
  text-align: center;
  word-break: break-all;
}
</style>
