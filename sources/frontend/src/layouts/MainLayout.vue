<template>
  <el-container class="edms-layout-wrapper">
    <el-aside :width="isCollapse ? '64px' : '240px'" class="edms-sidebar">
      <div class="sidebar-brand">
        <img src="/favicon.png" class="brand-logo" alt="Logo" />
        <span v-if="!isCollapse" class="brand">EDMS</span>
      </div>
      
      <el-menu 
        :default-active="route.path"
        router
        :collapse="isCollapse"
        :collapse-transition="false"
        class="edms-menu"
      >
        <el-menu-item index="/">
          <el-icon><Reading /></el-icon>
          <span>{{ t("nav.library", "Library") }}</span>
        </el-menu-item>
        <el-menu-item index="/dashboard">
          <el-icon><DataLine /></el-icon>
          <span>{{ t("nav.dashboard", "Dashboard") }}</span>
        </el-menu-item>
        <el-menu-item index="/templates">
          <el-icon><CopyDocument /></el-icon>
          <span>{{ t("nav.templates", "Templates") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.login_name === 'admin' || auth.user?.is_manager" index="/template-admin">
          <el-icon><Grid /></el-icon>
          <span>{{ t("nav.templateAdmin", "Template Mgmt") }}</span>
        </el-menu-item>
        <el-menu-item index="/inbox">
          <el-icon><Message /></el-icon>
          <span>{{ t("nav.inbox", "Approval Inbox") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.is_manager" index="/users">
          <el-icon><User /></el-icon>
          <span>{{ t("nav.users", "Member Management") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.login_name === 'admin'" index="/import">
          <el-icon><Setting /></el-icon>
          <span>{{ t("nav.masterData", "Master Data") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.login_name === 'admin'" index="/audit-log">
          <el-icon><Monitor /></el-icon>
          <span>{{ t("nav.auditLog", "Audit Log") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.login_name === 'admin'" index="/ai-history">
          <el-icon><MagicStick /></el-icon>
          <span>{{ t("nav.aiHistory", "AI Audit") }}</span>
        </el-menu-item>
        <el-menu-item index="/ai" class="ai-menu-item">
          <el-icon class="magic-icon"><MagicStick /></el-icon>
          <template #title>
            <span class="ai-text">{{ t("nav.aiAssistant") }}</span>
          </template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="main-container">
      <el-header class="edms-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <component :is="isCollapse ? Expand : Fold" />
          </el-icon>
          <span class="logo-text">Ecosystem of Document Matrix & Security 全栈智能协同与可信文档管理平台</span>
        </div>
        <div class="spacer" />
        
        <el-dropdown trigger="click" @command="readNotification" @visible-change="onNotifVisible" style="margin-right: 16px;">
          <el-badge :value="unreadCount" :max="99" class="item" :hidden="unreadCount === 0 || badgeHiddenLocally">
            <el-button link class="notification-btn" style="padding-top: 4px;"><el-icon size="20"><Bell /></el-icon></el-button>
          </el-badge>
          <template #dropdown>
            <el-dropdown-menu style="width: 300px; max-height: 400px; overflow-y: auto;">
              <div style="padding: 10px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--el-border-color-lighter);">
                <span style="font-weight: bold;">{{ t('nav.notifications', 'Notifications') }}</span>
                <el-button size="small" type="primary" link @click="markAllRead" v-if="unreadCount > 0">{{ t('common.markAllRead', 'Mark all read') }}</el-button>
              </div>
              <el-dropdown-item v-for="n in notifications.slice(0, 5)" :key="n.id" class="notif-dropdown-item">
                <div class="notif-item-content" :style="{ opacity: n.is_read ? 0.6 : 1 }" @click="readNotification(n)">
                  <div class="notif-text">
                    <div class="notif-title">{{ n.title }}</div>
                    <div class="notif-time">{{ formatLocalDate(n.created_at) }}</div>
                  </div>
                  <div class="notif-ops">
                    <el-button 
                      link 
                      size="large"
                      class="op-btn-large"
                      :style="{ color: n.is_starred ? '#E6A23C' : '#909399' }"
                      @click.stop="toggleStar(n)"
                    >
                      <el-icon :size="20"><component :is="n.is_starred ? StarFilled : Star" /></el-icon>
                    </el-button>
                    <el-button 
                      link 
                      size="large"
                      class="op-btn-large"
                      style="color: #F56C6C;"
                      @click.stop="deleteNotif(n)"
                    >
                      <el-icon :size="20"><Delete /></el-icon>
                    </el-button>
                  </div>
                </div>
              </el-dropdown-item>
              <el-dropdown-item v-if="notifications.length === 0" disabled>{{ t('nav.noNotifications', 'No new notifications') }}</el-dropdown-item>
              
              <div v-if="notifications.length > 5" style="border-top: 1px solid var(--el-border-color-lighter); padding: 8px; text-align: center;">
                <el-button link type="primary" size="small" @click="router.push({ name: 'notifications' })">
                  {{ t('nav.viewMore', 'View More') }}...
                </el-button>
              </div>
            </el-dropdown-menu>
          </template>
        </el-dropdown>

        <LocaleSwitcher />
        <div v-if="auth.user" class="user-profile">
          <el-tag
            size="small"
            effect="dark"
            class="role-badge"
          >
            {{ auth.user?.login_name === 'admin' ? t('common.roles.admin') : (auth.user?.is_manager ? t('common.roles.manager') : t('common.roles.user')) }}
          </el-tag>
          <el-avatar size="small" :style="{ backgroundColor: 'var(--el-color-primary)' }">
            {{ (auth.user?.display_name || auth.user?.login_name || "U").charAt(0).toUpperCase() }}
          </el-avatar>
          <el-button v-if="auth.user" type="primary" link @click="router.push({ name: 'personal' })">{{ auth.user.display_name || auth.user.login_name }}</el-button>
        </div>
        <el-button type="primary" link @click="onLogout">
          <el-icon><SwitchButton /></el-icon>
        </el-button>
      </el-header>

      <el-main class="edms-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-slide" mode="out-in">
            <component :is="Component" :key="$route.path" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useAiStore } from "@/stores/ai";
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { onMounted, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { 
  Reading, DataLine, Bell, Message, Setting, SwitchButton, 
  Monitor, CopyDocument, User, Star, StarFilled, Delete,
  Expand, Fold, MagicStick, Grid
} from "@element-plus/icons-vue";
import { formatLocalDate } from "@/utils/date";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const notifications = ref<any[]>([]);
const unreadCount = ref(0);
const badgeHiddenLocally = ref(false);
let notifTimer: any = null;

async function loadNotifications() {
  if (!auth.token) return;
  try {
    const { data } = await api.get('/notifications');
    notifications.value = data.items;
    
    // 如果未读数量增加了，说明有新消息，重新显示红点
    if (data.unread_count > unreadCount.value) {
      badgeHiddenLocally.value = false;
    }
    unreadCount.value = data.unread_count;
  } catch(e) {}
}

async function markAllRead() {
  try {
    await api.post('/notifications/read-all');
    loadNotifications();
  } catch(e) {}
}

async function readNotification(n: any) {
  try {
    if (!n.is_read) {
      await api.post(`/notifications/${n.id}/read`);
      n.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    }
    if (n.link_url) {
      router.push(n.link_url);
    }
  } catch(e) {}
}

async function toggleStar(n: any) {
  try {
    const { data } = await api.post(`/notifications/${n.id}/star`);
    n.is_starred = data.is_starred;
  } catch(e) {}
}

async function deleteNotif(n: any) {
  try {
    await api.delete(`/notifications/${n.id}`);
    notifications.value = notifications.value.filter(x => x.id !== n.id);
  } catch(e) {}
}

const isCollapse = ref(false);

const onNotifVisible = (v: boolean) => {
  if (v) {
    badgeHiddenLocally.value = true;
  }
};

const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value;
};

const checkWindowSize = () => {
  if (window.innerWidth < 1024) {
    isCollapse.value = true;
  } else {
    isCollapse.value = false;
  }
};

onMounted(() => {
  auth.fetchMe().catch(() => {});
  if (auth.token) {
    loadNotifications();
    notifTimer = setInterval(loadNotifications, 30000); // Poll every 30s
  }
  checkWindowSize();
  window.addEventListener('resize', checkWindowSize);
});
onBeforeUnmount(() => {
  if (notifTimer) clearInterval(notifTimer);
  window.removeEventListener('resize', checkWindowSize);
});

function onLogout() {
  const aiStore = useAiStore();
  aiStore.clearHistory('global');
  aiStore.clearHistory('editor');
  auth.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>

.edms-layout-wrapper {
  height: 100vh !important;
  overflow: hidden; /* 锁死最外层，禁止全局滚动 */
}

/* 2. 侧边栏：撑满屏幕高度，内部弹性布局 */
.edms-sidebar {
  height: 100vh;
  background-color: var(--edms-sidebar-bg) !important;
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 2px 0 8px rgba(0,0,0,0.02);
  z-index: 20;
  display: flex;
  flex-direction: column;
  transition: width 0.3s ease;
}

.sidebar-brand {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 20px;
  gap: 12px;
}

.brand-logo {
  height: 32px;
  width: auto;
  filter: drop-shadow(0 2px 4px rgba(0,0,0,0.1));
}

.brand {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--el-color-primary);
}

.edms-menu {
  border-right: none;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 隐藏侧边栏滚动条 */
.edms-menu::-webkit-scrollbar {
  width: 0px;
  background: transparent;
}

/* 3. 苹果风毛玻璃顶栏 */
.edms-header {
  background-color: var(--edms-header-bg);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: var(--edms-border);
  position: sticky;
  top: 0;
  z-index: 10;
  display: flex;
  align-items: center;
  padding: 0 24px;
}

.header-left {
  display: flex;
  align-items: center;
}

.collapse-btn {
  font-size: 20px;
  cursor: pointer;
  margin-right: 16px;
  color: var(--el-text-color-primary);
  transition: transform 0.3s ease;
}

.collapse-btn:hover {
  transform: scale(1.1);
  color: var(--el-color-primary);
}

.logo-text {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--el-text-color-primary);
}

.spacer {
  flex: 1;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 16px 0 12px;
}

.role-badge {
  border: none;
  background-color: var(--el-color-primary) !important;
  font-weight: 600;
  border-radius: 4px;
}

.main-container {
  height: 100vh;
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.edms-main {
  flex: 1;
  overflow-y: auto; /* 核心：只有内容区域允许滚动 */
  overflow-x: hidden;
  padding: 16px;
}

/* 美化主区域滚动条 */
.edms-main::-webkit-scrollbar {
  width: 8px;
}
.edms-main::-webkit-scrollbar-thumb {
  background-color: rgba(156, 163, 175, 0.3);
  border-radius: 4px;
}

@media (min-width: 1024px) {
  .edms-main {
    padding: 24px;
  }
}

/* ==========================================
   路由切换：开启 GPU 硬件加速的丝滑过渡
========================================== */
.fade-slide-enter-active,
.fade-slide-leave-active {
  /* 使用贝塞尔曲线，模仿 PPT/iOS那种“起步快，结尾柔和”的阻尼感 */
  transition: opacity 0.25s cubic-bezier(0.2, 0.8, 0.2, 1), 
              transform 0.25s cubic-bezier(0.2, 0.8, 0.2, 1);
  /* 🌟 核心：强行通知浏览器将此元素扔给 GPU 渲染，彻底解放 CPU */
  will-change: transform, opacity; 
}

.fade-slide-enter-from {
  opacity: 0;
  /* 使用 translate3d 替代 translateY 强制开启 3D 加速 */
  transform: translate3d(0, 15px, 0); 
}

.fade-slide-leave-to {
  opacity: 0;
  transform: translate3d(0, -15px, 0);
}

/* Notification Styles */
.notif-dropdown-item {
  padding: 0 !important;
}
.notif-item-content {
  padding: 10px 16px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  width: 100%;
}
.notif-text {
  flex: 1;
  margin-right: 12px;
  overflow: hidden;
}
.notif-title {
  font-weight: 500;
  font-size: 13px;
  line-height: 1.4;
  margin-bottom: 4px;
  color: var(--el-text-color-primary);
  white-space: normal;
}
.notif-time {
  font-size: 11px;
  color: var(--el-text-color-secondary);
}
.notif-ops {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.op-btn-large {
  padding: 8px !important;
  font-size: 20px !important;
}

.ai-menu-item {
  border-left: 3px solid transparent !important;
  margin-bottom: 4px;
  transition: all 0.3s ease !important;
}

.ai-menu-item:hover, .ai-menu-item.is-active {
  background: linear-gradient(90deg, rgba(64, 158, 255, 0.1) 0%, transparent 100%) !important;
  border-left: 3px solid var(--el-color-primary) !important;
}

.ai-menu-item .magic-icon {
  color: var(--el-color-primary) !important;
}

.ai-text {
  font-weight: bold;
  background: linear-gradient(45deg, var(--el-color-primary), #7367f0);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
</style>
