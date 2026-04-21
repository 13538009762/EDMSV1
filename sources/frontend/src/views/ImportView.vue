<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t("import.title") }}</h2>
      <p class="subtitle">{{ t("import.hint") }}</p>
    </div>

    <el-tabs type="border-card" class="master-tabs">
      <!-- Tab 1: XLSX Import (Only for System Admin) -->
      <el-tab-pane v-if="isSystemAdmin" :label="t('import.title')">
        <div class="upload-section">
          <div class="template-download">
            <el-button :icon="Download" @click="downloadTemplate" plain>
              {{ t('import.downloadTemplate') }}
            </el-button>
          </div>

          <div class="type-selector">
            <el-radio-group v-model="importType">
              <el-radio-button label="all">{{ t('import.typeAll') }}</el-radio-button>
              <el-radio-button label="departments">{{ t('import.typeDepts') }}</el-radio-button>
              <el-radio-button label="positions">{{ t('import.typePos') }}</el-radio-button>
              <el-radio-button label="employees">{{ t('import.typeUsers') }}</el-radio-button>
            </el-radio-group>
          </div>

          <el-upload
            class="upload-area"
            drag
            :auto-upload="false"
            :on-change="onFile"
            :limit="1"
            accept=".xlsx,.xlsm"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              {{ t("import.dragText") }} <em>{{ t("import.clickToUpload") }}</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                <el-icon><InfoFilled /></el-icon>
                {{ t("import.fileTip") }}
              </div>
            </template>
          </el-upload>

          <div class="mode-selector">
            <el-switch
              v-model="overwrite"
              :active-text="t('import.overwrite')"
              active-color="#ff4949"
            />
            <div class="mode-hint">
              <el-icon><Warning /></el-icon>
              {{ overwrite ? t('import.warning') : t('import.overwriteWarn') }}
            </div>
          </div>

          <div class="action-bar">
            <el-button
              type="primary"
              size="large"
              :icon="Upload"
              :loading="loading"
              :disabled="!file"
              @click="upload"
              class="submit-btn"
            >
              {{ t("import.upload") }}
            </el-button>
          </div>
        </div>

        <transition name="el-fade-in">
          <div v-if="result" class="result-section">
            <el-divider>{{ t("import.resultTitle", "导入结果") }}</el-divider>
            <el-alert v-if="!isError" :title="t('import.successTitle', '导入任务已执行完毕')" type="success" show-icon :closable="false" class="result-alert" />
            <el-alert v-else :title="t('import.errorTitle', '导入任务执行失败')" type="error" show-icon :closable="false" class="result-alert" />
            <div class="json-viewer"><pre>{{ JSON.stringify(result, null, 2) }}</pre></div>
          </div>
        </transition>
      </el-tab-pane>

      <!-- Tab 2: User Management -->
      <el-tab-pane :label="t('profile.editUser')">
        <div class="user-mgmt">
          <div class="mgmt-header">
            <el-input
              v-model="searchQuery"
              :placeholder="t('common.search', 'Search users...')"
              clearable
              style="width: 300px; margin-right: 12px;"
              @keyup.enter="loadUsers"
            />
            <el-button type="primary" :icon="Search" @click="loadUsers">{{ t('common.search') }}</el-button>
            <el-divider direction="vertical" />
            <el-button type="success" :icon="Plus" @click="openAddUser">{{ t('profile.addUser', 'Add User') }}</el-button>
          </div>

          <el-table :data="users" v-loading="userLoading" style="width: 100%">
            <el-table-column prop="employee_no" :label="t('profile.employeeNo')" width="120" />
            <el-table-column prop="login_name" :label="t('profile.loginName')" width="120" />
            <el-table-column prop="display_name" :label="t('common.name', 'Name')" />
            <el-table-column prop="department_name" :label="t('profile.dept')" />
            <el-table-column :label="t('common.actions')" width="180" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" link @click="editUser(row)">{{ t('common.edit') }}</el-button>
                <el-button v-if="isSystemAdmin || authStore.user?.is_manager" type="danger" link @click="handleDeleteUser(row)">{{ t('common.delete', 'Delete') }}</el-button>
              </template>
            </el-table-column>
          </el-table>

          <div class="pagination">
            <el-pagination
              size="small"
              layout="prev, pager, next"
              v-model:current-page="currentPage"
              :total="totalUsers"
              @current-change="loadUsers"
            />
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Create User Dialog -->
    <el-dialog :title="t('profile.addUser', 'Add User')" v-model="addDialogVisible" width="600px">
      <el-form :model="addForm" label-width="120px" v-loading="addLoading">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="t('profile.firstName')" required>
              <el-input v-model="addForm.first_name" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="t('profile.lastName')" required>
              <el-input v-model="addForm.last_name" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item :label="t('profile.loginName')" required>
          <el-input v-model="addForm.login_name" />
        </el-form-item>
        <el-form-item :label="t('profile.employeeNo')" required>
          <el-input v-model="addForm.employee_no" />
        </el-form-item>
        <el-form-item :label="t('login.password')" required>
          <el-input v-model="addForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('profile.dept')" required>
          <el-select v-model="addForm.department_id" :disabled="!isSystemAdmin" style="width: 100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profile.mgr')">
          <el-switch v-model="addForm.is_manager" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="addDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="createUser">{{ t('common.submit') }}</el-button>
      </template>
    </el-dialog>

    <!-- Admin User Edit Dialog -->
    <el-dialog :title="t('profile.editUser')" v-model="editDialogVisible" width="500px">
      <el-form :model="editForm" label-width="100px" v-loading="dialogLoading">
        <el-form-item :label="t('profile.dept')">
          <el-select v-model="editForm.department_id" :disabled="!isSystemAdmin" style="width: 100%">
            <el-option v-for="d in departments" :key="d.id" :label="d.name" :value="d.id" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profile.mgr')">
          <el-switch v-model="editForm.is_manager" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" @click="saveUser">{{ t('common.save') }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import type { UploadFile } from "element-plus";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage, ElMessageBox } from "element-plus";
