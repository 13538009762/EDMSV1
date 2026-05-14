<template>
  <div class="login-container">
    <!-- Top Navigation -->
    <div class="top-nav">
      <div class="logo-section">
        <img src="/favicon.png" class="app-logo" alt="EDMS Logo" />
        <div class="logo-text">
          <span class="brand">EDMS</span>
          <span class="divider">|</span>
          <span class="app-name">{{ t('common.appName') }}</span>
        </div>
      </div>
      <div class="nav-right">
        <LocaleSwitcher purple />
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-content">
      <!-- Left Hero Area -->
      <div class="hero-area">
        <div class="hero-content">
          <h1 class="hero-title">
            {{ t('login.heroPart1') }} · {{ t('login.heroPart2') }} · <span class="text-gradient">{{ t('login.heroPart3') }}</span>
          </h1>
          <p class="hero-subtitle">{{ t('login.heroSubtitle') }}</p>

          <div class="feature-list">
            <div class="feature-item" v-for="(f, i) in features" :key="i">
              <div class="feature-icon" :style="{ background: f.bg }">
                <el-icon><component :is="f.icon" /></el-icon>
              </div>
              <div class="feature-info">
                <h3>{{ f.title }}</h3>
                <p>{{ f.desc }}</p>
              </div>
            </div>
          </div>

          <!-- Bottom Left Floating Card -->
          <div class="system-intro-card">
            <h3>{{ t('login.introTitle', '企业级核心知识库') }}</h3>
            <p>{{ t('login.introText', '本系统致力于为企业提供一站式、智能化的文档全生命周期管理方案。依托底层 AI 大模型与区块链存证技术，我们不仅确保了企业核心知识资产的绝对安全，更通过高效的协作工具助力组织实现知识价值的持续增长。') }}</p>
          </div>
        </div>
      </div>

      <!-- Right Login Panel -->
      <div class="login-panel">
        <div class="login-glass-card">
          <transition name="form-fade" mode="out-in">
            <!-- Login Form Section -->
            <div v-if="mode === 'login'" key="login">
              <div class="card-header">
                <h2>{{ t('login.title') }}</h2>
                <p>{{ t('login.subtitle') }}</p>
              </div>

              <div class="login-tabs">
                <div class="tab-item active">{{ t('login.loginTab') }}</div>
              </div>

              <el-form class="login-form" @submit.prevent="submit">
                <el-form-item>
                  <el-input 
                    v-model="loginName" 
                    :placeholder="t('login.usernamePlaceholder')" 
                    :prefix-icon="User"
                    size="large"
                  />
                </el-form-item>

                <el-form-item>
                  <el-input 
                    v-model="password" 
                    type="password" 
                    :placeholder="t('login.passwordPlaceholder')" 
                    :prefix-icon="Lock"
                    size="large"
                    show-password
                  />
                </el-form-item>

                <div class="form-utils">
                  <el-checkbox v-model="rememberMe">{{ t('login.rememberMe') }}</el-checkbox>
                  <el-link class="purple-link" :underline="false">{{ t('login.forgotPassword') }}</el-link>
                </div>

                <el-button type="primary" class="login-btn" :loading="loading" native-type="submit">
                  {{ t('login.submit') }}
                </el-button>

                <div class="register-footer">
                  <span>{{ t('login.noAccount') }}</span>
                  <el-link class="purple-link" @click="mode = 'register'">
                    {{ t('login.register') }}
                  </el-link>
                </div>
              </el-form>
            </div>

            <!-- Registration Form Section -->
            <div v-else key="register" class="register-section">
              <div class="card-header">
                <h2>{{ t('register.title') }}</h2>
                <p>{{ t('register.submitInfo') }}</p>
              </div>

              <el-form :model="regForm" label-position="top" @submit.prevent="handleRegister">
                <el-row :gutter="12">
                  <el-col :span="12">
                    <el-form-item :label="t('register.lastName')" required>
                      <el-input v-model="regForm.last_name" :prefix-icon="Edit" />
                    </el-form-item>
                  </el-col>
                  <el-col :span="12">
                    <el-form-item :label="t('register.firstName')" required>
                      <el-input v-model="regForm.first_name" :prefix-icon="Edit" />
                    </el-form-item>
                  </el-col>
                </el-row>

                <el-form-item :label="t('register.loginName')" required>
                  <el-input v-model="regForm.login_name" :prefix-icon="User" />
                </el-form-item>

                <el-form-item :label="t('register.password')" required>
                  <el-input v-model="regForm.password" type="password" show-password :prefix-icon="Lock" />
                </el-form-item>

                <el-form-item :label="t('register.department')" required>
                  <el-select v-model="regForm.department_id" style="width: 100%" :placeholder="t('register.placeholder')">
                    <el-option
                      v-for="dept in departments"
                      :key="dept.id"
                      :label="formatDeptName(dept.name, dept.name_en)"
                      :value="dept.id"
                    />
                  </el-select>
                </el-form-item>

                <el-button type="primary" class="login-btn" :loading="loading" native-type="submit">
                  {{ t('register.submit') }}
                </el-button>

                <div class="register-footer">
                  <el-link type="info" @click="mode = 'login'">
                    {{ t('register.backToLogin') }}
                  </el-link>
                </div>
              </el-form>
            </div>
          </transition>
        </div>
      </div>
    </div>

    <!-- Security Icons Right Bottom -->
    <div class="security-footer">
      <div class="security-badges">
        <div class="badge-item">
          <el-icon><Lock /></el-icon> {{ t('login.encryption') }}
        </div>
        <div class="badge-item">
          <el-icon><Finished /></el-icon> {{ t('login.accessControl') }}
        </div>
        <div class="badge-item">
          <el-icon><Bell /></el-icon> {{ t('login.auditTrail') }}
        </div>
      </div>
      <div class="copyright">
        &copy; 2026 EDMS. All rights reserved.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { useI18n } from "vue-i18n";
