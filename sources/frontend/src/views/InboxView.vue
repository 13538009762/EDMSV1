<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t("inbox.title") }}</h2>
    </div>
    
    <el-card shadow="sm" class="table-card">
      <div class="toolbar">
        <el-button @click="load" :loading="loading" :icon="Refresh">{{ t("inbox.refresh") }}</el-button>
      </div>

      <el-table :data="items" stripe style="width: 100%">
        <el-table-column :label="t('inbox.colDocId')" width="100">
          <template #default="{ row }">
            {{ row.document_id }}
          </template>
        </el-table-column>
        
        <el-table-column :label="t('inbox.colTitle')" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.title }}
          </template>
        </el-table-column>

        <el-table-column :label="t('inbox.colFlow')" width="140">
          <template #default="{ row }">
            <el-tag size="small" type="info">{{ row.flow_type }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="t('inbox.colProgress')" width="120">
          <template #default="{ row }">
            <span style="font-weight: 600; color: var(--el-color-primary);">{{ row.progress.done }}</span> / {{ row.progress.total }}
          </template>
        </el-table-column>
        
        <el-table-column :label="t('inbox.colSubmittedAt')" width="180">
          <template #default="{ row }">
            <div style="font-size: 13px; color: var(--el-text-color-secondary);">
              {{ row.submitted_at?.replace('T', ' ').substring(0, 16) }}
            </div>
          </template>
        </el-table-column>

        <el-table-column :label="t('inbox.colActions')" width="420" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="$router.push(`/doc/${row.document_id}`)">
              {{ t("library.open") }}
            </el-button>

            <el-button type="info" plain size="small" @click="$router.push(`/doc/${row.document_id}/diff`)">
              {{ t("library.diff") }}
            </el-button>

            <el-button type="success" size="small" @click="decide(row.participant_id, 'approve')">
              {{ t("inbox.approve") }}
            </el-button>

            <el-button type="danger" size="small" @click="openReject(row)">
              {{ t("inbox.reject") }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="rejectDlg" :title="t('inbox.rejectTitle')" width="420px" class="custom-dialog">
      <div style="margin-bottom: 8px;">{{ t("inbox.reasonPrompt", "Please provide a reason for rejection:") }}</div>
      <el-input v-model="rejectReason" type="textarea" :rows="4" placeholder="..." />
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="rejectDlg = false">{{ t("inbox.cancel") }}</el-button>
          <el-button type="danger" @click="confirmReject">{{ t("inbox.reject") }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage } from "element-plus";
import { Refresh } from "@element-plus/icons-vue"; // 引入图标

interface InboxRow {
  participant_id: number;
  document_id: number;
  title: string;
  flow_type: string;
  progress: { done: number; total: number };
  submitted_at?: string;
}

const { t } = useI18n();
const items = ref<InboxRow[]>([]);
const loading = ref(false);
const rejectDlg = ref(false);
const rejectReason = ref("");
const rejectPid = ref<number | null>(null);

async function load() {
  loading.value = true;
  try {
    const { data } = await api.get("/approvals/inbox");
    items.value = data.items;
  } finally {
    loading.value = false;
  }
}

async function decide(participantId: number, decision: "approve" | "reject", reason?: string) {
  await api.post(`/approvals/participants/${participantId}/decision`, {
    decision,
    reason: reason || undefined,
  });
  ElMessage.success(t("inbox.submitted"));
  load();
}

function openReject(row: InboxRow) {
  rejectPid.value = row.participant_id;
  rejectReason.value = "";
  rejectDlg.value = true;
}

function confirmReject() {
  if (!rejectPid.value || !rejectReason.value.trim()) {
    ElMessage.warning(t("inbox.reasonRequired"));
    return;
  }
  decide(rejectPid.value, "reject", rejectReason.value);
  rejectDlg.value = false;
}

onMounted(load);
</script>

<style scoped>
.page-container {
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.table-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.toolbar {
  margin-bottom: 16px;
  display: flex;
}
</style>