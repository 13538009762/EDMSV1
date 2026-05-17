<template>
  <div class="page-wrapper">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><Reading /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t("nav.library", "Document Library") }}</h1>
          <p class="page-sub">{{ t("dashboard.subtitle", "Access and manage all organizational documents.") }}</p>
        </div>
      </div>
    </div>

    <el-container class="library-layout">
      <el-aside :width="sidebarCollapsed ? '64px' : '280px'" class="tree-sidebar" :class="{ 'is-collapsed': sidebarCollapsed }">
        <el-card shadow="sm" class="tree-card" :body-style="{ padding: sidebarCollapsed ? '12px 8px' : '12px 4px' }">
          <div class="tree-header">
            <template v-if="!sidebarCollapsed">
              <div class="header-title">
                <el-icon><Folder /></el-icon> {{ t("library.wikiTree", "Wiki Directory") }}
                <el-tooltip :content="t('library.createSpace')" placement="top">
                  <el-button 
                    v-if="authStore.user?.is_super_admin" 
                    size="small" 
                    circle 
                    :icon="Plus" 
                    @click="showCreateSpace = true" 
                    class="add-space-btn"
                    style="margin-left: 8px; transform: scale(0.8);"
                  />
                </el-tooltip>
              </div>
              <el-button link @click="toggleSidebar" class="collapse-btn">
                <el-icon><Fold /></el-icon>
              </el-button>
            </template>
            <template v-else>
              <el-button link @click="toggleSidebar" class="expand-btn">
                <el-icon><Expand /></el-icon>
              </el-button>
            </template>
          </div>
          
          <div v-show="!sidebarCollapsed" class="tree-content">
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
          </div>
          
          <div v-if="sidebarCollapsed" class="collapsed-indicator">
            <div class="vertical-text">{{ t("library.wikiTree", "Wiki Directory") }}</div>
          </div>
        </el-card>
      </el-aside>

      <el-main class="library-main">
        <el-card shadow="sm" class="table-card">
      <div class="toolbar-container" :class="{ 'is-collapsed': toolbarCollapsed }">
        <div class="toolbar" v-show="!toolbarCollapsed">
          <div class="toolbar-left">
            <el-button type="primary" :icon="Plus" @click="createDoc">{{ t("library.newDoc") }}</el-button>
            <el-tag v-if="currentSpaceId" closable @close="clearSpaceFilter" type="info" size="large" effect="plain" style="margin-left: 10px; font-weight: 600;">
              <el-icon><Folder /></el-icon> {{ currentSpaceName }}
            </el-tag>
            <el-tag v-if="currentDeptId" closable @close="clearSpaceFilter" type="success" size="large" effect="plain" style="margin-left: 10px; font-weight: 600;">
              <el-icon><Connection /></el-icon> {{ currentDeptName }}
            </el-tag>
            <el-upload
              :show-file-list="false"
              accept=".docx"
              :before-upload="onImportDocx"
              style="display: inline-flex; margin-right: 8px;"
            >
              <el-button :icon="Upload">{{ t("library.importDocx") }}</el-button>
            </el-upload>
            <el-upload
              :show-file-list="false"
              accept=".pdf"
              :before-upload="onImportPdf"
              style="display: inline-flex; margin-right: 8px;"
            >
              <el-button :icon="Upload">{{ t("library.importPdf") }}</el-button>
            </el-upload>
            <el-upload
              :show-file-list="false"
              accept="image/*"
              :before-upload="onImportImage"
              style="display: inline-flex;"
            >
              <el-button :icon="MagicStick">{{ t("library.importImage", "AI 识图建档") }}</el-button>
            </el-upload>
          </div>
          
          <div class="toolbar-right">
            <div v-if="selectedIds.length > 0" class="selection-actions">
              <span class="selection-count">{{ t('common.selected', 'Selected') }}: {{ selectedIds.length }}</span>
              <el-button type="danger" :icon="Delete" plain @click="batchDelete">{{ t('common.batchDelete') }}</el-button>
              <el-button type="warning" :icon="Share" plain @click="batchShare(true)">{{ t('common.share') }}</el-button>
              <el-button type="info" :icon="Lock" plain @click="batchShare(false)">{{ t('common.unshare') }}</el-button>
              <el-button type="success" :icon="Folder" plain @click="showMove = true">{{ t('library.moveToSpace', 'Move to Space') }}</el-button>
              <el-button type="info" :icon="Close" plain @click="batchClearSpace">{{ t('library.clearSpaces', 'Clear Categories') }}</el-button>
              <el-button type="primary" :icon="ChatDotRound" plain @click="showMultiQa = true">{{ t('library.multiDocQa', '多文档 QA') }}</el-button>
              <el-divider direction="vertical" />
            </div>
  
            <el-input
              v-model="searchQuery"
              :placeholder="t('editor.searchPlaceholder')"
              :prefix-icon="Search"
              clearable
              style="width: 180px"
            />
            <el-select
              v-show="authStore.user?.is_super_admin || authStore.user?.is_manager"
              v-model="currentDeptId"
              clearable
              style="width: 180px"
              :placeholder="t('profile.dept', 'Department')"
              @change="onDeptFilterChange"
            >
              <el-option 
                v-for="d in deptOptions" 
                :key="d.id" 
                :label="formatDeptName(d.name, d.name_en)" 
                :value="d.id.toString()" 
              />
            </el-select>
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
        
        <div class="toolbar-toggle">
          <el-button link @click="toggleToolbar" class="toggle-btn">
            <el-icon v-if="!toolbarCollapsed"><ArrowUp /></el-icon>
            <el-icon v-else><ArrowDown /></el-icon>
            <span v-if="toolbarCollapsed" style="margin-left: 8px; font-size: 12px; color: var(--el-text-color-secondary)">{{ t('library.showToolbar', 'Show Filters & Actions') }}</span>
          </el-button>
        </div>
      </div>

      <el-table :data="paginatedItems" v-loading="loading" stripe style="width: 100%" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="55" />
        <el-table-column prop="doc_number" :label="t('library.colId')" width="140" />
        <el-table-column prop="title" :label="t('library.colTitle')" min-width="180">
          <template #default="{ row }">
            <div style="font-weight: 500; margin-bottom: 4px;">{{ row.title }}</div>
            <div v-if="row.space_names && row.space_names.length" style="display: flex; flex-wrap: wrap; gap: 4px;">
              <el-tag v-for="name in row.space_names" :key="name" size="small" type="info" effect="light" round>
                {{ t('space.' + name, name) }}
              </el-tag>
            </div>
          </template>
        </el-table-column>
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
            {{ formatDeptName(row.owner_department, row.owner_department_en) }}
          </template>
        </el-table-column>
        <el-table-column prop="my_role" :label="t('library.colRole')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.my_role" size="small" :type="row.my_role === 'owner' ? 'primary' : row.my_role === 'approver' ? 'warning' : 'info'" effect="light">
              {{ t('common.roles.' + row.my_role, row.my_role) }}
            </el-tag>
            <span v-else>-</span>
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
        <el-table-column :label="t('library.colActions')" width="160" fixed="right">
          <template #default="{ row }">
            <div class="action-btns">
              <el-button 
                type="primary" 
                size="small" 
                @click="open(row.doc_number || row.id)"
                class="main-action"
              >
                {{ t("library.open") }}
              </el-button>
              
              <el-dropdown trigger="click" @command="(cmd: any) => handleCommand(cmd, row)">
                <el-button size="small" :icon="More" class="more-btn" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item 
                      v-if="row.can_manage_permissions && (row.status === 'draft' || row.status === 'approved')"
                      command="share"
                      :icon="Share"
                    >
                      {{ t("library.share") }}
                    </el-dropdown-item>
                    
                    <el-dropdown-item 
                      v-if="row.status === 'approved'"
                      command="diff"
                      :icon="Connection"
                    >
                      {{ t("library.diff") }}
                    </el-dropdown-item>

                    <el-dropdown-item 
                      v-if="row.is_owner || authStore.user?.is_super_admin"
                      command="move"
                      :icon="Folder"
                    >
                      {{ t("library.moveToSpace", "Move to Space") }}
                    </el-dropdown-item>
                    
                    <el-dropdown-item 
                      v-if="(row.is_owner || authStore.user?.is_super_admin) && (row.status === 'draft' || row.status === 'rejected' || row.status === 'approved')"
                      command="delete"
                      :icon="Delete"
                      divided
                      style="color: var(--el-color-danger)"
                    >
                      {{ t("editor.delete") }}
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          size="small"
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

    <DocumentMoveDialog
      v-model="showMove"
      :doc-ids="selectedIds"
      @saved="onMoved"
    />

    <SpaceCreateDialog
      v-model="showCreateSpace"
      @saved="loadTree"
    />

    <MultiDocQaDialog
      v-model="showMultiQa"
      :doc-ids="selectedIds"
      :selected-docs="selectedRows"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage, ElMessageBox, ElLoading } from "element-plus";