import { useAuthStore } from "@/stores/auth";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import api from "@/api/client";
import { 
  User, Lock, Cpu, Finished, Connection, Monitor, 
  Bell, Edit
} from "@element-plus/icons-vue";

const { t, locale, te } = useI18n();
const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const formatDeptName = (name: string, nameEn?: string) => {
  if (!name) return "";
  if (te(`dept.${name}`)) return t(`dept.${name}`);
  if (nameEn && te(`dept.${nameEn}`)) return t(`dept.${nameEn}`);
  return locale.value === 'zh-CN' ? name : (nameEn || name);
};

const loginName = ref("");
const password = ref("");
const rememberMe = ref(false);
const loading = ref(false);

const mode = ref('login');

const departments = ref<any[]>([]);
const regForm = ref({
  login_name: '',
  password: '',
  first_name: '',
  last_name: '',
  department_id: null as number | null
});

const features = computed(() => [
  {
    icon: Cpu,
    title: t("login.featureAiTitle"),
    desc: t("login.featureAiDesc"),
    bg: "rgba(167, 139, 250, 0.15)"
  },
  {
    icon: Finished,
    title: t("login.featureSecurityTitle"),
    desc: t("login.featureSecurityDesc"),
    bg: "rgba(139, 92, 246, 0.15)"
  },
  {
    icon: Connection,
    title: t("login.featureCollabTitle"),
    desc: t("login.featureCollabDesc"),
    bg: "rgba(124, 58, 237, 0.15)"
  },
  {
    icon: Monitor,
    title: t("login.featureSupportTitle"),
    desc: t("login.featureSupportDesc"),
    bg: "rgba(109, 40, 217, 0.15)"
  }
]);

onMounted(async () => {
  try {
    const { data } = await api.get('/users/departments');
    departments.value = data;
  } catch (err) {}
});

async function submit() {
  if (!loginName.value || !password.value) {
    ElMessage.warning(t("common.requiredFields"));
    return;
  }
  loading.value = true;
  try {
    await auth.login(loginName.value.trim(), password.value);
    const r = (route.query.redirect as string) || "/";
    router.replace(r);
  } catch (err) {
    ElMessage.error(t("login.invalid"));
  } finally {
    loading.value = false;
  }
}

async function handleRegister() {
  if (!regForm.value.login_name || !regForm.value.password || !regForm.value.department_id) {
    ElMessage.warning(t('common.requiredFields'));
    return;
  }
  loading.value = true;
  try {
    await api.post('/auth/register', regForm.value);
    await ElMessageBox.alert(
      t('register.successInfo'),
      t('common.success'),
      { 
        confirmButtonText: t('common.ok'),
        confirmButtonClass: 'purple-confirm-button'
      }
    );
    mode.value = 'login';
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('register.error'));
  } finally {
    loading.value = false;
  }
}
</script>

<style scoped>
.login-container {
  /* 🌟 Local Theme Override: Purple */
  --el-color-primary: #8b5cf6;
  --el-color-primary-light-3: #a78bfa;
  --el-color-primary-light-5: #c4b5fd;
  --el-color-primary-light-7: #ddd6fe;
  --el-color-primary-light-8: #ede9fe;
  --el-color-primary-light-9: #f5f3ff;
  --el-color-primary-dark-2: #7c3aed;

  width: 100vw;
  min-height: 100vh;
  background: #f8fafc url('/images/v1.png') no-repeat center center;
  background-size: cover;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
  color: #1e293b;
  position: relative;
}

