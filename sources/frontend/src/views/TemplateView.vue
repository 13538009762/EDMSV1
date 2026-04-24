<template>
  <div class="page-wrapper" v-loading="loading">
    <div class="card-header">
      <div style="text-align: center;">
        <h2>{{ t("templates.title", "Template Gallery") }}</h2>
        <p class="subtitle" style="margin: 8px 0 0; font-size: 1rem; color: var(--el-text-color-secondary)">{{ t("templates.subtitle", "Start your documentation from a standard template.") }}</p>
      </div>
    </div>

    <el-empty v-if="items.length === 0 && !loading" :description="t('templates.noTemplates', 'No templates available')" />

    <el-row :gutter="24" class="template-grid">
      <el-col :xs="24" :sm="12" :md="8" :lg="6" v-for="item in items" :key="item.id">
        <div class="template-card" @click="useTemplate(item.id)">
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
        </div>
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
.template-grid {
  margin-top: 24px;
}

.template-card {
  cursor: pointer;
  background-color: var(--edms-card-bg);
  border: 1px solid rgba(156, 163, 175, 0.15);
  border-radius: 12px;
  box-shadow: var(--edms-shadow);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  height: 100%;
  box-sizing: border-box;
}

.template-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.12);
  border-color: var(--el-color-primary); 
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
  transition: all 0.3s ease;
}

.template-card:hover .card-icon {
  transform: scale(1.1);
  background-color: var(--el-color-primary);
  color: #fff;
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

/* 适配不同角色的图标背景 */
html[data-theme='manager'] .card-icon {
  background-color: rgba(217, 119, 6, 0.1);
}
html[data-theme='admin'] .card-icon {
  background-color: rgba(79, 70, 229, 0.1);
}
</style>
