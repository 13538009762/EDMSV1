<template>
  <el-dropdown trigger="click" @command="onLocale">
    <span class="trigger" :class="{ 'is-purple': purple }">
      <svg class="icon" viewBox="0 0 24 24" width="1em" height="1em" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="10"></circle>
        <line x1="2" y1="12" x2="22" y2="12"></line>
        <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
      </svg>
      <span class="lang-text">{{ t("nav.language") }}</span>
      <span class="caret">▼</span>
    </span>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="en">{{ t("nav.english") }}</el-dropdown-item>
        <el-dropdown-item command="zh-CN">{{ t("nav.chinese") }}</el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup lang="ts">
import { useI18n } from "vue-i18n";
import { saveLocale, type LocaleCode } from "@/i18n";

defineProps<{
  purple?: boolean;
}>();

const { locale, t } = useI18n();

function onLocale(cmd: string) {
  const code = cmd as LocaleCode;
  locale.value = code;
  saveLocale(code);
}
</script>

<style scoped>
.trigger {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  color: var(--el-text-color-regular);
  font-size: 14px;
  font-weight: 500;
  background-color: var(--el-bg-color);
  padding: 8px 16px;
  border-radius: 20px;
  border: 1px solid var(--el-border-color-light);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
  user-select: none;
}

.trigger:hover {
  color: var(--el-color-primary);
  border-color: var(--el-color-primary-light-5);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateY(-1px);
}

.trigger.is-purple:hover {
  color: #8b5cf6;
  border-color: rgba(139, 92, 246, 0.3);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
}

.trigger:active {
  transform: translateY(0);
}

.icon {
  margin-right: 6px;
  font-size: 16px;
  color: var(--el-color-primary);
}

.is-purple .icon {
  color: #8b5cf6;
}

.lang-text {
  margin-right: 6px;
}

.caret {
  font-size: 10px;
  opacity: 0.5;
  transition: transform 0.3s ease;
}

.el-dropdown-menu__item {
  min-width: 120px;
}

:deep(.el-dropdown-menu__item:not(.is-disabled):focus),
:deep(.el-dropdown-menu__item:not(.is-disabled):hover) {
  background-color: rgba(139, 92, 246, 0.08) !important;
  color: #8b5cf6 !important;
}
</style>