/* Top Nav */
.top-nav {
  padding: 32px 64px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  z-index: 10;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.app-logo {
  width: 40px;
  height: 40px;
}

.brand {
  font-size: 26px;
  font-weight: 900;
  color: #8b5cf6;
  letter-spacing: -1px;
}

.divider {
  color: #cbd5e1;
  margin: 0 12px;
  font-weight: 300;
}

.app-name {
  font-size: 15px;
  color: #64748b;
  font-weight: 600;
}

/* Main Content */
.main-content {
  flex: 1;
  display: flex;
  padding: 0 80px;
  align-items: center;
  justify-content: space-between;
  max-width: 1600px;
  margin: 0 auto;
  width: 100%;
}

/* Left Area */
.hero-area {
  flex: 1;
  max-width: 600px;
  position: relative;
  transition: all 0.5s ease;
}

/* Add a subtle glow behind the text to separate it from the busy background */
.hero-area::before {
  content: "";
  position: absolute;
  top: -50px;
  left: -80px;
  right: -40px;
  bottom: -50px;
  /* Frosted glass effect specifically for the text area */
  background: linear-gradient(
    to right, 
    rgba(255, 255, 255, 0.8) 0%, 
    rgba(255, 255, 255, 0.5) 50%, 
    rgba(255, 255, 255, 0) 100%
  );
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  z-index: -1;
  pointer-events: none;
  border-radius: 40px;
}

.hero-title {
  font-size: clamp(32px, 4vw, 52px);
  font-weight: 850;
  color: #0f172a;
  margin-bottom: 24px;
  line-height: 1.1;
  letter-spacing: -1px;
  text-shadow: 0 2px 10px rgba(255, 255, 255, 0.8);
}

.text-gradient {
  color: #7c3aed; /* Deep purple */
}

.hero-subtitle {
  font-size: 18px;
  color: #1e293b; /* Darker for readability */
  line-height: 1.6;
  margin-bottom: 56px;
  max-width: 480px;
  text-shadow: 0 1px 4px rgba(255, 255, 255, 0.6);
}

.feature-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 60px;
}

.feature-item {
  display: flex;
  align-items: center; /* 确保图标和文字垂直居中 */
  gap: 16px;
  background: rgba(255, 255, 255, 0.3);
  padding: 16px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(255, 255, 255, 0.5);
  transform: translateY(-2px);
}

.feature-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  color: #7c3aed;
  flex-shrink: 0;
}

.feature-info h3 {
  font-size: 17px;
  font-weight: 700;
  margin: 0 0 6px 0;
  color: #0f172a;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.feature-info p {
  font-size: 14px;
  color: #334155; /* Darker */
  margin: 0;
  line-height: 1.4;
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
}

.system-intro-card {
  padding: 28px;
  background: rgba(255, 255, 255, 0.4);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.6);
  border-radius: 20px;
  max-width: 400px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.02);
}

.system-intro-card h3 {
  font-size: 17px;
  font-weight: 700;
  color: #1e293b;
  margin: 0 0 12px 0;
}

.system-intro-card p {
  font-size: 14px;
  color: #475569;
  line-height: 1.6;
  margin: 0;
  font-weight: 500;
}

.login-panel {
  flex-shrink: 0;
  margin-right: 60px; /* 往左移一点，向中心靠拢 */
  transition: all 0.5s ease;
}

/* 🌟 核心登录卡片：极光白亚克力材质 */
/* 1. 修复登录舱，变得更加晶莹剔透 */
.login-glass-card {
  width: clamp(320px, 26vw, 400px); /* 缩小宽度 */
  padding: 40px 32px; /* 减小内边距 */
  background: rgba(255, 255, 255, 0.45) !important; 
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border: 1px solid rgba(255, 255, 255, 0.7) !important;
  box-shadow: 0 20px 40px rgba(139, 92, 246, 0.05) !important; 
  border-radius: 24px;
  min-height: 460px; /* 减小最小高度 */
  transition: all 0.3s ease;
}

.card-header {
  margin-bottom: 32px;
}

.card-header h2 {
  font-size: 30px;
  font-weight: 800;
  color: #0f172a;
  margin: 0 0 10px 0;
}

.card-header p {
  font-size: 15px;
  color: #64748b;
}

.login-tabs {
  display: flex;
  margin-bottom: 32px;
}

.tab-item {
  padding: 8px 0;
  font-size: 16px;
  font-weight: 700;
  color: #1e293b;
  margin-right: 36px;
  position: relative;
  opacity: 0.8;
}

.tab-item.active {
  color: #8b5cf6;
}
/* 去掉孤立的下划线，让它更像一个标题 */

