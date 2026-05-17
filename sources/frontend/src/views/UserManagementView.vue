<template>
  <div class="user-mgmt-page">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><User /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t('nav.users', 'Member Management') }}</h1>
          <p class="page-sub">{{ t("dashboard.subtitle", "Organize departments and manage employee access.") }}</p>
        </div>
      </div>
    </div>

    <el-card shadow="hover" class="mgmt-card">
      <div class="mgmt-toolbar">
        <div class="toolbar-left">
          <el-input
            v-model="searchQuery"
            :placeholder="t('nav.usersSearchPlaceholder')"
            clearable
            class="search-input"
            @input="handleSearch"
          >
            <template #prefix><el-icon><Search /></el-icon></template>
          </el-input>

          <el-select 
            v-slot:default
            v-if="auth.user?.is_super_admin"
            v-model="filterDept" 
            :placeholder="t('profile.dept', 'Department')" 
            clearable 
            class="filter-select"
            @change="loadUsers"
          >
            <el-option 
              v-for="d in deptOptions" 
              :key="d.id" 
              :label="formatDeptName(d.name, d.name_en)" 
              :value="d.id" 
            />
          </el-select>

          <el-select 
            v-model="filterRole" 
            :placeholder="t('library.colRole', 'Role')" 
            clearable 
            class="filter-select"
            @change="loadUsers"
          >
            <el-option :label="t('common.roles.admin', 'System Admin')" value="admin" />
            <el-option :label="t('common.roles.manager', 'Manager')" value="manager" />
            <el-option :label="t('common.roles.user', 'Staff')" value="staff" />
          </el-select>
        </div>

        <div class="header-actions">
          <el-button 
            v-slot:default
            v-if="auth.user?.is_super_admin || auth.user?.is_manager" 
            type="primary" 
            :icon="Plus" 
            @click="openAddUser"
          >
            {{ t('admin.addUser', 'Add Member') }}
          </el-button>
          <el-button 
            v-slot:default
            v-if="auth.user?.is_super_admin" 
            type="success" 
            :icon="Plus" 
            @click="deptDialogVisible = true"
          >
            {{ t('admin.addDept', 'Add Department') }}
          </el-button>
          <el-button 
            type="danger" 
            :icon="Delete" 
            :disabled="selectedIds.length === 0" 
            @click="handleBatchDelete"
          >
            {{ t('common.delete') }} ({{ selectedIds.length }})
          </el-button>
        </div>
      </div>
      <el-table 
        v-loading="loading" 
        :data="users" 
        stripe 
        style="width: 100%"
        @selection-change="handleSelectionChange"
      >
        <el-table-column type="selection" width="55" />
        <el-table-column prop="employee_no" :label="t('profile.employeeNo')" width="120" />
        <el-table-column prop="display_name" :label="t('common.name')" min-width="120" />
        <el-table-column prop="login_name" :label="t('profile.loginName')" width="120" />
        <el-table-column prop="department_name" :label="t('profile.dept')" min-width="150">
          <template #default="{ row }">
            {{ formatDeptName(row.department_name, row.department_name_en) }}
          </template>
        </el-table-column>
        <el-table-column :label="t('library.colRole', 'Role')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_super_admin" type="danger" size="small">{{ t('common.roles.admin', 'Super Admin') }}</el-tag>
            <el-tag v-else-if="row.is_manager" type="success" size="small">{{ t('common.roles.manager', 'Manager') }}</el-tag>
            <el-tag v-else type="info" size="small">{{ t('common.roles.user', 'Staff') }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column :label="t('common.actions')" width="240" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="editUser(row)">{{ t('common.edit') }}</el-button>
            <el-button type="warning" link @click="handleResetPassword(row)">{{ t('admin.resetPass') }}</el-button>
            <el-button v-if="auth.user?.is_super_admin || auth.user?.is_manager" type="danger" link @click="handleDeleteUser(row)">{{ t('common.delete') }}</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          :page-size="pageSize"
          size="small"
          background
          layout="prev, pager, next, total"
          :total="total"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- Add Department Dialog -->
    <el-dialog v-model="deptDialogVisible" :title="t('admin.addDept', 'Add New Department')" width="400px">
      <el-form label-width="100px">
        <el-form-item :label="t('common.name') + ' (ZH)'">
          <el-input v-model="newDeptName" placeholder="例如：研发部" />
        </el-form-item>
        <el-form-item :label="t('common.name') + ' (EN)'">
          <el-input v-model="newDeptNameEn" placeholder="e.g. R&D Department" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="deptLoading" @click="createDept">{{ t('common.ok') }}</el-button>
      </template>
    </el-dialog>

    <!-- Add User Dialog -->
    <el-dialog v-model="userDialogVisible" :title="isEdit ? t('profile.editUser') : t('admin.addUser')" width="600px" custom-class="spacious-dialog">
      <el-form :model="userForm" label-width="140px" style="padding: 10px 20px;">
        <el-form-item :label="t('profile.loginName')">
          <el-input v-model="userForm.login_name" />
        </el-form-item>
        <el-form-item :label="t('profile.password')">
          <el-input v-model="userForm.password" type="password" show-password />
        </el-form-item>
        <el-form-item :label="t('profile.employeeNo')">
          <el-input v-model="userForm.employee_no" />
        </el-form-item>
        <el-form-item :label="t('profile.firstName')">
          <el-input v-model="userForm.first_name" />
        </el-form-item>
        <el-form-item :label="t('profile.lastName')">
          <el-input v-model="userForm.last_name" />
        </el-form-item>
        <el-form-item v-if="auth.user?.is_super_admin" :label="t('profile.dept')">
          <el-select v-model="userForm.department_id" style="width: 100%">
            <el-option 
              v-for="d in deptOptions" 
              :key="d.id" 
              :label="formatDeptName(d.name, d.name_en)" 
              :value="d.id" 
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profile.mgr')">
          <el-switch v-model="userForm.is_manager" />
        </el-form-item>
        <el-form-item v-if="auth.user?.is_super_admin" :label="t('common.roles.admin', 'Super Admin')">
          <el-switch v-model="userForm.is_super_admin" :disabled="isEdit && editingUserId === auth.user?.id" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div style="padding: 10px 20px;">
          <el-button @click="userDialogVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="userLoading" @click="createUser">{{ t('common.ok') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { Plus, Delete, User, Search } from "@element-plus/icons-vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { useAuthStore } from "@/stores/auth";

const { t, locale, te } = useI18n();
const auth = useAuthStore();
const users = ref([]);

const formatDeptName = (name: string, nameEn?: string) => {
  if (!name) return "";
  // Try translating the primary name
  if (te(`dept.${name}`)) return t(`dept.${name}`);
  // Try translating the English name if available
  if (nameEn && te(`dept.${nameEn}`)) return t(`dept.${nameEn}`);
  // Fallback to raw values
  return locale.value === 'zh-CN' ? name : (nameEn || name);
};

async function handleResetPassword(user: any) {
  try {
    const { value: newPassword } = await ElMessageBox.prompt(
      t('admin.newPassHint'),
      t('admin.resetPassTitle'),
      {
        confirmButtonText: t('common.ok'),
        cancelButtonText: t('common.cancel'),
        inputType: 'password'
      }
    );
    
    if (newPassword) {
      await api.post(`/users/${user.id}/reset-password`, { password: newPassword });
      ElMessage.success(t('common.success'));
    }
  } catch (err) {
    // Cancelled
  }
}

const total = ref(0);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(15);
const searchQuery = ref("");
const filterDept = ref<number | null>(null);
const filterRole = ref<string | null>(null);
const selectedIds = ref<number[]>([]);

let searchTimer: any = null;
function handleSearch() {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    currentPage.value = 1;
    loadUsers();
  }, 400);
}

