<template>
  <div class="page-wrapper" v-loading="loading">
    <div class="hero-header">
      <div class="header-left">
        <div class="header-icon-ring">
          <el-icon><CopyDocument /></el-icon>
        </div>
        <div>
          <h1 class="page-title">{{ t("templates.title") }}</h1>
          <p class="page-sub">{{ t("templates.subtitle") }}</p>
        </div>
      </div>
    </div>

    <!-- Search / Filter Bar -->
    <div class="toolbar">
      <el-input
        v-model="searchQuery"
        :placeholder="t('templates.searchPlaceholder', 'Search templates...')"
        clearable
        class="search-input"
        id="template-search-input"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
      <el-tag class="count-tag" type="info" effect="plain">
        {{ filteredItems.length }} {{ t('templates.count', 'templates') }}
      </el-tag>
    </div>

    <!-- Empty state -->
    <el-empty
      v-if="filteredItems.length === 0 && !loading"
      :description="searchQuery ? t('templates.noResults', 'No matching templates') : t('templates.noTemplates', 'No templates available')"
      class="gallery-empty"
    />

    <!-- Template Cards Grid -->
    <div class="template-grid" v-if="filteredItems.length > 0">
      <div
        v-for="item in filteredItems"
        :key="item.id"
        class="template-card"
        @click="useTemplate(item)"
        :id="`template-card-${item.id}`"
      >
        <!-- Card accent ribbon -->
        <div class="card-ribbon" />

        <div class="card-body">
          <!-- Icon -->
          <div class="card-icon-wrap">
            <el-icon class="card-icon-el"><component :is="getIconComponent(item.icon)" /></el-icon>
          </div>

          <!-- Text -->
          <h3 class="card-title">{{ t(`templates.templateNames.${item.title}`, item.title) }}</h3>
          <p class="card-desc">{{ item.description || t('templates.noDescription', 'Standard document template') }}</p>

          <!-- Meta -->
          <div class="card-meta">
            <el-tag size="small" effect="plain" class="meta-tag">
              <el-icon style="margin-right:3px"><User /></el-icon>{{ item.owner_name }}
            </el-tag>
          </div>
        </div>

        <!-- Use CTA -->
        <div class="card-footer">
          <span class="use-btn">
            <el-icon><DocumentAdd /></el-icon>
            {{ t('templates.useTemplate', 'Use Template') }}
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
import api from '@/api/client';
import {
  CopyDocument, Search, User, DocumentAdd,
  Document, Tickets, DataAnalysis, Calendar, Money, EditPen,
  Files, Folder, Memo, Postcard, Collection, Briefcase, Management,
  Monitor, PieChart, Stamp, List
} from '@element-plus/icons-vue';
import { ElMessage } from 'element-plus';

const { t } = useI18n();
const router = useRouter();
const loading = ref(false);
const items = ref<any[]>([]);
const searchQuery = ref('');

const ICON_COMPONENTS: Record<string, any> = {
  Document, Tickets, Files, Folder, Memo, Postcard, Collection,
  Briefcase, Management, DataAnalysis, Monitor, Calendar,
  Money, PieChart, Stamp, List
};

function getIconComponent(name: string) {
  return ICON_COMPONENTS[name] || Document;
}

const filteredItems = computed(() => {
  const q = searchQuery.value.trim().toLowerCase();
  if (!q) return items.value;
  return items.value.filter(i =>
    i.title.toLowerCase().includes(q) ||
    (i.description || '').toLowerCase().includes(q)
  );
});

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get('/templates');
    items.value = data.items;
  } catch (err) {
    ElMessage.error(t('common.failed', 'Failed to load templates'));
  } finally {
    loading.value = false;
  }
}

async function useTemplate(item: any) {
  loading.value = true;
  try {
    const { data } = await api.post(`/templates/${item.id}/create-from`);
    ElMessage.success(t('templates.createdSuccessfully', 'Document created from template'));
    router.push(`/doc/${data.id}`);
  } catch (err) {
    ElMessage.error(t('common.failed', 'Failed to create document'));
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
/* ── Page wrapper ────────────────────────────────────────────── */
.page-wrapper {
  padding: 0 0 40px;
}

/* ── Hero Header ─────────────────────────────────────────────── */
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

/* ── Toolbar ─────────────────────────────────────────────────── */
.toolbar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 24px;
}

.search-input {
  max-width: 320px;
}

.count-tag {
  font-size: 13px;
  border-radius: 20px;
}

/* ── Template Grid ───────────────────────────────────────────── */
.template-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: 20px;
}

/* ── Single Card ─────────────────────────────────────────────── */
.template-card {
  cursor: pointer;
  background: var(--edms-card-bg);
  border: 1px solid rgba(156, 163, 175, 0.12);
  border-radius: 16px;
  box-shadow: var(--edms-shadow);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: transform 0.28s cubic-bezier(0.4,0,0.2,1),
              box-shadow 0.28s cubic-bezier(0.4,0,0.2,1),
              border-color 0.28s ease;
  position: relative;
}

.template-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 16px 36px -8px rgba(0,0,0,0.14), 0 4px 12px rgba(0,0,0,0.06);
  border-color: var(--el-color-primary);
}

.card-ribbon {
  height: 4px;
  background: linear-gradient(90deg, var(--el-color-primary), color-mix(in srgb, var(--el-color-primary) 60%, #7367f0 40%));
}

.card-body {
  padding: 20px 20px 12px;
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.card-icon-wrap {
  width: 60px; height: 60px;
  border-radius: 14px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 28px;
  margin-bottom: 14px;
  transition: background 0.3s, color 0.3s, transform 0.3s;
}

.template-card:hover .card-icon-wrap {
  background: var(--el-color-primary);
  color: #fff;
  transform: scale(1.1) rotate(-3deg);
}

.card-title {
  margin: 0 0 8px;
  font-size: 15px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  line-height: 1.3;
}

.card-desc {
  margin: 0 0 14px;
  font-size: 12.5px;
  color: var(--el-text-color-secondary);
  line-height: 1.55;
  flex: 1;
}

.card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  justify-content: center;
}

.meta-tag {
  border-radius: 20px;
  font-size: 11px;
}

/* ── Card Footer CTA ─────────────────────────────────────────── */
.card-footer {
  padding: 12px 20px;
  border-top: 1px solid rgba(156,163,175,0.1);
  display: flex;
  justify-content: center;
}

.use-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 600;
  color: var(--el-color-primary);
  transition: gap 0.2s ease;
}

.template-card:hover .use-btn {
  gap: 10px;
}

/* ── Empty State ─────────────────────────────────────────────── */
.gallery-empty {
  margin-top: 48px;
}

/* ── Admin theme tints ───────────────────────────────────────── */
html[data-theme='admin'] .card-ribbon {
  background: linear-gradient(90deg, #4f46e5, #818cf8);
}
html[data-theme='manager'] .card-ribbon {
  background: linear-gradient(90deg, #d97706, #f59e0b);
}
</style>
