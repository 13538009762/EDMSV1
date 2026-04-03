<template>
  <div class="admin">
    <div class="top">
      <LocaleSwitcher />
    </div>
    <el-card class="card">
      <template #header>
        <span>{{ t("admin.title") }}</span>
      </template>
      <p class="intro">{{ t("admin.intro") }}</p>
      <el-alert
        v-if="status"
        :title="status.has_users ? t('admin.hasUsersHint') : t('admin.bootstrapHint')"
        type="info"
        show-icon
        :closable="false"
        class="alert"
      >
        <div v-if="status.has_users && status.sample_managers?.length" style="margin-top: 8px">
          <span>{{ t('admin.tryLogin') }}</span>
          <el-tag
            v-for="m in status.sample_managers"
            :key="m"
            size="small"
            class="tag-small"
            @click="copyLogin(m)"
          >{{ m }}</el-tag>
        </div>
      </el-alert>

      <el-form label-position="top" class="form">
        <el-form-item :label="t('admin.selectFile')">
          <el-upload
            :auto-upload="false"
            :on-change="onFile"
            :limit="1"
            accept=".xlsx,.xlsm"
          >
            <el-button>{{ t("admin.selectFile") }}</el-button>
          </el-upload>
        </el-form-item>
        <el-button
          type="primary"
          :loading="loading"
          :disabled="!file"
          @click="doImport"
          >{{ t("admin.upload") }}</el-button
        >
        <el-button style="margin-left: 8px" @click="goLogin">{{ t("admin.goLogin") }}</el-button>
      </el-form>

      <div v-if="sampleLogins.length" class="samples">
        <h4>{{ t("admin.sampleLogins") }}</h4>
        <el-tag v-for="n in sampleLogins" :key="n" class="tag" @click="copyLogin(n)">{{ n }}</el-tag>
      </div>

      <div v-if="resultJson" class="result">
        <h4>{{ t("admin.resultTitle") }}</h4>
        <pre>{{ resultJson }}</pre>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { useI18n } from "vue-i18n";
import type { UploadFile } from "element-plus";
import { ElMessage } from "element-plus";
import axios from "axios";
import LocaleSwitcher from "@/components/LocaleSwitcher.vue";
import { ArrowDown, Plus, Upload, Edit, Lock, Unlock } from "@element-plus/icons-vue";
const { t } = useI18n();
const router = useRouter();

const status = ref<{ has_users: boolean; sample_managers?: string[] } | null>(null);

const file = ref<File | null>(null);
const loading = ref(false);
const resultJson = ref("");
const sampleLogins = ref<string[]>([]);

const base = import.meta.env.VITE_API_BASE || "/api";

function authHeaders(): Record<string, string> {
  const h: Record<string, string> = {};
  const tok = localStorage.getItem("edms_token");
  if (tok) h.Authorization = `Bearer ${tok}`;
  return h;
}

async function loadStatus() {
  const { data } = await axios.get(`${base}/admin/status`);
  status.value = data;
}

function onFile(f: UploadFile) {
  file.value = f.raw || null;
}

async function doImport() {
  if (!file.value) return;
  loading.value = true;
  resultJson.value = "";
  sampleLogins.value = [];
  const fd = new FormData();
  fd.append("file", file.value);
  try {
    const { data } = await axios.post(`${base}/admin/master-data/import`, fd, {
      headers: authHeaders(),
    });
    resultJson.value = JSON.stringify(data, null, 2);
    sampleLogins.value = data.sample_login_names || [];
    ElMessage.success(t("admin.importOk"));
    await loadStatus();
  } catch (err: unknown) {
    let msg = String(err);
    if (axios.isAxiosError(err) && err.response) {
      msg = err.response.data?.error || `Server error (${err.response.status}): ${err.response.statusText}`;
    }
    resultJson.value = msg;
    ElMessage.error(msg);

  } finally {
    loading.value = false;
  }
}

function goLogin() {
  router.push({ name: "login" });
}

function copyLogin(name: string) {
  void navigator.clipboard.writeText(name);
  ElMessage.success(name);
}
const roleTagMap: Record<string, string> = {
  'Administrator': 'danger', // 管理员显示为红色
  'User': 'info',            // 普通用户显示为灰色
};
onMounted(async () => {
  try {
    await loadStatus();
  } catch {
    status.value = { has_users: true };
  }
});
</script>

<style scoped>
.admin {
  min-height: 100%;
  padding: 24px;
  background: var(--el-fill-color-light);
  box-sizing: border-box;
}
.top {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.card {
  max-width: 720px;
  margin: 0 auto;
}
.intro {
  color: var(--el-text-color-regular);
  line-height: 1.5;
  white-space: pre-line;
}
.alert {
  margin: 16px 0;
}
.form {
  margin-top: 16px;
}
.samples {
  margin-top: 24px;
}
.tag {
  margin: 4px;
  cursor: pointer;
}
.result {
  margin-top: 24px;
}
.result pre {
  background: var(--el-fill-color);
  padding: 12px;
  overflow: auto;
  font-size: 12px;
}
</style>