import mammoth from "mammoth";
import type { UploadRawFile } from "element-plus";
import DocumentShareDialog from "@/components/DocumentShareDialog.vue";
import DocumentMoveDialog from "@/components/DocumentMoveDialog.vue";
import SpaceCreateDialog from "@/components/SpaceCreateDialog.vue";
import MultiDocQaDialog from "@/components/MultiDocQaDialog.vue";
import { Search, Plus, Folder, Connection, Upload, Expand, Fold, MagicStick, Refresh, ArrowUp, ArrowDown, Share, Delete, More, Reading, Lock, Close, ChatDotRound } from "@element-plus/icons-vue";
import { formatLocalDate } from "@/utils/date";
import { useAuthStore } from "@/stores/auth";
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
  is_owner?: boolean;
}

const router = useRouter();
const { t, locale, te } = useI18n();
const authStore = useAuthStore();
const items = ref<DocRow[]>([]);
const loading = ref(false);
const scope = ref("");
const statusFilter = ref("");
const shareOpen = ref(false);
const shareDocId = ref<number | null>(null);
const searchQuery = ref("");
const currentSpaceId = ref<string | null>(null);
const currentSpaceName = ref("");
const currentDeptId = ref<string | null>(null);
const currentDeptName = ref("");
const selectedIds = ref<number[]>([]);
const selectedRows = ref<DocRow[]>([]);
const deptOptions = ref<any[]>([]);
const showMove = ref(false);
const showCreateSpace = ref(false);
const showMultiQa = ref(false);

