<template>
  <div class="admin-tmpl-page" v-loading="loading">
    <!-- Page Header -->
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><Grid /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t('templates.adminTitle', 'Template Management') }}</h1>
          <p class="page-sub">{{ t('templates.adminSubtitle', 'Create, edit, and publish templates for all employees.') }}</p>
        </div>
      </div>
      <el-button type="primary" class="hero-action-btn" :icon="Plus" @click="openCreate" id="create-template-btn" size="large">
        {{ t('templates.create', 'New Template') }}
      </el-button>
    </div>

    <!-- Stats Strip -->
    <div class="stats-strip">
      <div class="stat-card">
        <span class="stat-num">{{ auth.user?.login_name === 'admin' ? items.length : ownItems.length }}</span>
        <span class="stat-label">{{ auth.user?.login_name === 'admin' ? t('templates.statTotal', 'Total Templates') : t('personal.createdDocs', 'My Templates') }}</span>
      </div>
      <div class="stat-card published">
        <span class="stat-num">{{ publishedCount }}</span>
        <span class="stat-label">{{ t('templates.statPublished', 'Published') }}</span>
      </div>
      <div class="stat-card draft">
        <span class="stat-num">{{ draftCount }}</span>
        <span class="stat-label">{{ t('templates.statDraft', 'Draft') }}</span>
      </div>
    </div>

    <!-- Templates Table -->
    <div class="table-card">
      <div class="table-toolbar">
        <el-input
          v-model="search"
          :placeholder="t('templates.searchPlaceholder', 'Search templates...')"
          clearable
          class="table-search"
          id="admin-template-search"
        >
          <template #prefix><el-icon><Search /></el-icon></template>
        </el-input>
        <el-radio-group v-model="filterStatus" size="small">
          <el-radio-button value="all">{{ t('common.ok', 'All') }}</el-radio-button>
          <el-radio-button value="published">{{ t('templates.statPublished', 'Published') }}</el-radio-button>
          <el-radio-button value="draft">{{ t('templates.statDraft', 'Draft') }}</el-radio-button>
        </el-radio-group>
      </div>

      <el-table
        :data="filteredItems"
        border
        stripe
        class="tmpl-table"
        empty-text="No templates found"
        id="admin-template-table"
      >
        <el-table-column prop="title" :label="t('templates.colTitle', 'Title')" min-width="200">
          <template #default="{ row }">
            <div class="title-cell">
              <el-icon class="title-icon"><Document /></el-icon>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" :label="t('templates.colDesc', 'Description')" min-width="240">
          <template #default="{ row }">
            <span class="desc-text">{{ row.description || '—' }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="owner_name" :label="t('templates.colOwner', 'Author')" width="130" />

        <el-table-column prop="updated_at" :label="t('templates.colUpdated', 'Last Updated')" width="170">
          <template #default="{ row }">
            <span class="date-text">{{ formatDate(row.updated_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column :label="t('templates.colStatus', 'Status')" width="130" align="center">
          <template #default="{ row }">
            <el-tag
              :type="row.is_public ? 'success' : 'warning'"
              effect="dark"
              size="small"
              class="status-tag"
            >
              {{ row.is_public ? t('templates.statusPublished', 'Published') : t('templates.statusDraft', 'Draft') }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column :label="t('common.actions', 'Actions')" width="260" align="center" fixed="right">
          <template #default="{ row }">
            <div class="action-btns" v-if="canManage(row)">
              <!-- Edit in rich editor -->
              <el-tooltip :content="t('templates.editContent', 'Edit Content')" placement="top">
                <el-button
                  size="small"
                  type="primary"
                  :icon="Edit"
                  circle
                  @click="openInEditor(row)"
                  :id="`tmpl-edit-${row.id}`"
                />
              </el-tooltip>
              <!-- Edit meta -->
              <el-tooltip :content="t('templates.editMeta', 'Edit Info')" placement="top">
                <el-button
                  size="small"
                  :icon="EditPen"
                  circle
                  @click="openEdit(row)"
                  :id="`tmpl-meta-${row.id}`"
                />
              </el-tooltip>
              <!-- Publish / Unpublish -->
              <el-tooltip :content="row.is_public ? t('templates.unpublish', 'Unpublish') : t('templates.publish', 'Publish')" placement="top">
                <el-button
                  size="small"
                  :type="row.is_public ? 'warning' : 'success'"
                  :icon="row.is_public ? Hide : View"
                  circle
                  @click="togglePublish(row)"
                  :id="`tmpl-pub-${row.id}`"
                />
              </el-tooltip>
              <!-- Delete -->
              <el-tooltip :content="t('common.delete', 'Delete')" placement="top">
                <el-popconfirm
                  :title="t('templates.deleteConfirm', 'Permanently delete this template?')"
                  @confirm="deleteTemplate(row)"
                  :confirm-button-text="t('common.ok', 'OK')"
                  :cancel-button-text="t('common.cancel', 'Cancel')"
                >
                  <template #reference>
                    <el-button
                      size="small"
                      type="danger"
                      :icon="Delete"
                      circle
                      :id="`tmpl-del-${row.id}`"
                    />
                  </template>
                </el-popconfirm>
              </el-tooltip>
            </div>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create / Edit Dialog -->
    <el-dialog
      v-model="dialogVisible"
      :title="editMode === 'create' ? t('templates.create', 'New Template') : t('templates.editMeta', 'Edit Template Info')"
      width="520px"
      destroy-on-close
      id="template-form-dialog"
    >
      <el-form :model="form" label-position="top" ref="formRef" :rules="rules">
        <el-form-item :label="t('templates.colTitle', 'Title')" prop="title">
          <el-input v-model="form.title" :placeholder="t('templates.titlePlaceholder', 'e.g. Meeting Minutes')" maxlength="512" show-word-limit />
        </el-form-item>
        <el-form-item :label="t('templates.colDesc', 'Description')" prop="description">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="3"
            :placeholder="t('templates.descPlaceholder', 'Short description shown in the gallery...')"
            maxlength="512"
            show-word-limit
          />
        </el-form-item>
        <el-form-item :label="t('templates.colStatus', 'Status')">
          <el-switch
            v-model="form.is_public"
            :active-text="t('templates.statusPublished', 'Published — visible to all')"
            :inactive-text="t('templates.statusDraft', 'Draft — hidden from gallery')"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">{{ t('common.cancel', 'Cancel') }}</el-button>
          <el-button type="primary" @click="submitForm" :loading="saving" id="template-form-submit">
            {{ editMode === 'create' ? t('templates.createAndEdit', 'Create & Edit Content') : t('common.save', 'Save') }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import api from '@/api/client';
import { useAuthStore } from '@/stores/auth';
import { ElMessage } from 'element-plus';
import {
  Plus, Edit, EditPen, Delete, Search, Setting,
  Document, View, Hide, Grid
} from '@element-plus/icons-vue';

const { t } = useI18n();
const router = useRouter();
const auth = useAuthStore();
const loading = ref(false);
const saving = ref(false);
const items = ref<any[]>([]);
const search = ref('');
const filterStatus = ref<'all' | 'published' | 'draft'>('all');
const dialogVisible = ref(false);
const editMode = ref<'create' | 'edit'>('create');
const editingId = ref<number | null>(null);
const formRef = ref<any>(null);

const form = reactive({ title: '', description: '', is_public: false });
const rules = {
  title: [{ required: true, message: t('common.requiredFields', 'Required'), trigger: 'blur' }]
};

const ownItems = computed(() => items.value.filter(i => i.owner_id === auth.user?.id));
const publishedCount = computed(() => ownItems.value.filter(i => i.is_public).length);
const draftCount = computed(() => ownItems.value.filter(i => !i.is_public).length);

const filteredItems = computed(() => {
  let list = items.value;
  if (filterStatus.value === 'published') list = list.filter(i => i.is_public);
  if (filterStatus.value === 'draft') list = list.filter(i => !i.is_public);
  const q = search.value.trim().toLowerCase();
  if (q) list = list.filter(i => i.title.toLowerCase().includes(q) || (i.description || '').toLowerCase().includes(q));
  return list;
});

const canManage = (row: any) => {
  return auth.user?.login_name === 'admin' || row.owner_id === auth.user?.id;
};

function formatDate(iso: string | null): string {
  if (!iso) return '—';
  return new Date(iso).toLocaleString();
}

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get('/templates/admin');
    items.value = data.items;
  } catch {
    ElMessage.error(t('common.failed', 'Failed to load'));
  } finally {
    loading.value = false;
  }
}

function openCreate() {
  editMode.value = 'create';
  editingId.value = null;
  Object.assign(form, { title: '', description: '', is_public: false });
  dialogVisible.value = true;
}

function openEdit(row: any) {
  editMode.value = 'edit';
  editingId.value = row.id;
  Object.assign(form, { title: row.title, description: row.description, is_public: row.is_public });
  dialogVisible.value = true;
}

function openInEditor(row: any) {
  router.push(`/doc/${row.id}`);
}

async function submitForm() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    if (editMode.value === 'create') {
      const { data } = await api.post('/templates/admin', { ...form });
      ElMessage.success(t('templates.createSuccess', 'Template created! Opening editor…'));
      dialogVisible.value = false;
      await loadData();
      // Navigate to editor so admin can fill content
      router.push(`/doc/${data.id}`);
    } else {
      await api.patch(`/templates/admin/${editingId.value}`, { ...form });
      ElMessage.success(t('common.success', 'Saved'));
      dialogVisible.value = false;
      await loadData();
    }
  } catch {
    ElMessage.error(t('common.failed', 'Operation failed'));
  } finally {
    saving.value = false;
  }
}

async function togglePublish(row: any) {
  const endpoint = row.is_public
    ? `/templates/admin/${row.id}/unpublish`
    : `/templates/admin/${row.id}/publish`;
  try {
    await api.post(endpoint);
    row.is_public = !row.is_public;
    ElMessage.success(
      row.is_public
        ? t('templates.publishedOk', 'Template published — now visible to all employees')
        : t('templates.unpublishedOk', 'Template hidden from gallery')
    );
  } catch {
    ElMessage.error(t('common.failed', 'Failed'));
  }
}

async function deleteTemplate(row: any) {
  try {
    await api.delete(`/templates/admin/${row.id}`);
    ElMessage.success(t('templates.deleteOk', 'Template deleted'));
    items.value = items.value.filter(i => i.id !== row.id);
  } catch {
    ElMessage.error(t('common.failed', 'Delete failed'));
  }
}

onMounted(() => loadData());
</script>

<style scoped>
/* ── Page wrapper ────────────────────────────────────────────── */
.admin-tmpl-page {
  padding: 0 0 40px;
}

/* ── Page Header ─────────────────────────────────────────────── */
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

.hero-action-btn {
  background: rgba(255, 255, 255, 0.15) !important;
  border: 1px solid rgba(255, 255, 255, 0.3) !important;
  color: #fff !important;
  backdrop-filter: blur(8px);
  transition: all 0.3s;
}
.hero-action-btn:hover {
  background: rgba(255, 255, 255, 0.25) !important;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
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
  margin: 0 0 4px;
  font-size: 1.5rem;
  font-weight: 800;
  color: #fff;
}

.page-sub {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(255,255,255,0.8);
}

/* ── Stats ───────────────────────────────────────────────────── */
.stats-strip {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.stat-card {
  flex: 1;
  min-width: 120px;
  background: var(--edms-card-bg);
  border: 1px solid rgba(156,163,175,0.12);
  border-radius: 12px;
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  box-shadow: var(--edms-shadow);
}

.stat-num {
  font-size: 2rem;
  font-weight: 800;
  color: var(--el-text-color-primary);
  line-height: 1;
}

.stat-label {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  text-align: center;
}

.stat-card.published .stat-num { color: var(--el-color-success); }
.stat-card.draft .stat-num { color: var(--el-color-warning); }

/* ── Table Card ──────────────────────────────────────────────── */
.table-card {
  background: var(--edms-card-bg);
  border: 1px solid rgba(156,163,175,0.12);
  border-radius: 16px;
  box-shadow: var(--edms-shadow);
  overflow: hidden;
}

.table-toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-bottom: 1px solid var(--el-border-color-lighter);
  flex-wrap: wrap;
}

.table-search {
  max-width: 280px;
}

.tmpl-table {
  width: 100%;
}

.title-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
}

.title-icon {
  color: var(--el-color-primary);
  font-size: 16px;
  flex-shrink: 0;
}

.desc-text {
  font-size: 12.5px;
  color: var(--el-text-color-secondary);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.date-text {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.status-tag {
  border-radius: 20px;
  letter-spacing: 0.02em;
}

.action-btns {
  display: flex;
  justify-content: center;
  gap: 6px;
  flex-wrap: wrap;
}

/* ── Dialog ──────────────────────────────────────────────────── */
.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
