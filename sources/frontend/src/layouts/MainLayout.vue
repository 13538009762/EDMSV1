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
            <el-dropdown-item v-for="n in notifications" :key="n.id" :command="n">
              <div :style="{ opacity: n.is_read ? 0.6 : 1, padding: '4px 0', width: '100%' }">
                <div style="font-weight: 500; font-size: 13px; margin-bottom: 4px; white-space: normal;">{{ n.title }}</div>
                <div style="font-size: 12px; color: var(--el-text-color-secondary);">{{ formatLocalDate(n.created_at) }}</div>
              </div>
            </el-dropdown-item>
            <el-dropdown-item v-if="notifications.length === 0" disabled>{{ t('nav.noNotifications', 'No new notifications') }}</el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <LocaleSwitcher />
      <div v-if="auth.user" class="user-profile">
        <el-avatar size="small" :style="{ backgroundColor: 'var(--el-color-primary)' }">
          {{ auth.user.display_name.charAt(0).toUpperCase() }}
        </el-avatar>
         <el-button v-if="auth.user" type="primary" link @click="router.push({ name: 'personal' })">{{ auth.user.display_name }}</el-button>
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
import { onMounted, onBeforeUnmount, ref } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { Platform, Reading, DataLine, Bell, Message, Setting, SwitchButton, Monitor, CopyDocument, User } from "@element-plus/icons-vue";

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


function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}

</script>

<style scoped>
.layout {
  height: 100vh;
  background-color: var(--el-bg-color-page);
}
.header {
  display: flex;
  align-items: center;
  background: white;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
  z-index: 100;
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
</style>
