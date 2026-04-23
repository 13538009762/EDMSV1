<template>
  <el-config-provider :locale="elementLocale">
    <div id="app-wrapper">
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
import { useI18n } from "vue-i18n";
import en from "element-plus/es/locale/lang/en";
import zhCn from "element-plus/es/locale/lang/zh-cn";

const { locale, t } = useI18n();

const elementLocale = computed(() => (locale.value === "zh-CN" ? zhCn : en));

watch(
  locale,
  (l) => {
    document.documentElement.lang = l === "zh-CN" ? "zh-CN" : "en";
    document.title = t("app.title");
  },
  { immediate: true },
);
</script>

<style>
:root {
  --app-font-ui: 'Inter', system-ui, -apple-system, sans-serif;
  --app-font-title: 'Outfit', 'Inter', sans-serif;
  --app-primary-gradient: linear-gradient(135deg, #6366f1 0%, #a855f7 100%);
}

html,
body,
#app,
#app-wrapper {
  margin: 0;
  height: 100%;
  font-family: var(--app-font-ui);
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background-color: #f8fafc;
  color: #1e293b;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--app-font-title);
  font-weight: 600;
  letter-spacing: -0.02em;
}

/* Custom Scrollbar */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}
::-webkit-scrollbar-track {
  background: #f1f5f9;
}
::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}

/* Global Transitions */
.el-button, .el-card, .el-input__inner {
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
}

.el-card {
  border: 1px solid rgba(226, 232, 240, 0.8);
  box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
}
</style>
