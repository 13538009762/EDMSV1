<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t("nav.library", "Document Library") }}</h2>
    </div>

    <el-card shadow="sm" class="table-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" :icon="Plus" @click="createDoc">{{ t("library.newDoc") }}</el-button>
          <el-upload
            :show-file-list="false"
            accept=".docx"
            :before-upload="onImportDocx"
            style="display: inline-flex;"
          >
            <el-button :icon="Upload">{{ t("library.importDocx") }}</el-button>
          </el-upload>
        </div>
        
        <div class="toolbar-right">
          <el-select
            v-model="scope"
            clearable
            style="width: 200px"
            :placeholder="t('library.scopePlaceholder')"
            @change="load"
          >
            <el-option :label="t('library.scopeAll')" value="" />
            <el-option :label="t('library.scopeMine')" value="mine" />
            <el-option :label="t('library.scopeCollab')" value="collab" />
            <el-option :label="t('library.scopeDepartment')" value="department" />
          </el-select>
          <el-select
            v-model="statusFilter"
            clearable
            style="width: 180px"
            :placeholder="t('library.statusFilter')"
            @change="load"
          >
            <el-option :label="t('library.statusAll')" value="" />
            <el-option :label="t('library.statusDraft')" value="draft" />
            <el-option :label="t('library.statusInApproval')" value="in_approval" />
            <el-option :label="t('library.statusApproved')" value="approved" />
            <el-option :label="t('library.statusRejected')" value="rejected" />
          </el-select>
          <el-button @click="load" :icon="Refresh">{{ t("library.refresh") }}</el-button>
        </div>
      </div>

      <el-table :data="items" v-loading="loading" stripe style="width: 100%">
        <el-table-column prop="id" :label="t('library.colId')" width="80" />
        <el-table-column prop="title" :label="t('library.colTitle')" min-width="180" />
        <el-table-column prop="status" :label="t('library.colStatus')" width="160">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : row.status === 'in_approval' ? 'warning' : 'info'">
              {{ t('common.status.' + row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" :label="t('library.colOwner')" min-width="120" />
        <el-table-column prop="owner_department" :label="t('library.colDepartment')" min-width="140" />
        <el-table-column prop="updated_at" :label="t('library.colUpdatedAt')" width="170">
          <template #default="{ row }">
            <div v-if="row.updated_at" style="font-size: 13px; color: var(--el-text-color-secondary);">
              {{ row.updated_at.replace('T', ' ').substring(0, 16) }}
            </div>
            <span v-else style="color: var(--el-text-color-placeholder);">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="my_role" :label="t('library.colRole')" width="100" />
        <el-table-column :label="t('library.colActions')" width="260" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" @click="open(row.id)">
              {{ t("library.open") }}
            </el-button>
            
            <el-button
              v-if="row.can_manage_permissions && row.status === 'draft'"
              type="warning"
              plain
              size="small"
              @click="openShare(row.id)"
            >
              {{ t("library.share") }}
            </el-button>
            
            <el-button
              v-if="row.status === 'approved'"
              type="info"
              plain
              size="small"
              @click="router.push({ name: 'diff', params: { id: row.id } })"
            >
              {{ t("library.diff") }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <DocumentShareDialog
      v-model="shareOpen"
      :document-id="shareDocId"
      @saved="load"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage } from "element-plus";
import mammoth from "mammoth";
import type { UploadRawFile } from "element-plus";
import DocumentShareDialog from "@/components/DocumentShareDialog.vue";
import { Plus, Upload, Refresh } from "@element-plus/icons-vue"; // 引入图标

interface DocRow {
  id: number;
  title: string;
  status: string;
  my_role?: string;
  can_manage_permissions?: boolean;
  owner_name?: string;
  owner_department?: string;
  updated_at?: string;
}

const router = useRouter();
const { t } = useI18n();
const items = ref<DocRow[]>([]);
const loading = ref(false);
const scope = ref("");
const statusFilter = ref("");
const shareOpen = ref(false);
const shareDocId = ref<number | null>(null);

async function load() {
  loading.value = true;
  try {
    const params: Record<string, string> = { scope: scope.value || "all" };
    if (statusFilter.value) params.status = statusFilter.value;
    const { data } = await api.get("/documents", { params });
    items.value = data.items as DocRow[];
  } finally {
    loading.value = false;
  }
}

async function createDoc() {
  try {
    const { data } = await api.post("/documents", { title: t("common.untitled") });
    router.push({ name: "editor", params: { id: data.id } });
  } catch {
    ElMessage.error(t("library.createFailed"));
  }
}

function open(id: number) {
  router.push({ name: "editor", params: { id } });
}

function openShare(id: number) {
  shareDocId.value = id;
  shareOpen.value = true;
}

async function onImportDocx(file: UploadRawFile) {
  try {
    const { data: docData } = await api.post("/documents", { title: file.name.replace(/\.docx$/, "") });
    const docId = docData.id;
    
    const ab = await file.arrayBuffer();
    const { value: rawText } = await mammoth.extractRawText({ arrayBuffer: ab });
    
    const lines = rawText.split('\n').filter(line => line.trim().length > 0);
    const content = {
      type: "doc",
      content: lines.length > 0 ? lines.map(line => ({
        type: "paragraph",
        attrs: { textAlign: "left" },
        content: line.trim() ? [{ type: "text", text: line.trim() }] : [],
      })) : [{
        type: "paragraph",
        attrs: { textAlign: "left" },
        content: [],
      }],
    };
    
    await api.put(`/documents/${docId}/content`, {
      content_json: JSON.stringify(content),
    });
    
    ElMessage.success(t("library.importDocxSuccess"));
    await load();
  } catch (error) {
    console.error("Import DOCX error:", error);
    ElMessage.error(t("library.importDocxFailed"));
  }
  return false;
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
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 20px;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>