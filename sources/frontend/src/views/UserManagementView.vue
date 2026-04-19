<template>
  <div class="user-mgmt-page">
    <div class="header">
      <h2>{{ t('nav.masterData', 'Member Management') }}</h2>
      <div class="actions">
        <el-button type="success" :icon="Plus" @click="deptDialogVisible = true">{{ t('admin.addDept', 'Add Department') }}</el-button>
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
            {{ t('dept.' + row.department_name, row.department_name) }}
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
          background
          layout="prev, pager, next, total"
          :total="total"
          @current-change="loadUsers"
        />
      </div>
    </el-card>

    <!-- Add Department Dialog -->
    <el-dialog v-model="deptDialogVisible" :title="t('admin.addDept', 'Add New Department')" width="400px">
      <el-form label-width="80px">
        <el-form-item :label="t('common.name')">
          <el-input v-model="newDeptName" placeholder="e.g. Finance" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="deptDialogVisible = false">{{ t('common.cancel') }}</el-button>
        <el-button type="primary" :loading="deptLoading" @click="createDept">{{ t('common.ok') }}</el-button>
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

const { t } = useI18n();
const users = ref([]);
const total = ref(0);
const loading = ref(false);
const currentPage = ref(1);
const pageSize = ref(15);
const selectedIds = ref<number[]>([]);

const deptDialogVisible = ref(false);
const deptLoading = ref(false);
const newDeptName = ref("");

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
      t('editor.deleteConfirm'),
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
    await api.post("/users/departments", { name: newDeptName.value.trim() });
    ElMessage.success(t('common.success'));
    deptDialogVisible.value = false;
    newDeptName.value = "";
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('common.failed'));
  } finally {
    deptLoading.value = false;
  }
}

onMounted(loadUsers);
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
