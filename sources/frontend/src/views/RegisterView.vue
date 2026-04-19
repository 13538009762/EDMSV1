<template>
  <div class="register-wrap">
    <div class="top-bar">
      <LocaleSwitcher />
    </div>
    <div class="register-container">
      <el-card class="register-card">
        <template #header>
          <div class="header">
            <h3>{{ t('register.title', 'User Registration') }}</h3>
            <el-button link @click="router.push('/login')">{{ t('register.backToLogin', 'Back to Login') }}</el-button>
          </div>
        </template>
        
        <el-form :model="form" label-position="top" @submit.prevent="handleRegister">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item :label="t('register.firstName', 'First Name')" required>
                <el-input v-model="form.first_name" />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item :label="t('register.lastName', 'Last Name')" required>
                <el-input v-model="form.last_name" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item :label="t('register.loginName', 'Login Name')" required>
            <el-input v-model="form.login_name" />
          </el-form-item>

          <el-form-item :label="t('register.password', 'Password')" required>
            <el-input v-model="form.password" type="password" show-password />
          </el-form-item>

          <el-form-item :label="t('register.department', 'Department')" required>
            <el-select v-model="form.department_id" style="width: 100%">
              <el-option
                v-for="dept in departments"
                :key="dept.id"
                :label="dept.name"
                :value="dept.id"
              />
            </el-select>
          </el-form-item>

          <div class="actions">
            <el-button type="primary" native-type="submit" :loading="loading" style="width: 100%">
              {{ t('register.submit', 'Submit Request') }}
            </el-button>
          </div>
        </el-form>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { ElMessage, ElMessageBox } from 'element-plus';
import { useI18n } from 'vue-i18n';
import api from '@/api/client';
import LocaleSwitcher from '@/components/LocaleSwitcher.vue';

const { t } = useI18n();
const router = useRouter();
const loading = ref(false);
const departments = ref<any[]>([]);

const form = ref({
  login_name: '',
  password: '',
  first_name: '',
  last_name: '',
  department_id: null as number | null
});

onMounted(async () => {
  try {
    const { data } = await api.get('/users/departments');
    departments.value = data;
  } catch (err) {
    ElMessage.error('Failed to load departments');
  }
});

async function handleRegister() {
  if (!form.value.login_name || !form.value.password || !form.value.department_id) {
    ElMessage.warning(t('common.requiredFields', 'Please fill in all required fields'));
    return;
  }

  loading.value = true;
  try {
    await api.post('/auth/register', form.value);
    await ElMessageBox.alert(
      t('register.successInfo', 'Registration submitted successfully. Please wait for department and admin approval.'),
      t('common.success', 'Success'),
      { confirmButtonText: t('common.ok', 'OK') }
    );
    router.push('/login');
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('register.error', 'Registration failed'));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.register-wrap {
  min-height: 100vh;
  background: var(--el-fill-color-light);
  display: flex;
  flex-direction: column;
}
.top-bar {
  padding: 16px;
  display: flex;
  justify-content: flex-end;
}
.register-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.register-card {
  width: 100%;
  max-width: 500px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.header h3 {
  margin: 0;
}
.actions {
  margin-top: 24px;
}
</style>
