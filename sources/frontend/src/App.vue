npm<template>
  <el-config-provider :locale="elementLocale">
    <router-view />
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
html,
body,
#app {
  margin: 0;
  height: 100%;
  font-family:
    system-ui,
    -apple-system,
    sans-serif;
}
</style>
