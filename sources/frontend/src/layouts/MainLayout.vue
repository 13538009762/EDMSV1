<template>
  <el-container class="layout">
    <el-header class="header">
      <div class="brand-container">
        <el-icon class="brand-icon"><Platform /></el-icon>
        <span class="brand">EDMS</span>
      </div>
      <el-menu mode="horizontal" router :default-active="route.path" class="menu" :ellipsis="false">
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
        <el-menu-item index="/inbox">
          <el-icon><Message /></el-icon>
          <span>{{ t("nav.inbox", "Approval Inbox") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.is_manager" index="/users">
          <el-icon><User /></el-icon>
          <span>{{ t("nav.users", "Member Management") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.login_name === 'admin'" index="/audit-log">
          <el-icon><Monitor /></el-icon>
          <span>{{ t("nav.auditLog", "Audit Log") }}</span>
        </el-menu-item>
      </el-menu>
      <div class="spacer" />
      
      <el-dropdown trigger="click" @command="readNotification" style="margin-right: 16px;">
        <el-badge :value="unreadCount" :max="99" class="item" :hidden="unreadCount === 0">
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
          :type="auth.user?.login_name === 'admin' ? 'danger' : (auth.user?.is_manager ? 'primary' : 'success')"
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
    <el-main class="main">
      <router-view :key="route.fullPath" />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { onMounted, onBeforeUnmount, ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { 
  Platform, Reading, DataLine, Bell, Message, Setting, SwitchButton, 
  Monitor, CopyDocument, User, Star, StarFilled, Delete 
} from "@element-plus/icons-vue";
import { formatLocalDate } from "@/utils/date";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const notifications = ref<any[]>([]);
const unreadCount = ref(0);
let notifTimer: any = null;

async function loadNotifications() {
  if (!auth.token) return;
  try {
    const { data } = await api.get('/notifications');
    notifications.value = data.items;
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

onMounted(() => {
  auth.fetchMe().catch(() => {});
  if (auth.token) {
    loadNotifications();
    notifTimer = setInterval(loadNotifications, 30000); // Poll every 30s
  }
});
onBeforeUnmount(() => {
  if (notifTimer) clearInterval(notifTimer);
});


watch(() => auth.user, (user) => {
  if (!user) {
    document.documentElement.classList.remove('theme-admin', 'theme-manager', 'theme-user');
    return;
  }
  
  // Remove all first
  document.documentElement.classList.remove('theme-admin', 'theme-manager', 'theme-user');
  
  if (user.login_name === 'admin') {
    document.documentElement.classList.add('theme-admin');
  } else if (user.is_manager) {
    document.documentElement.classList.add('theme-manager');
  } else {
    document.documentElement.classList.add('theme-user');
  }
}, { immediate: true });

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}

</script>

<style>
/* Global Theme Variables */
html.theme-admin {
  --el-color-primary: #8b5cf6 !important; /* Royal Purple */
  --el-color-primary-light-3: #a78bfa !important;
  --el-color-primary-light-5: #c4b5fd !important;
  --el-color-primary-light-7: #ddd6fe !important;
  --el-color-primary-light-8: #ede9fe !important;
  --el-color-primary-light-9: #f5f3ff !important;
  --el-color-primary-dark-2: #7c3aed !important;
}

html.theme-manager {
  --el-color-primary: #2563eb !important; /* Business Blue */
  --el-color-primary-light-3: #60a5fa !important;
  --el-color-primary-light-5: #93c5fd !important;
  --el-color-primary-light-7: #bfdbfe !important;
  --el-color-primary-light-8: #dbeafe !important;
  --el-color-primary-light-9: #eff6ff !important;
  --el-color-primary-dark-2: #1d4ed8 !important;
}

html.theme-user {
  --el-color-primary: #0d9488 !important; /* Modern Teal */
  --el-color-primary-light-3: #2dd4bf !important;
  --el-color-primary-light-5: #5eead4 !important;
  --el-color-primary-light-7: #99f6e4 !important;
  --el-color-primary-light-8: #ccfbf1 !important;
  --el-color-primary-light-9: #f0fdfa !important;
  --el-color-primary-dark-2: #0f766e !important;
}

/* Transition for smooth theme switching */
html {
  transition: background-color 0.3s, color 0.3s;
}

/* Background Ambient Glow */
html.theme-admin .layout {
  background-image: 
    radial-gradient(at 0% 0%, rgba(139, 92, 246, 0.05) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(139, 92, 246, 0.05) 0px, transparent 50%);
}
html.theme-manager .layout {
  background-image: 
    radial-gradient(at 0% 0%, rgba(37, 99, 235, 0.05) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(37, 99, 235, 0.05) 0px, transparent 50%);
}
html.theme-user .layout {
  background-image: 
    radial-gradient(at 0% 0%, rgba(13, 148, 136, 0.05) 0px, transparent 50%),
    radial-gradient(at 100% 100%, rgba(13, 148, 136, 0.05) 0px, transparent 50%);
}

/* Specific Layout Header Style (Glassmorphism) */
.layout > .header {
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  z-index: 2000;
  position: sticky;
  top: 0;
  transition: all 0.3s;
}

html.theme-admin .layout > .header {
  background-color: rgba(255, 255, 255, 0.7);
  border-bottom: 2px solid rgba(139, 92, 246, 0.2);
}

html.theme-manager .layout > .header {
  background-color: rgba(255, 255, 255, 0.7);
  border-bottom: 2px solid rgba(37, 99, 235, 0.2);
}

html.theme-user .layout > .header {
  background-color: rgba(255, 255, 255, 0.7);
  border-bottom: 2px solid rgba(13, 148, 136, 0.2);
}
</style>

<style scoped>
.layout {
  height: 100vh;
  background-color: #f8fafc;
}
.header {
  display: flex;
  align-items: center;
  /* background: white; */ /* Handled by glassmorphism in global style */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
  padding: 0 24px;
}
.brand-container {
  display: flex;
  align-items: center;
  margin-right: 32px;
  color: var(--el-color-primary);
}
.brand-icon {
  font-size: 24px;
  margin-right: 8px;
}
.brand {
  font-size: 20px;
  font-weight: 800;
  letter-spacing: 0.5px;
}
.menu {
  flex: 0 1 auto;
  border-bottom: none;
  background: transparent;
}
.el-menu-item {
  font-weight: 500;
  transition: all 0.2s !important;
}
.el-menu-item.is-active {
  color: var(--el-color-primary) !important;
  font-weight: 700;
}
.el-menu-item.is-active::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 12px;
  right: 12px;
  height: 3px;
  background: var(--el-color-primary);
  border-radius: 3px 3px 0 0;
  box-shadow: 0 -2px 8px var(--el-color-primary);
}
.main {
  padding: 0;
  overflow: auto;
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
.user {
  font-weight: 500;
  color: var(--el-text-color-primary);
}
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
</style>
