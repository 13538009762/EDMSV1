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
        <el-menu-item index="/inbox">
          <el-icon><Bell /></el-icon>
          <span>{{ t("nav.inbox", "Approval Inbox") }}</span>
        </el-menu-item>
        <el-menu-item v-if="auth.user?.is_manager" index="/import">
          <el-icon><Setting /></el-icon>
          <span>{{ t("nav.masterData", "Master Data") }}</span>
        </el-menu-item>
      </el-menu>
      <div class="spacer" />
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
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";
import { useAuthStore } from "@/stores/auth";
import { onMounted } from "vue";
import { useI18n } from "vue-i18n";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { Platform, Reading, DataLine, Bell, Setting, SwitchButton } from "@element-plus/icons-vue";

const route = useRoute();
const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

onMounted(() => {
  auth.fetchMe().catch(() => {});
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
