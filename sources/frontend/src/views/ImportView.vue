<template>
  <div class="page-container">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><Setting /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t("nav.masterData", "Master Data Management") }}</h1>
          <p class="page-sub">{{ t("import.hint") }}</p>
        </div>
      </div>
    </div>

    <div class="page-content">
      <el-card shadow="hover" class="import-card">
        <div class="upload-section">
          <div class="template-download">
            <el-button :icon="Download" @click="downloadTemplate" plain>
              {{ t('import.downloadTemplate') }}
            </el-button>
          </div>

          <div class="type-selector">
            <el-radio-group v-model="importType">
              <el-radio-button value="all">{{ t('import.typeAll') }}</el-radio-button>
              <el-radio-button value="departments">{{ t('import.typeDepts') }}</el-radio-button>
              <el-radio-button value="positions">{{ t('import.typePos') }}</el-radio-button>
              <el-radio-button value="employees">{{ t('import.typeUsers') }}</el-radio-button>
            </el-radio-group>
          </div>

          <el-upload
            class="upload-area"
            drag
            :auto-upload="false"
            :on-change="onFile"
            :limit="1"
            accept=".xlsx,.xlsm"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">
              {{ t("import.dragText") }} <em>{{ t("import.clickToUpload") }}</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                <el-icon><InfoFilled /></el-icon>
                {{ t("import.fileTip") }}
              </div>
            </template>
          </el-upload>

          <div class="mode-selector">
            <el-switch
              v-model="overwrite"
              :active-text="t('import.overwrite')"
              active-color="#ff4949"
            />
            <div class="mode-hint">
              <el-icon><Warning /></el-icon>
              {{ overwrite ? t('import.warning') : t('import.overwriteWarn') }}
            </div>
          </div>

          <div class="action-bar">
            <el-button
              type="primary"
              size="large"
              :icon="Upload"
              :loading="loading"
              :disabled="!file"
              @click="upload"
              class="submit-btn"
            >
              {{ t("import.upload") }}
            </el-button>
          </div>
        </div>

        <transition name="el-fade-in">
          <div v-if="result" class="result-section">
            <el-divider>{{ t("import.resultTitle") }}</el-divider>
            <el-alert v-if="!isError" :title="t('import.successTitle')" type="success" show-icon :closable="false" class="result-alert" />
            <el-alert v-else :title="t('import.errorTitle')" type="error" show-icon :closable="false" class="result-alert" />
            <div class="json-viewer"><pre>{{ JSON.stringify(result, null, 2) }}</pre></div>
          </div>
        </transition>
      </el-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { UploadFile } from "element-plus";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage, ElMessageBox } from "element-plus";
import { Upload, UploadFilled, InfoFilled, Warning, Download, Setting } from "@element-plus/icons-vue";

const { t } = useI18n();
const file = ref<File | null>(null);
const loading = ref(false);
const result = ref<unknown>(null);
const isError = ref(false);
const overwrite = ref(true);
const importType = ref("all");

function onFile(f: UploadFile) {
  file.value = f.raw || null;
  result.value = null;
  isError.value = false;
}

async function upload() {
  if (!file.value) return;
  
  try {
    await ElMessageBox.confirm(t('import.warning'), t('import.confirmTitle'), {
      confirmButtonText: t('import.confirmImport'),
      cancelButtonText: t('common.cancel'),
      type: 'warning',
    });
  } catch { return; }
  
  loading.value = true;
  result.value = null;
  isError.value = false;
  
  const fd = new FormData();
  fd.append("file", file.value);
  fd.append("overwrite", String(overwrite.value));
  fd.append("table_type", importType.value);
  try {
    const { data } = await api.post("/admin/master-data/import", fd);
    result.value = data;
    ElMessage.success(t("import.success"));
  } catch (e: unknown) {
    ElMessage.error(t("import.failed"));
    result.value = e;
    isError.value = true;
  } finally {
    loading.value = false;
  }
}

function downloadTemplate() {
  window.open(api.defaults.baseURL + "/admin/master-data/template", "_blank");
}
</script>

<style scoped>
.page-container {
  padding: 0;
  max-width: 1400px;
  margin: 0 auto;
}

.hero-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 32px 40px;
  background: linear-gradient(135deg, var(--el-color-primary) 0%, #7367f0 130%) !important;
  border-radius: 16px;
  margin-bottom: 24px;
  flex-wrap: wrap;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.header-icon-ring {
  width: 52px; height: 52px;
  border-radius: 50%;
  background: rgba(255,255,255,0.18);
  display: flex; align-items: center; justify-content: center;
  font-size: 24px;
  color: #fff;
  flex-shrink: 0;
}

.page-title {
  margin: 0 0 4px !important;
  font-size: 1.5rem !important;
  font-weight: 800 !important;
  color: #fff !important;
}

.page-sub {
  margin: 0 !important;
  font-size: 0.9rem !important;
  color: rgba(255,255,255,0.8) !important;
}

.page-content {
  padding: 0 24px 40px;
}

.import-card {
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.upload-area { width: 100%; max-width: 600px; }
.el-upload__tip { display: flex; align-items: center; justify-content: center; gap: 4px; margin-top: 12px; color: var(--el-text-color-secondary); font-size: 13px; }
.action-bar { margin-top: 32px; width: 100%; display: flex; justify-content: center; }
.template-download { margin-bottom: 24px; }
.submit-btn { width: 220px; border-radius: 8px; font-weight: 700; letter-spacing: 1px; margin-top: 12px; }
.type-selector { margin-bottom: 24px; }
.type-selector :deep(.el-radio-button__inner) { padding: 12px 24px; }
.result-section { margin-top: 24px; width: 100%; max-width: 800px; }
.mode-selector { margin-top: 24px; display: flex; flex-direction: column; align-items: center; border: 1px solid var(--el-border-color-lighter); padding: 16px; border-radius: 8px; background: var(--el-fill-color-blank); }
.mode-hint { margin-top: 12px; font-size: 13px; color: var(--el-text-color-secondary); display: flex; align-items: center; gap: 6px; text-align: center; max-width: 400px; }
.mode-hint .el-icon { color: var(--el-color-warning); font-size: 16px; }
.result-alert { margin-bottom: 16px; border-radius: 6px; }
.json-viewer { background: var(--el-bg-color-page); border: 1px solid var(--el-border-color-lighter); border-radius: 6px; padding: 16px; overflow-x: auto; }
.json-viewer pre { margin: 0; font-family: 'Consolas', 'Courier New', Courier, monospace; font-size: 13px; color: var(--el-text-color-primary); line-height: 1.6; }
</style>