/* 🌟 输入框重塑：融合进卡片 */
/* 2. 强化输入框的边界感 */
:deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.6) !important;
  box-shadow: 0 0 0 1px rgba(148, 163, 184, 0.3) inset !important; /* 加上极其精致的内边框 */
  border: none !important;
  border-radius: 10px;
  height: 52px;
  transition: all 0.3s;
}

:deep(.el-input__wrapper.is-focus) {
  background: #ffffff !important;
  border-color: #8b5cf6 !important;
  box-shadow: 0 0 0 4px rgba(139, 92, 246, 0.08) !important;
}

:deep(.el-input__inner) {
  font-weight: 500;
}

.form-utils {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 12px 0 36px 0;
}

/* 强化 Checkbox 可视化 */
:deep(.el-checkbox__inner) {
  border-color: #cbd5e1 !important;
  background-color: rgba(255, 255, 255, 0.8) !important;
}
:deep(.el-checkbox__label) {
  color: #475569 !important;
  font-weight: 500;
}

/* 🌟 登录按钮：科技感主色调 */
/* 3. 让登录按钮焕发微光 */
.login-btn {
  width: 100%;
  height: 52px;
  border-radius: 10px;
  font-size: 17px;
  font-weight: 700;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%) !important;
  border: none;
  box-shadow: 0 8px 16px rgba(139, 92, 246, 0.25) !important; /* 给按钮加一层紫色的发光阴影 */
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: white !important;
}

.login-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(139, 92, 246, 0.35);
  filter: brightness(1.05);
}

:deep(.el-checkbox.is-checked .el-checkbox__inner) {
  background-color: #8b5cf6 !important;
  border-color: #8b5cf6 !important;
}
:deep(.el-checkbox.is-checked .el-checkbox__label) {
  color: #8b5cf6 !important;
}

.purple-link {
  color: #7c3aed !important;
  font-weight: 600;
  transition: all 0.3s;
}

.purple-link:hover {
  color: #6d28d9 !important;
  opacity: 0.8;
}

.register-footer {
  margin-top: 32px;
  text-align: center;
  font-size: 15px;
  color: #64748b;
  display: flex;
  justify-content: center;
  gap: 8px;
}

/* Security Footer */
.security-footer {
  padding: 40px 80px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #64748b; /* 加深辅助文字颜色 */
  text-shadow: 0 0 4px rgba(255,255,255,0.8); /* 文字发光以剥离复杂背景 */
}

.security-badges {
  display: flex;
  gap: 40px;
}

.badge-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.badge-item .el-icon {
  font-size: 18px;
  color: #cbd5e1;
}

/* Fix for Select border and dropdown items */
:deep(.el-select .el-input.is-focus .el-input__wrapper),
:deep(.el-select .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #8b5cf6 inset !important;
  border-color: #8b5cf6 !important;
}

:deep(.el-select:hover:not(.el-select--disabled) .el-input__wrapper) {
  box-shadow: 0 0 0 1px #8b5cf6 inset !important;
}

:deep(.el-select-dropdown__item.selected) {
  color: #8b5cf6 !important;
  font-weight: 700;
}

:deep(.el-select-dropdown__item.hover), 
:deep(.el-select-dropdown__item:hover) {
  background-color: rgba(139, 92, 246, 0.08) !important;
  color: #8b5cf6 !important;
}

:deep(.el-form-item.is-required:not(.is-no-asterisk).asterisk-left > .el-form-item__label:before) {
  color: #8b5cf6 !important;
}

/* Transitions */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}
.form-fade-enter-from {
  opacity: 0;
  transform: translateX(40px);
}
.form-fade-leave-to {
  opacity: 0;
  transform: translateX(-40px);
}

.register-section :deep(.el-form-item__label) {
  padding-bottom: 6px;
  font-weight: 600;
  color: #475569;
}

/* Responsive */
@media (max-width: 1440px) {
  .main-content {
    padding: 0 40px;
    gap: 40px;
  }
}

@media (max-width: 1024px) {
  .hero-area {
    display: none;
  }
  .main-content {
    justify-content: center;
  }
  .login-glass-card {
    width: 440px;
    max-width: 100%;
  }
}

@media (max-width: 480px) {
  .login-glass-card {
    padding: 32px 20px;
    border-radius: 0;
    width: 100vw;
    height: 100vh;
    min-height: 100vh;
  }
  .top-nav {
    padding: 20px;
  }
}
</style>

<style>
/* Global styles for MessageBox in body */
.purple-confirm-button {
  background: linear-gradient(135deg, #a78bfa 0%, #8b5cf6 100%) !important;
  border: none !important;
  color: white !important;
  font-weight: 600 !important;
  padding: 8px 20px !important;
  border-radius: 8px !important;
  transition: all 0.3s !important;
}

.purple-confirm-button:hover {
  transform: translateY(-1px) !important;
  filter: brightness(1.1) !important;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2) !important;
}
</style>
