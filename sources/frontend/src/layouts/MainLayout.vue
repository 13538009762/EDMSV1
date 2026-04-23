<template>
  <el-container class="edms-layout-wrapper">
    <el-aside width="240px" class="edms-sidebar">
      <div class="sidebar-brand">
        <img src="/favicon.png" class="brand-logo" alt="Logo" />
        <span class="brand">EDMS</span>
      </div>
      
      <el-menu 
        :default-active="route.path"
        router
        background-color="var(--edms-sidebar-bg)" 
        text-color="var(--edms-sidebar-text)"
        active-text-color="var(--el-color-primary)"
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
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="edms-header">
        <div class="header-content">
          <span class="logo-text">EDMS 零信任架构</span>
        </div>
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
            <component :is="Component" />
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { onMounted, onBeforeUnmount, ref, computed, watch } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { 
  Reading, DataLine, Bell, Message, Setting, SwitchButton, 
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

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
/* 1. 环境光底板 */
.edms-layout-wrapper {
  height: 100vh;
  background-color: var(--edms-body-bg);
  background-image: var(--edms-ambient-glow);
  background-repeat: no-repeat;
  background-attachment: fixed;
}

/* 2. 侧边栏质感 */
.edms-sidebar {
  background-color: var(--edms-sidebar-bg);
  border-right: 1px solid rgba(0, 0, 0, 0.05);
  box-shadow: 2px 0 8px rgba(0,0,0,0.02);
  z-index: 20;
  display: flex;
  flex-direction: column;
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

.header-content {
  display: flex;
  align-items: center;
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

.edms-main {
  padding: 0;
  overflow: auto;
}

/* 4. 路由丝滑动画 */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}
.fade-slide-enter-from { opacity: 0; transform: translateY(15px); }
.fade-slide-leave-to { opacity: 0; transform: translateY(-15px); }

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
</style>
