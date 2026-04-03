<template>
  <div class="page-container">
    <div class="page-header">
      <h2>{{ t("import.title") }}</h2>
      <p class="subtitle">{{ t("import.hint") }}</p>
    </div>

    <el-card shadow="sm" class="import-card">
      <div class="upload-section">
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
          <el-divider>{{ t("import.resultTitle", "导入结果") }}</el-divider>
          
          <el-alert
            v-if="!isError"
            :title="t('import.successTitle', '导入任务已执行完毕')"
            type="success"
            show-icon
            :closable="false"
            class="result-alert"
          />
          <el-alert
            v-else
            :title="t('import.errorTitle', '导入任务执行失败')"
            type="error"
            show-icon
            :closable="false"
            class="result-alert"
          />

          <div class="json-viewer">
            <pre>{{ JSON.stringify(result, null, 2) }}</pre>
          </div>
        </div>
      </transition>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import type { UploadFile } from "element-plus";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage, ElMessageBox } from "element-plus";
import { Upload, UploadFilled, InfoFilled } from "@element-plus/icons-vue"; // 引入图标

const { t } = useI18n();
const file = ref<File | null>(null);
const loading = ref(false);
const result = ref<unknown>(null);
const isError = ref(false); // 跟踪是否为报错信息

function onFile(f: UploadFile) {
  file.value = f.raw || null;
  // 当用户重新选择文件时，清空上次的结果
  result.value = null;
  isError.value = false;
}

async function upload() {
  if (!file.value) return;
  
  // Show confirmation warning before import
  try {
    await ElMessageBox.confirm(
      t('import.warning'),
      t('import.confirmTitle'),
      {
        confirmButtonText: t('import.confirmImport'),
        cancelButtonText: t('inbox.cancel'),
        type: 'warning',
      }
    );
  } catch {
    // User cancelled
    return;
  }
  
  loading.value = true;
  result.value = null;
  isError.value = false;
  
  const fd = new FormData();
  fd.append("file", file.value);
  try {
    const { data } = await api.post("/admin/master-data/import", fd, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
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
</script>

<style scoped>
.page-container {
  padding: 24px 32px;
  max-width: 1000px; /* 导入页面不需要像表格那么宽，稍微窄一点更聚拢 */
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  max-width: 600px;
  line-height: 1.5;
}

.import-card {
  border-radius: 8px;
  border: none;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.upload-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px 0;
}

.upload-area {
  width: 100%;
  max-width: 600px;
}

/* 覆盖 el-upload 的默认提示样式，使其更柔和 */
.el-upload__tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  margin-top: 12px;
  color: var(--el-text-color-secondary);
  font-size: 13px;
}

.action-bar {
  margin-top: 32px;
  width: 100%;
  display: flex;
  justify-content: center;
}

.submit-btn {
  width: 200px;
  border-radius: 6px;
  font-weight: 600;
  letter-spacing: 1px;
}

.result-section {
  margin-top: 24px;
}

.result-alert {
  margin-bottom: 16px;
  border-radius: 6px;
}

.json-viewer {
  background: var(--el-bg-color-page);
  border: 1px solid var(--el-border-color-lighter);
  border-radius: 6px;
  padding: 16px;
  overflow-x: auto;
}

.json-viewer pre {
  margin: 0;
  font-family: 'Consolas', 'Courier New', Courier, monospace;
  font-size: 13px;
  color: var(--el-text-color-primary);
  line-height: 1.6;
}
</style>