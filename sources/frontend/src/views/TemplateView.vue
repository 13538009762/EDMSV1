<template>
  <div class="template-page" v-loading="loading">
    <div class="header">
      <h2>{{ t("templates.title", "Template Gallery") }}</h2>
      <p class="subtitle">{{ t("templates.subtitle", "Start your documentation from a standard template.") }}</p>
    </div>

    <el-empty v-if="items.length === 0 && !loading" :description="t('templates.noTemplates', 'No templates available')" />

    <el-row :gutter="24" class="template-grid">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in items" :key="item.id">
        <el-card shadow="hover" class="template-card" @click="useTemplate(item.id)">
          <div class="card-icon">
            <el-icon><Document /></el-icon>
          </div>
          <div class="card-content">
            <h3 class="template-title">{{ t(`templates.templateNames.${item.title}`, item.title) }}</h3>
            <p class="template-desc">{{ item.description }}</p>
            <div class="template-meta">
              <span>{{ item.owner_name }}</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import api from '@/api/client';
import { Document } from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const { t } = useI18n();
const router = useRouter();
const loading = ref(false);
const items = ref<any[]>([]);

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get('/spaces/templates');
    items.value = data.items;
  } catch (err) {
    ElMessage.error(t("common.failed", "Failed to load templates"));
  } finally {
    loading.value = false;
  }
}

async function useTemplate(id: number) {
  loading.value = true;
  try {
    const { data } = await api.post(`/spaces/templates/${id}/create-from`);
    ElMessage.success(t("templates.createdSuccessfully", "Document created from template"));
    router.push(`/doc/${data.id}`);
  } catch (err) {
    ElMessage.error(t("common.failed", "Failed to create document"));
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.template-page {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}

.header {
  margin-bottom: 32px;
}

.header h2 {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 8px 0 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.template-grid {
  margin-bottom: 24px;
}

.template-card {
  cursor: pointer;
  border-radius: 8px;
  transition: all 0.3s;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.template-card:hover {
  transform: translateY(-4px);
  border-color: var(--el-color-primary-light-5);
}

.template-card :deep(.el-card__body) {
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  height: 100%;
  box-sizing: border-box;
}

.card-icon {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  background-color: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin-bottom: 16px;
}

.template-title {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.template-desc {
  margin: 0 0 16px 0;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  line-height: 1.5;
  flex: 1;
}

.template-meta {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
}
</style>