import { Upload, UploadFilled, InfoFilled, Search, Plus, Warning, Download } from "@element-plus/icons-vue"; // 引入图标
import { useAuthStore } from "@/stores/auth";

const { t } = useI18n();
const authStore = useAuthStore();
const isSystemAdmin = computed(() => authStore.user?.login_name === 'admin');
const file = ref<File | null>(null);
const loading = ref(false);
const result = ref<unknown>(null);
const isError = ref(false); // 跟踪是否为报错信息
const overwrite = ref(true); // 默认覆盖
const importType = ref("all");

function onFile(f: UploadFile) {
  file.value = f.raw || null;
  // 当用户重新选择文件时，清空上次的结果
  result.value = null;
  isError.value = false;
}

async function upload() {
  if (!file.value) return;
  
  try {
    await ElMessageBox.confirm(t('import.warning'), t('import.confirmTitle'), {
      confirmButtonText: t('import.confirmImport'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    });
  } catch { return; }
  
  loading.value = true;
  result.value = null;
  isError.value = false;
  
  const fd = new FormData();
  fd.append("file", file.value);
  fd.append("overwrite", String(overwrite.value));
  fd.append("table_type", importType.value);
  try {
    const { data } = await api.post("/admin/master-data/import", fd);
    result.value = data;
    ElMessage.success(t("import.success"));
  } catch (e: unknown) {
    ElMessage.error(t("import.failed"));
    result.value = e;
    isError.value = true;
  } finally {
    loading.value = false;
  }
}

function downloadTemplate() {
  window.open(api.defaults.baseURL + "/admin/master-data/template", "_blank");
}

// --- User Management Logic ---
const searchQuery = ref("");
const users = ref<any[]>([]);
const totalUsers = ref(0);
const currentPage = ref(1);
const userLoading = ref(false);
const editDialogVisible = ref(false);
const dialogLoading = ref(false);
const editForm = ref({ id: 0, department_id: null as number | null, is_manager: false });

const addDialogVisible = ref(false);
const addLoading = ref(false);
const addForm = ref({
  login_name: "",
  password: "",
  employee_no: "",
  first_name: "",
  last_name: "",
  department_id: null as number | null,
  is_manager: false
});
const departments = ref<any[]>([]);

async function loadUsers() {
  userLoading.value = true;
  try {
    const { data } = await api.get("/users", { params: { search: searchQuery.value, page: currentPage.value } });
    users.value = data.items;
    totalUsers.value = data.total;
  } catch(e) {} finally { userLoading.value = false; }
}

async function loadDepts() {
  const { data } = await api.get("/users/departments");
  departments.value = data;
}

function editUser(user: any) {
  editForm.value = { id: user.id, department_id: user.department_id, is_manager: user.is_manager };
  editDialogVisible.value = true;
  loadDepts();
}

async function saveUser() {
  dialogLoading.value = true;
  try {
    await api.patch(`/users/${editForm.value.id}`, {
      department_id: editForm.value.department_id,
      is_manager: editForm.value.is_manager
    });
    ElMessage.success(t('common.saveOk'));
    editDialogVisible.value = false;
    loadUsers();
  } catch(e) {
    ElMessage.error(t('common.failed'));
  } finally { dialogLoading.value = false; }
}

function openAddUser() {
  addForm.value = {
    login_name: "",
    password: "",
    employee_no: "",
    first_name: "",
    last_name: "",
    department_id: isSystemAdmin.value ? null : (authStore.user?.department_id ?? null),
    is_manager: false
  };
  addDialogVisible.value = true;
  loadDepts();
}

async function createUser() {
  if (!addForm.value.login_name || !addForm.value.password || !addForm.value.department_id) {
    ElMessage.warning(t('common.requiredFields', 'Fill in required fields'));
    return;
  }
  addLoading.value = true;
  try {
    await api.post("/users", addForm.value);
    ElMessage.success(t('common.saveOk'));
    addDialogVisible.value = false;
    loadUsers();
  } catch(e: any) {
    ElMessage.error(e.response?.data?.error || t('common.failed'));
  } finally { addLoading.value = false; }
}

async function handleDeleteUser(user: any) {
  if (!isSystemAdmin.value && !authStore.user?.is_manager) {
      ElMessage.error(t('common.noPermission', 'No permission'));
      return;
  }
  try {
    await ElMessageBox.confirm(
      t('editor.deleteUserConfirm', 'Are you sure you want to delete this user? This cannot be undone.'),
      t('common.warning', 'Warning'),
      { type: 'warning', confirmButtonClass: 'el-button--danger' }
    );
    await api.delete(`/users/${user.id}`);
    ElMessage.success(t('common.saveOk'));
    loadUsers();
  } catch (e: any) {
    if (e !== 'cancel') {
      ElMessage.error(e.response?.data?.error || t('common.failed'));
    }
  }
}

onMounted(loadUsers);
</script>

<style scoped>
.page-container {
  padding: 24px 32px;
  max-width: 1200px;
  margin: 0 auto;
}
.master-tabs {
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}
.mgmt-header {
  display: flex;
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: center;
}
.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}
/* Existing styles... */
.upload-area { width: 100%; max-width: 600px; }
.el-upload__tip { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 12px; color: var(--el-text-color-secondary); font-size: 13px; }
.action-bar { margin-top: 32px; width: 100%; display: flex; justify-content: center; }
.template-download { margin-bottom: 24px; }
.type-selector { margin-bottom: 16px; }
.submit-btn { width: 200px; border-radius: 6px; font-weight: 600; letter-spacing: 1px; }
.result-section { margin-top: 24px; }
.mode-selector { margin-top: 24px; display: flex; flex-direction: column; align-items: center; border: 1px solid var(--el-border-color-lighter); padding: 16px; border-radius: 8px; background: var(--el-fill-color-blank); }
.mode-hint { margin-top: 12px; font-size: 13px; color: var(--el-text-color-secondary); display: flex; align-items: center; gap: 6px; text-align: center; max-width: 400px; }
.mode-hint .el-icon { color: var(--el-color-warning); font-size: 16px; }
.result-alert { margin-bottom: 16px; border-radius: 6px; }
.json-viewer { background: var(--el-bg-color-page); border: 1px solid var(--el-border-color-lighter); border-radius: 6px; padding: 16px; overflow-x: auto; }
.json-viewer pre { margin: 0; font-family: 'Consolas', 'Courier New', Courier, monospace; font-size: 13px; color: var(--el-text-color-primary); line-height: 1.6; }
</style>