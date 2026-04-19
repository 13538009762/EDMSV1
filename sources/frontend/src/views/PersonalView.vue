<template>
  <div class="personal">
    <el-card class="card">
      <template #header>
        <span>{{ t("personal.title") }}</span>
      </template>
      <div class="profile">
        <div class="avatar">
          <el-avatar :size="100" :src="avatarUrl">{{ userInitials }}</el-avatar>
        </div>
        <div class="info">
          <h2>{{ user?.last_name }} {{ user?.first_name }}</h2>
          <div class="detail">{{ t("personal.department") }}: {{ t('dept.' + user?.department_name, user?.department_name) }}</div>
          <div class="detail">{{ t("personal.position") }}: {{ t('pos.' + (user?.position_full_name || user?.position_short), user?.position_full_name || user?.position_short) }}</div>
          <div class="detail">{{ t("personal.login") }}: {{ user?.login_name }}</div>
          <div class="detail">{{ t("personal.employeeNo") }}: {{ user?.employee_no }}</div>
          <div class="detail" v-if="user?.gender">{{ t("personal.gender") }}: {{ user.gender === 'Male' ? t("personal.male") : t("personal.female") }}</div>
          <div class="detail" v-if="user?.birth_date">{{ t("personal.birthDate") }}: {{ user.birth_date }} ({{ t("personal.age") }}: {{ user.age }})</div>
          <div style="margin-top: 16px;">
            <el-button type="primary" :icon="Edit" @click="editVisible = true">{{ t('common.edit') }}</el-button>
          </div>
        </div>
      </div>

      <!-- Edit Dialog -->
      <el-dialog :title="t('profile.title')" v-model="editVisible" width="500px">
        <el-form :model="editForm" label-width="100px" v-loading="editLoading">
          <el-form-item :label="t('profile.firstName')">
            <el-input v-model="editForm.first_name" />
          </el-form-item>
          <el-form-item :label="t('profile.lastName')">
            <el-input v-model="editForm.last_name" />
          </el-form-item>
          <el-form-item :label="t('profile.gender')">
            <el-select v-model="editForm.gender" style="width: 100%">
              <el-option label="Male" value="Male" />
              <el-option label="Female" value="Female" />
              <el-option label="Other" value="Other" />
            </el-select>
          </el-form-item>
          <el-form-item :label="t('profile.birthDate')">
            <el-date-picker v-model="editForm.birth_date" type="date" value-format="YYYY-MM-DD" style="width: 100%" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="editVisible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" @click="saveProfile">{{ t('common.save') }}</el-button>
        </template>
      </el-dialog>
      <div class="stats">
        <h3>{{ t("personal.stats") }}</h3>
        <div class="stats-grid">
          <el-card class="stat-card">
            <template #header>
              <span>{{ t("personal.createdDocs") }}</span>
            </template>
            <div class="stat-value">{{ stats?.created_docs || 0 }}</div>
          </el-card>
          <el-card class="stat-card">
            <template #header>
              <span>{{ t("personal.collaboratedDocs") }}</span>
            </template>
            <div class="stat-value">{{ stats?.collaborated_docs || 0 }}</div>
          </el-card>
          <el-card class="stat-card">
            <template #header>
              <span>{{ t("personal.approvedDocs") }}</span>
            </template>
            <div class="stat-value">{{ stats?.approved_docs || 0 }}</div>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { Edit } from "@element-plus/icons-vue";
import { ElMessage } from "element-plus";

interface UserInfo {
  id: number;
  last_name: string;
  first_name: string;
  login_name: string;
  employee_no: string;
  department_name: string;
  position_short: string;
  position_full_name?: string;
  birth_date?: string;
  gender?: string;
  age?: number;
  is_manager?: boolean;
}

interface Stats {
  created_docs: number;
  collaborated_docs: number;
  approved_docs: number;
}

const { t } = useI18n();
const user = ref<UserInfo | null>(null);
const stats = ref<Stats | null>(null);

const avatarUrl = computed(() => {
  // 使用默认头像
  return "https://via.placeholder.com/100";
});

const userInitials = computed(() => {
  if (!user.value) return "";
  const first = user.value.first_name?.charAt(0) || "";
  const last = user.value.last_name?.charAt(0) || "";
  return (first + last).toUpperCase();
});

const editVisible = ref(false);
const editLoading = ref(false);
const editForm = ref({ first_name: '', last_name: '', gender: '', birth_date: '' });

async function loadUserInfo() {
  try {
    const { data } = await api.get("/users/me");
    user.value = data;
    editForm.value = { ...data };
  } catch (error) {}
}

async function saveProfile() {
  editLoading.value = true;
  try {
    await api.patch(`/users/${user.value.id}`, editForm.value);
    ElMessage.success(t('profile.saveSuccess'));
    editVisible.value = false;
    await loadUserInfo();
  } catch (e) {
    ElMessage.error(t('common.failed'));
  } finally {
    editLoading.value = false;
  }
}

async function loadStats() {
  try {
    const { data } = await api.get("/users/me/stats");
    stats.value = data;
  } catch (error) {}
}

onMounted(async () => {
  await loadUserInfo();
  await loadStats();
});
</script>

<style scoped>
.personal {
  min-height: 100%;
  padding: 24px;
  background: var(--el-fill-color-light);
  box-sizing: border-box;
}

.top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}

.card {
  max-width: 800px;
  margin: 0 auto;
}

.profile {
  display: flex;
  align-items: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--el-border-color);
}

.avatar {
  margin-right: 32px;
}

.info h2 {
  margin: 0 0 16px 0;
  font-size: 24px;
  font-weight: 600;
}

.detail {
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--el-text-color-regular);
}

.stats h3 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: var(--el-color-primary);
  margin-top: 8px;
}
</style>