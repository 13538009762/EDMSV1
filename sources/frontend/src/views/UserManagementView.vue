<template>
  <div class="user-mgmt-page">
    <div class="header">
      <h2>{{ t('nav.users', 'Member Management') }}</h2>
      <div class="actions">
        <el-button 
          v-if="auth.user?.login_name === 'admin' || auth.user?.is_manager" 
          type="primary" 
          :icon="Plus" 
          @click="openAddUser"
        >
          {{ t('admin.addUser', 'Add Member') }}
        </el-button>
        <el-button 
          v-if="auth.user?.login_name === 'admin'" 
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

    <el-card shadow="hover">
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
        <el-table-column prop="is_manager" :label="t('profile.mgr')" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_manager" type="success" size="small">{{ t('common.yes') }}</el-tag>
            <el-tag v-else type="info" size="small">{{ t('common.no') }}</el-tag>
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
    <el-dialog v-model="userDialogVisible" :title="t('admin.addUser', 'Add New Member')" width="600px" custom-class="spacious-dialog">
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
        <el-form-item :label="t('profile.dept')">
          <el-select v-model="userForm.department_id" :disabled="auth.user?.login_name !== 'admin'" style="width: 100%">
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
import { Plus, Delete } from "@element-plus/icons-vue";
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
const total = ref(0);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(15);
const selectedIds = ref<number[]>([]);

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
  is_manager: false
});

async function loadDepts() {
  const { data } = await api.get("/users/departments");
  deptOptions.value = data;
}

function openAddUser() {
  userForm.value = {
    login_name: "",
    password: "",
    employee_no: "",
    first_name: "",
    last_name: "",
    department_id: auth.user?.login_name === 'admin' ? null : (auth.user?.department_id ?? null),
    is_manager: false
  };
  userDialogVisible.value = true;
}

async function createUser() {
  if (!userForm.value.login_name || !userForm.value.password || !userForm.value.department_id) {
    return ElMessage.warning("Please fill required fields");
  }
  userLoading.value = true;
  try {
    await api.post("/users", userForm.value);
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
    const { data } = await api.get("/users", {
      params: { page: currentPage.value, size: pageSize.value }
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
  padding: 24px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.header h2 {
  margin: 0;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
</style>