async function batchClearSpace() {
  if (selectedIds.value.length === 0) return;
  try {
    await ElMessageBox.confirm(
      t('library.clearSpacesConfirm', 'Are you sure you want to remove all categories from selected documents?'),
      t('common.warning'),
      { type: 'warning' }
    );
    const loading = ElLoading.service({ text: t('common.processing') });
    await api.post('/documents/batch-move', {
      doc_ids: selectedIds.value,
      space_ids: [],
      append: false
    });
    loading.close();
    ElMessage.success(t('common.success'));
    onMoved();
  } catch {}
}

function onMoved() {
  selectedIds.value = [];
  load();
  loadTree();
}

const formatName = (name: string, nameEn?: string, type: 'dept' | 'space' = 'dept') => {
  if (!name || name === 'Unknown' || name === 'Unassigned') {
    return name === 'Unassigned' ? t('library.scopeMine') : t('common.unknown');
  }
  if (te(`${type}.${name}`)) return t(`${type}.${name}`);
  if (nameEn && te(`${type}.${nameEn}`)) return t(`${type}.${nameEn}`);
  return locale.value === 'zh-CN' ? name : (nameEn || name);
};
const formatDeptName = (name: string, nameEn?: string) => formatName(name, nameEn, 'dept');
const formatSpaceName = (name: string, nameEn?: string) => formatName(name, nameEn, 'space');

const sidebarCollapsed = ref(false);
const toolbarCollapsed = ref(false);

function toggleSidebar() {
  sidebarCollapsed.value = !sidebarCollapsed.value;
}

function toggleToolbar() {
  toolbarCollapsed.value = !toolbarCollapsed.value;
}

function handleSelectionChange(selection: DocRow[]) {
  selectedIds.value = selection.map(row => row.id);
  selectedRows.value = selection;
}

async function batchDelete() {
  const selectedDocs = items.value.filter(item => selectedIds.value.includes(item.id));
  const authorizedIds = selectedDocs
    .filter(doc => doc.is_owner)
    .map(doc => doc.id);

  if (authorizedIds.length === 0) {
    ElMessage.error(t('library.allUnauthorized'));
    return;
  }

  if (authorizedIds.length < selectedIds.value.length) {
    ElMessage.warning(t('library.someUnauthorized'));
  }

  try {
    await ElMessageBox.confirm(
      t("editor.deleteDocConfirm"),
      t("common.warning"),
      { type: "warning" }
    );
    const { data } = await api.post("/documents/batch-delete", { doc_ids: authorizedIds });
    if (data.errors && data.errors.length > 0) {
      ElMessage.warning(data.errors.join('\n'));
    } else {
      ElMessage.success(t("common.success"));
    }
    await load();
    selectedIds.value = [];
  } catch (err: any) {
    if (err !== 'cancel') {
      const msg = err.response?.data?.error || err.message || t("common.failed");
      ElMessage.error(msg);
    }
  }
}

