<template>
  <div class="profile-page">
    <el-card shadow="hover" class="profile-card">
      <template #header>
        <div class="card-header">
          <span>{{ t('profile.title') }}</span>
        </div>
      </template>

      <el-form :model="form" label-width="120px" v-loading="loading">
        <el-form-item :label="t('profile.employeeNo')">
          <el-input v-model="form.employee_no" disabled />
        </el-form-item>
        <el-form-item :label="t('profile.loginName')">
          <el-input v-model="form.login_name" disabled />
        </el-form-item>
        <el-form-item :label="t('profile.firstName')">
          <el-input v-model="form.first_name" />
        </el-form-item>
        <el-form-item :label="t('profile.lastName')">
          <el-input v-model="form.last_name" />
        </el-form-item>
        <el-form-item :label="t('profile.gender')">
          <el-select v-model="form.gender" style="width: 100%;">
            <el-option label="Male" value="Male" />
            <el-option label="Female" value="Female" />
            <el-option label="Other" value="Other" />
          </el-select>
        </el-form-item>
        <el-form-item :label="t('profile.birthDate')">
          <el-date-picker
            v-model="form.birth_date"
            type="date"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%;"
          />
        </el-form-item>
        <el-form-item :label="t('profile.dept')">
          <el-tag type="info">{{ form.department_name || 'N/A' }}</el-tag>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSave">{{ t('common.save') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage } from "element-plus";

const { t } = useI18n();
const loading = ref(false);
const form = ref({
  id: 0,
  employee_no: "",
  login_name: "",
  first_name: "",
  last_name: "",
  gender: "",
  birth_date: "",
  department_name: ""
});

async function loadProfile() {
  loading.value = true;
  try {
    const { data } = await api.get("/users/me");
    form.value = data;
  } catch (err) {
    ElMessage.error(t('common.failed'));
  } finally {
    loading.value = false;
  }
}

async function handleSave() {
  loading.value = true;
  try {
    await api.patch(`/users/${form.value.id}`, {
      first_name: form.value.first_name,
      last_name: form.value.last_name,
      gender: form.value.gender,
      birth_date: form.value.birth_date
    });
    ElMessage.success(t('profile.saveSuccess'));
    await loadProfile();
  } catch (err) {
    ElMessage.error(t('common.failed'));
  } finally {
    loading.value = false;
  }
}

onMounted(loadProfile);
</script>

<style scoped>
.profile-page {
  padding: 24px;
  display: flex;
  justify-content: center;
}
.profile-card {
  width: 100%;
  max-width: 600px;
}
.card-header {
  font-weight: bold;
}
</style>
