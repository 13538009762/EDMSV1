<template>
  <div v-loading="loading" class="diff-page-container">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">{{ t("diff.title") }}</h2>
        <div v-if="mode === 'blame' && legend.length" class="blame-legend">
          <span v-for="l in legend" :key="l.name" class="legend-item">
            <span class="color-box" :style="{ backgroundColor: l.color }"></span>
            <span class="author-name">{{ l.name }}</span>
          </span>
        </div>
      </div>
      <el-radio-group v-model="mode" @change="onModeChange" class="mode-toggle">
        <el-radio-button label="compare">{{ t("diff.modes.compare") }}</el-radio-button>
        <el-radio-button label="blame">{{ t("diff.modes.blame") }}</el-radio-button>
      </el-radio-group>
    </div>

    <div class="toolbar" v-if="mode === 'compare'">
      <el-select v-model="fromId" :placeholder="t('diff.fromVersion')" class="version-select">
        <el-option
          v-for="v in versions"
          :key="v.id"
          :label="t('diff.versionLabel', { no: v.version_no, name: v.created_by_name })"
          :value="v.id"
        />
      </el-select>
      <el-select v-model="toId" :placeholder="t('diff.toVersion')" class="version-select">
        <el-option
          v-for="v in versions"
          :key="v.id"
          :label="t('diff.versionLabel', { no: v.version_no, name: v.created_by_name })"
          :value="v.id"
        />
      </el-select>
      <el-radio-group v-model="diffMode" size="small" class="diff-mode-select">
        <el-radio-button label="inline">{{ t("diff.modes.inline") }}</el-radio-button>
        <el-radio-button label="side_by_side">{{ t("diff.modes.sideBySide") }}</el-radio-button>
      </el-radio-group>
      <el-button type="primary" @click="loadDiff">{{ t("diff.compare") }}</el-button>
    </div>

    <div class="diff-content-wrapper">
      <div v-if="html" class="diff-box" :class="[mode, diffMode]" v-html="html" />
      <el-empty v-else-if="!loading" :description="t('common.noData', 'No data')" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { useI18n } from "vue-i18n";
import api from "@/api/client";

const route = useRoute();
const { t } = useI18n();
const id = Number(route.params.id);
const versions = ref<Array<{ id: number; version_no: number; created_by_name: string }>>([]);
const fromId = ref<number | undefined>();
const toId = ref<number | undefined>();
const html = ref("");
const loading = ref(false);
const mode = ref("compare");
const diffMode = ref("inline");
const legend = ref<Array<{name: string, color: string}>>([]);

async function loadVers() {
  const { data } = await api.get(`/documents/${id}/versions`);
  versions.value = data.items;
  if (data.items.length >= 2) {
    fromId.value = data.items[1]!.id; // second latest (it's sorted desc)
    toId.value = data.items[0]!.id;   // latest
  } else if (data.items.length === 1) {
    fromId.value = data.items[0]!.id;
    toId.value = data.items[0]!.id;
  }
}

function onModeChange() {
  html.value = "";
  if (mode.value === 'blame') {
    loadBlame();
  } else {
    loadDiff();
  }
}

watch(diffMode, () => {
    if (mode.value === 'compare') loadDiff();
});

async function loadBlame() {
  loading.value = true;
  try {
    const { data } = await api.get(`/documents/${id}/blame`);
    html.value = data.html;
    legend.value = data.legend;
  } finally {
    loading.value = false;
  }
}

async function loadDiff() {
  if (!fromId.value || !toId.value) return;
  loading.value = true;
  try {
    const { data } = await api.get(`/documents/${id}/diff`, {
      params: { from: fromId.value, to: toId.value, mode: diffMode.value },
    });
    html.value = data.html;
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  await loadVers();
  if (mode.value === 'compare') await loadDiff();
});
</script>

<style scoped>
.diff-page-container {
  padding: 30px 40px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
}

.page-title {
  margin: 0 0 12px 0;
  font-size: 24px;
  color: #1a1a1a;
}

.header-left {
  display: flex;
  flex-direction: column;
}

.toolbar {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.version-select {
  width: 200px;
}

.diff-content-wrapper {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.05);
  overflow: hidden;
  min-height: 400px;
}

.diff-box.side_by_side {
  padding: 0;
}

.diff-box.side_by_side :deep(table.diff) {
  width: 100%;
  border-collapse: collapse;
  font-family: 'Fira Code', 'Courier New', monospace;
  font-size: 13px;
}

.diff-box.side_by_side :deep(.diff_header) {
  background-color: #f8f9fa;
  color: #adb5bd;
  text-align: right;
  padding: 4px 10px;
  width: 1%;
  white-space: nowrap;
  border-right: 1px solid #e9ecef;
  user-select: none;
}

.diff-box.side_by_side :deep(td) {
  padding: 4px 12px;
  line-height: 1.6;
  vertical-align: top;
  word-break: break-all;
}

.diff-box.side_by_side :deep(.diff_add) {
  background-color: #e6ffec;
}

.diff-box.side_by_side :deep(.diff_chg) {
  background-color: #fffbdd;
}

.diff-box.side_by_side :deep(.diff_sub) {
  background-color: #ffeef0;
}

.diff-box.side_by_side :deep(ins) {
  background-color: #acf2bd;
  text-decoration: none;
}

.diff-box.side_by_side :deep(del) {
  background-color: #fdb8c0;
  text-decoration: none;
}

.blame-legend {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.legend-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #666;
}

.color-box {
  width: 12px;
  height: 12px;
  border-radius: 2px;
  margin-right: 6px;
}

.author-name {
  font-weight: 500;
}

/* Customize scrollbar for a more premium look */
::-webkit-scrollbar {
  width: 8px;
}
::-webkit-scrollbar-track {
  background: #f1f1f1;
}
::-webkit-scrollbar-thumb {
  background: #ccc;
  border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover {
  background: #999;
}
</style>
