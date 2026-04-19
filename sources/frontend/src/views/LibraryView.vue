<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t("nav.library", "Document Library") }}</h2>
    </div>

    <el-container class="library-layout">
      <el-aside width="200px" class="tree-sidebar">
        <el-card shadow="sm" class="tree-card" :body-style="{ padding: '12px 4px' }">
          <div class="tree-header">
            <el-icon><Folder /></el-icon> {{ t("library.wikiTree", "Wiki Directory") }}
          </div>
          <el-tree
            :data="treeData"
            :props="defaultProps"
            @node-click="handleNodeClick"
            highlight-current
            :expand-on-click-node="false"
            class="custom-tree"
          >
            <template #default="{ node, data }">
              <span class="custom-tree-node">
                <el-icon v-if="data.is_space"><Connection /></el-icon>
                <el-icon v-else><Document /></el-icon>
                <span class="node-label" :title="node.label">{{ node.label }}</span>
              </span>
            </template>
          </el-tree>
        </el-card>
      </el-aside>

      <el-main class="library-main">
        <el-card shadow="sm" class="table-card">
      <div class="toolbar">
        <div class="toolbar-left">
          <el-button type="primary" :icon="Plus" @click="createDoc">{{ t("library.newDoc") }}</el-button>
          <el-tag v-if="currentSpaceId" closable @close="clearSpaceFilter" type="info" size="large" effect="plain" style="margin-left: 10px; font-weight: 600;">
            <el-icon><Folder /></el-icon> {{ currentSpaceName }}
          </el-tag>
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
          <el-button-group v-if="selectedIds.length > 0" style="margin-right: 12px;">
            <el-button type="danger" @click="batchDelete">{{ t('common.delete', 'Batch Delete') }} ({{ selectedIds.length }})</el-button>
            <el-button type="warning" @click="batchShare(true)">{{ t('common.share', 'Share All') }}</el-button>
            <el-button type="info" @click="batchShare(false)">{{ t('common.unshare', 'Unshare All') }}</el-button>
          </el-button-group>

          <el-input
            v-model="searchQuery"
            :placeholder="t('editor.searchPlaceholder')"
            :prefix-icon="Search"
            clearable
            style="width: 200px"
          />
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

      <el-table :data="paginatedItems" v-loading="loading" stripe style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="doc_number" :label="t('library.colId')" width="140" />
        <el-table-column prop="title" :label="t('library.colTitle')" min-width="180" />
        <el-table-column prop="status" :label="t('library.colStatus')" width="160">
          <template #default="{ row }">
            <el-tag :type="row.status === 'approved' ? 'success' : row.status === 'rejected' ? 'danger' : row.status === 'in_approval' ? 'warning' : 'info'">
              {{ t('common.status.' + row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="owner_name" :label="t('library.colOwner')" min-width="120" />
        <el-table-column prop="owner_department" :label="t('library.colDepartment')" min-width="140">
          <template #default="{ row }">
            {{ t('dept.' + row.owner_department, row.owner_department) }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" :label="t('library.colUpdatedAt')" width="170">
          <template #default="{ row }">
            <div v-if="row.updated_at" style="font-size: 13px; color: var(--el-text-color-secondary);">
              {{ formatLocalDate(row.updated_at) }}
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
              v-if="row.can_manage_permissions && (row.status === 'draft' || row.status === 'approved')"
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

            <el-button
              v-if="row.is_owner && (row.status === 'draft' || row.status === 'rejected')"
              type="danger"
              plain
              size="small"
              @click="confirmDelete(row.id)"
            >
              {{ t("editor.delete") }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          small
          background
          layout="prev, pager, next, total"
          :total="filteredItems.length"
        />
      </div>
        </el-card>
      </el-main>
    </el-container>

    <DocumentShareDialog
      v-model="shareOpen"
      :document-id="shareDocId"
      @saved="load"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage, ElMessageBox } from "element-plus";
import mammoth from "mammoth";
import type { UploadRawFile } from "element-plus";
import DocumentShareDialog from "@/components/DocumentShareDialog.vue";
import { Plus, Upload, Refresh, Search, Folder, Document, Connection } from "@element-plus/icons-vue"; // 引入图标
import { formatLocalDate } from "@/utils/date";
import { Editor } from "@tiptap/vue-3";
import StarterKit from "@tiptap/starter-kit";
import Image from "@tiptap/extension-image";
import TextAlign from "@tiptap/extension-text-align";
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import Underline from "@tiptap/extension-underline";

interface DocRow {
  id: number;
  title: string;
  status: string;
  my_role?: string;
  can_manage_permissions?: boolean;
  owner_name?: string;
  owner_department?: string;
  doc_number?: string;
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
const searchQuery = ref("");
const currentSpaceId = ref<string | null>(null);
const currentSpaceName = ref("");
const selectedIds = ref<number[]>([]);

function handleSelectionChange(selection: DocRow[]) {
  selectedIds.value = selection.map(row => row.id);
}

async function batchDelete() {
  try {
    await ElMessageBox.confirm(
      t("editor.deleteConfirm"),
      t("common.warning"),
      { type: "warning" }
    );
    await api.post("/documents/batch-delete", { doc_ids: selectedIds.value });
    ElMessage.success(t("common.success"));
    await load();
  } catch {}
}

async function batchShare(isPublic: boolean) {
  try {
    await api.post("/documents/batch-share", { 
      doc_ids: selectedIds.value,
      is_public: isPublic
    });
    ElMessage.success(t("common.success"));
    await load();
  } catch {}
}

// Pagination
const currentPage = ref(1);
const pageSize = ref(10);

const filteredItems = computed(() => {
  if (!searchQuery.value) return items.value;
  const q = searchQuery.value.toLowerCase();
  return items.value.filter(item => 
    item.title?.toLowerCase().includes(q) || 
    item.doc_number?.toLowerCase().includes(q)
  );
});

const paginatedItems = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value;
  return filteredItems.value.slice(start, start + pageSize.value);
});

async function load() {
  loading.value = true;
  try {
    const params: Record<string, string> = { scope: scope.value || "all" };
    if (statusFilter.value) params.status = statusFilter.value;
    if (currentSpaceId.value) params.space_id = currentSpaceId.value;
    const { data } = await api.get("/documents", { params });
    items.value = data.items as DocRow[];
  } finally {
    loading.value = false;
  }
}

const treeData = ref([]);
const defaultProps = {
  children: "children",
  label: (data: any) => data.title || data.name,
};

async function loadTree() {
  try {
    const { data } = await api.get('/documents/tree');
    treeData.value = data.items;
  } catch (err) {
    console.error(err);
  }
}

function handleNodeClick(data: any) {
  if (data.is_space) {
    // 点击空间节点，切换表格过滤
    const sid = data.id || data.space_id;
    if (sid === "space_unassigned") {
      currentSpaceId.value = "unassigned";
      currentSpaceName.value = t("library.scopeMine");
    } else {
      currentSpaceId.value = sid.toString().replace("space_", "");
      currentSpaceName.value = data.name || data.title;
    }
    load();
  } else if (data.id) {
    // 点击文档节点，跳转编辑器
    router.push({ name: "editor", params: { id: data.id } });
  }
}

function clearSpaceFilter() {
  currentSpaceId.value = null;
  currentSpaceName.value = "";
  load();
}

async function createDoc() {
  try {
    const payload: any = { title: t("common.untitled") };
    if (currentSpaceId.value && currentSpaceId.value !== "unassigned") {
      payload.space_id = currentSpaceId.value;
    }
    
    const { data } = await api.post("/documents", payload);
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
    const payload: any = { title: file.name.replace(/\.docx$/, "") };
    if (currentSpaceId.value && currentSpaceId.value !== "unassigned") {
      payload.space_id = currentSpaceId.value;
    }
    const { data: docData } = await api.post("/documents", payload);
    const docId = docData.id;
    
    const ab = await file.arrayBuffer();
    const { value: html } = await mammoth.convertToHtml({ arrayBuffer: ab }, {
      convertImage: mammoth.images.imgElement(function(element) {
        return element.read("base64").then(function(imageBuffer) {
          return {
            src: "data:" + element.contentType + ";base64," + imageBuffer
          };
        });
      })
    });
    
    // Use a headless editor to convert HTML to TipTap JSON
    const tempEditor = new Editor({
      extensions: [
        StarterKit,
        Underline,
        Image.configure({ allowBase64: true }),
        Table.configure({ resizable: true }),
        TableRow,
        TableHeader,
        TableCell,
        TextAlign.configure({ types: ["heading", "paragraph", "image"] }),
      ],
      content: html,
    });
    
    const content_json = tempEditor.getJSON();
    tempEditor.destroy();

    await api.put(`/documents/${docId}/content`, {
      content_json: JSON.stringify(content_json),
    });
    
    ElMessage.success(t("library.importDocxSuccess"));
    await load();
  } catch (error) {
    console.error("Import DOCX error:", error);
    ElMessage.error(t("library.importDocxFailed"));
  }
  return false;
}

async function confirmDelete(id: number) {
  try {
    await ElMessageBox.confirm(
      t("editor.deleteConfirm"),
      t("common.warning", "Warning"),
      {
        confirmButtonText: t("common.ok", "OK"),
        cancelButtonText: t("inbox.cancel"),
        type: "warning",
      }
    );
    await api.delete(`/documents/${id}`);
    ElMessage.success(t("editor.deleteSuccess"));
    await load();
  } catch (err) {
    if (err !== "cancel") {
      ElMessage.error(t("editor.deleteFailed"));
    }
  }
}

onMounted(() => {
  load();
  loadTree();
});
</script>

<style scoped>
.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.page-container {
  padding: 24px 32px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.page-header h2 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  letter-spacing: -0.5px;
}

.table-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.04);
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

.library-layout {
  gap: 16px;
}
.tree-sidebar {
  overflow: hidden;
}
.tree-card {
  height: 100%;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}
.tree-header {
  font-weight: 600;
  font-size: 14px;
  color: var(--el-text-color-primary);
  margin-bottom: 10px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  gap: 8px;
}
.library-main {
  padding: 0;
  overflow: hidden;
}
 
.custom-tree {
  background: transparent;
}
.custom-tree-node {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  width: 100%;
}
.node-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>