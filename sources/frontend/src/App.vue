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
  color: #1e293b;
}
</style>