const isEdit = ref(false);
const editingUserId = ref<number | null>(null);
const deptDialogVisible = ref(false);
const deptLoading = ref(false);
const newDeptName = ref("");
const newDeptNameEn = ref("");

const userDialogVisible = ref(false);
const userLoading = ref(false);
const deptOptions = ref<any[]>([]);
const userForm = ref({
  login_name: "",
  password: "",
  employee_no: "",
  first_name: "",
  last_name: "",
  department_id: null as number | null,
  is_manager: false,
  is_super_admin: false
});

async function loadDepts() {
  const { data } = await api.get("/users/departments");
  deptOptions.value = data;
}

function openAddUser() {
  isEdit.value = false;
  editingUserId.value = null;
  userForm.value = {
    login_name: "",
    password: "",
    employee_no: "",
    first_name: "",
    last_name: "",
    department_id: auth.user?.is_super_admin ? null : (auth.user?.department_id ?? null),
    is_manager: false,
    is_super_admin: false
  };
  userDialogVisible.value = true;
}

function editUser(row: any) {
  isEdit.value = true;
  editingUserId.value = row.id;
  userForm.value = {
    login_name: row.login_name,
    password: "", // Leave blank to keep existing
    employee_no: row.employee_no,
    first_name: row.display_name.split(' ')[1] || row.display_name,
    last_name: row.display_name.split(' ')[0] || "",
    department_id: row.department_id,
    is_manager: row.is_manager || false,
    is_super_admin: row.is_super_admin || false
  };
  userDialogVisible.value = true;
}

