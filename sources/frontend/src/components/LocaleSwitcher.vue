<template>
  <el-dropdown trigger="click" @command="onLocale">
    <span class="trigger">
      {{ t("nav.language") }}
      <span class="caret">▾</span>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="en">{{ t("nav.english") }}</el-dropdown-item>
        <el-dropdown-item command="zh-CN">{{ t("nav.chinese") }}</el-dropdown-item>
        <el-dropdown-item command="ru">{{ t("nav.russian") }}</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { saveLocale, type LocaleCode } from "@/i18n";

const { locale, t } = useI18n();

function onLocale(cmd: string) {
  const code = cmd as LocaleCode;
  locale.value = code;
  saveLocale(code);
}
</script>

<style scoped>
.trigger {
  cursor: pointer;
  color: var(--el-color-primary);
  font-size: 14px;
}
.caret {
  margin-left: 4px;
  font-size: 10px;
  opacity: 0.7;
}
</style>