async function batchShare(isPublic: boolean) {
  const selectedDocs = items.value.filter(item => selectedIds.value.includes(item.id));
  const authorizedIds = selectedDocs
    .filter(doc => doc.can_manage_permissions)
    .map(doc => doc.id);

  if (authorizedIds.length === 0) {
    ElMessage.error(t('library.allUnauthorized'));
    return;
  }

  if (authorizedIds.length < selectedIds.value.length) {
    ElMessage.warning(t('library.someUnauthorized'));
  }

  try {
    await api.post("/documents/batch-share", { 
      doc_ids: authorizedIds,
      is_public: isPublic
    });
    ElMessage.success(t("common.success"));
    await load();
    selectedIds.value = [];
  } catch {}
}

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
    if (currentDeptId.value) params.dept_id = currentDeptId.value;
    const { data } = await api.get("/documents", { params });
    items.value = data.items as DocRow[];
  } finally {
    loading.value = false;
  }
}

const treeData = ref([]);
const defaultProps = {
  children: "children",
  label: (data: any) => {
    if (data.is_dept) return formatDeptName(data.name, data.name_en);
    if (data.is_space) return formatSpaceName(data.name, data.name_en);
    return data.title || data.name;
  },
};

async function loadTree() {
  try {
    const { data } = await api.get('/documents/tree');
    treeData.value = data.items;
  } catch (err) {
    console.error(err);
  }
}

async function loadDeptOptions() {
  try {
    const { data } = await api.get('/users/departments');
    deptOptions.value = data;
  } catch (err) {
    console.error(err);
  }
}

function onDeptFilterChange(val: string) {
  currentSpaceId.value = null;
  currentSpaceName.value = "";
  if (!val) {
    currentDeptId.value = null;
    currentDeptName.value = "";
  } else {
    const dept = deptOptions.value.find(d => d.id.toString() === val);
    if (dept) {
      currentDeptName.value = formatDeptName(dept.name, dept.name_en);
    }
  }
  load();
}

function handleNodeClick(data: any) {
  if (data.is_dept) {
    currentSpaceId.value = null;
    currentSpaceName.value = "";
    currentDeptId.value = data.id.toString().replace("dept_", "");
    currentDeptName.value = formatDeptName(data.name, data.name_en);
    load();
  } else if (data.is_space) {
    currentDeptId.value = null;
    currentDeptName.value = "";
    const sid = data.id || data.space_id;
    if (sid === "space_unassigned") {
      currentSpaceId.value = "unassigned";
      currentSpaceName.value = t("library.scopeMine");
    } else {
      currentSpaceId.value = sid.toString().replace("space_", "");
      currentSpaceName.value = formatSpaceName(data.name, data.name_en);
    }
    load();
  } else if (data.id && !data.is_space && !data.is_dept) {
    open(data.doc_number || data.id);
  }
}

function handleCommand(cmd: string, row: DocRow) {
    if (cmd === 'share') openShare(row.id);
    if (cmd === 'diff') router.push({ name: 'diff', params: { id: row.doc_number || row.id } });
    if (cmd === 'move') {
      selectedIds.value = [row.id];
      showMove.value = true;
    }
    if (cmd === 'delete') confirmDelete(row.id);
}

function clearSpaceFilter() {
  currentSpaceId.value = null;
  currentSpaceName.value = "";
  currentDeptId.value = null;
  currentDeptName.value = "";
  load();
}

async function createDoc() {
  try {
    const payload: any = { title: t("common.untitled") };
    if (currentSpaceId.value && currentSpaceId.value !== "unassigned") {
      payload.space_id = currentSpaceId.value;
    }
    
    const { data } = await api.post("/documents", payload);
    if (data && data.id) {
        router.push({ name: "editor", params: { id: data.doc_number || data.id } });
    } else {
        throw new Error("Invalid document ID received");
    }
  } catch (err: any) {
    console.error("Document creation failed:", err);
    ElMessage.error(err.response?.data?.error || t("library.createFailed"));
  }
}