async function handleDeleteUser(user: any) {
  try {
    await ElMessageBox.confirm(
      t('editor.deleteUserConfirm'),
      t('common.warning'),
      { type: 'warning', confirmButtonClass: 'el-button--danger' }
    );
    await api.delete(`/users/${user.id}`);
    ElMessage.success(t('common.success'));
    loadUsers();
  } catch {}
}

async function createUser() {
  const isDeptMissing = auth.user?.is_super_admin && !userForm.value.department_id;
  if (!userForm.value.login_name || (!isEdit.value && !userForm.value.password) || isDeptMissing) {
    return ElMessage.warning("Please fill required fields");
  }
  userLoading.value = true;
  try {
    if (isEdit.value && editingUserId.value) {
      await api.patch(`/users/${editingUserId.value}`, userForm.value);
    } else {
      await api.post("/users", userForm.value);
    }
    ElMessage.success(t('common.success'));
    userDialogVisible.value = false;
    loadUsers();
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('common.failed'));
  } finally {
    userLoading.value = false;
  }
}

async function loadUsers() {
  loading.value = true;
  try {
    let isManagerParam: number | null = null;
    let isSuperAdminParam: number | null = null;
    if (filterRole.value === 'admin') {
      isSuperAdminParam = 1;
    } else if (filterRole.value === 'manager') {
      isSuperAdminParam = 0;
      isManagerParam = 1;
    } else if (filterRole.value === 'staff') {
      isSuperAdminParam = 0;
      isManagerParam = 0;
    }

    const { data } = await api.get("/users", {
      params: { 
        page: currentPage.value, 
        size: pageSize.value,
        management: 1,
        search: searchQuery.value,
        department_id: filterDept.value,
        is_manager: isManagerParam,
        is_super_admin: isSuperAdminParam
      }
    });
    users.value = data.items;
    total.value = data.total;
  } finally {
    loading.value = false;
  }
}

function handleSelectionChange(items: any[]) {
  selectedIds.value = items.map(u => u.id);
}

async function handleBatchDelete() {
  try {
    await ElMessageBox.confirm(
      t('editor.deleteUserConfirm'),
      t('common.warning'),
      { type: 'warning' }
    );
    const { data } = await api.post("/users/batch-delete", { user_ids: selectedIds.value });
    ElMessage.success(data.message);
    loadUsers();
  } catch {}
}

async function createDept() {
  if (!newDeptName.value.trim()) return;
  deptLoading.value = true;
  try {
    await api.post("/users/departments", { 
      name: newDeptName.value.trim(),
      name_en: newDeptNameEn.value.trim() 
    });
    ElMessage.success(t('common.success'));
    deptDialogVisible.value = false;
    newDeptName.value = "";
    newDeptNameEn.value = "";
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('common.failed'));
  } finally {
    deptLoading.value = false;
  }
}

onMounted(() => {
  loadUsers();
  loadDepts();
});
</script>

<style scoped>
.user-mgmt-page {
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
/* 🚀 白色区域（卡片）样式优化 */
.mgmt-card {
  border-radius: 16px;
  padding: 8px; /* 扩大内部感官空间 */
}
/* 🚀 内部工具栏：将按钮移至右上方 */
.mgmt-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: 240px;
}

.filter-select {
  width: 180px;
}

.filter-select.mini {
  width: 120px;
}
.pagination {
  margin-top: 24px;
  display: flex;
  justify-content: flex-end;
}
</style>