function open(id: number | string) {
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

async function onImportPdf(file: UploadRawFile) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    if (currentSpaceId.value && currentSpaceId.value !== "unassigned") {
      formData.append("space_id", currentSpaceId.value);
    }

    loading.value = true;
    await api.post("/documents/import-pdf", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    
    ElMessage.success(t("library.importPdfSuccess"));
    await load();
  } catch (err) {
    console.error("Import PDF error:", err);
    ElMessage.error(t("library.importPdfFailed"));
  } finally {
    loading.value = false;
  }
  return false;
}

async function onImportImage(file: any) {
  const loadingInstance = ElLoading.service({ text: t('library.importImageLoading', 'AI 正在识别并排版...'), background: 'rgba(0, 0, 0, 0.7)' });
  try {
    const formData = new FormData();
    formData.append('file', file);
    const { data } = await api.post('/ai/import-image', formData);
    if (data.code === 200) {
      ElMessage.success(t('library.importImageSuccess', '识别成功'));
      router.push({ name: 'editor', params: { id: data.data.doc_number || data.data.document_id } });
    }
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('library.importImageFailed', '识别失败'));
  } finally {
    loadingInstance.close();
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
  loadDeptOptions();
});
</script>

<style scoped>
.page-wrapper {
  padding: 0 0 40px;
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

.library-container {
  padding: 0;
  background-color: transparent;
  min-height: auto;
}

.library-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
}

.tree-card {
  height: calc(100vh - 120px);
  border-radius: 12px;
  border: none;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
  display: flex;
  flex-direction: column;
}

.action-btns {
  display: flex;
  align-items: center;
  gap: 8px;
}

.main-action {
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #7367f0 100%);
  border: none;
  transition: all 0.3s ease;
}

.main-action:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(115, 103, 240, 0.3);
}

.more-btn {
  border: 1px solid var(--el-border-color-lighter);
  background: #fff;
  color: var(--el-text-color-secondary);
}

.more-btn:hover {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}

:deep(.el-table__row) {
  transition: background-color 0.2s ease;
}

:deep(.el-table__row:hover > td) {
  background-color: var(--el-color-primary-light-9) !important;
}

.status-tag {
    font-weight: 500;
    border-radius: 6px;
    padding: 0 10px;
}

.pagination-wrapper {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
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
  transition: width 0.3s ease;
}
.tree-sidebar.is-collapsed {
  border-right: none;
}
.tree-card {
  height: 100%;
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
  display: flex;
  flex-direction: column;
  transition: all 0.3s ease;
}
.tree-header {
  font-family: var(--app-font-title);
  font-weight: 700;
  font-size: 16px;
  color: #1e1b4b;
  margin-bottom: 12px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  height: 36px;
  border-bottom: 2px solid rgba(99, 102, 241, 0.1);
}
.header-title {
  display: flex;
  align-items: center;
  gap: 8px;
  overflow: hidden;
  white-space: nowrap;
}
.collapse-btn, .expand-btn {
  padding: 4px;
  font-size: 18px;
}
.expand-btn {
  margin: 0 auto;
}
.tree-content {
  flex: 1;
  overflow-y: auto;
}
.collapsed-indicator {
  flex: 1;
  display: flex;
  justify-content: center;
  align-items: center;
  padding-top: 20px;
}
.vertical-text {
  writing-mode: vertical-lr;
  color: var(--el-text-color-placeholder);
  font-size: 12px;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.library-main {
  padding: 0;
  overflow: hidden;
}

.toolbar-container {
  margin-bottom: 10px;
  transition: all 0.3s ease;
}
.toolbar-container.is-collapsed {
  margin-bottom: 0px;
}
.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
  margin-bottom: 8px;
  padding: 4px 0;
  transition: all 0.3s ease;
}
.toolbar-toggle {
  display: flex;
  justify-content: center;
  border-top: 1px solid var(--el-border-color-extra-light);
  margin-top: 4px;
}
.toggle-btn {
  width: 100%;
  height: 24px;
  font-size: 14px;
  color: var(--el-text-color-placeholder);
}
.toggle-btn:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary);
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
.selection-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--el-color-primary-light-9);
  padding: 4px 12px;
  border-radius: 8px;
  border: 1px solid var(--el-color-primary-light-8);
  animation: slideIn 0.3s ease;
}

.selection-count {
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-right: 8px;
  padding: 2px 8px;
  background: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.05);
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}
</style>