<template>
  <div class="dashboard-page" v-loading="loading">
    <div class="header">
      <h2>{{ t('dashboard.title', 'Data Dashboard') }}</h2>
      <p class="subtitle">{{ t('dashboard.subtitle', 'Overview of your document management system statistics.') }}</p>
    </div>

    <el-row :gutter="20" class="kpi-row">
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon total"><el-icon><Document /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('dashboard.totalDocs', 'Total Documents') }}</div>
            <div class="kpi-value">{{ totalDocs }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon active"><el-icon><EditPen /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.draft') }}</div>
            <div class="kpi-value">{{ draftsCount }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon warning"><el-icon><Stamp /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.in_approval') }}</div>
            <div class="kpi-value">{{ inApprovalCount }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon success" style="background: var(--el-color-success-light-9); color: var(--el-color-success);">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.approved') }}</div>
            <div class="kpi-value">{{ approvedCount }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon danger" style="background: var(--el-color-danger-light-9); color: var(--el-color-danger);">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.rejected') }}</div>
            <div class="kpi-value">{{ rejectedCount }}</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon info" style="background: var(--el-color-info-light-9); color: var(--el-color-info);">
            <el-icon><User /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('dashboard.totalUsers', 'Total Users') }}</div>
            <div class="kpi-value">{{ totalUsers }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.statusDistribution', 'Document Status Distribution') }}</span>
            </div>
          </template>
          <v-chart class="echart-container" :option="pieOption" autoresize />
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.activityTrend', 'Activity Trend (Last 7 Days)') }}</span>
            </div>
          </template>
          <v-chart class="echart-container" :option="lineOption" autoresize />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { Document, EditPen, Stamp, User, CircleCheck, CircleClose } from "@element-plus/icons-vue";
// ECharts imports
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart, LineChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from "echarts/components";
import VChart from "vue-echarts";

// Register ECharts core components manually
use([
  CanvasRenderer,
  PieChart,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
]);

const { t } = useI18n();

const loading = ref(true);
const totalDocs = ref(0);
const totalUsers = ref(0);
const statusData = ref<{ status: string; count: number }[]>([]);
const trendData = ref<{ date: string; count: number }[]>([]);

const draftsCount = computed(() => {
  return statusData.value.find((s) => s.status === "draft")?.count || 0;
});
const approvedCount = computed(() => {
  return statusData.value.find((s) => s.status === "approved")?.count || 0;
});

const rejectedCount = computed(() => {
  return statusData.value.find((s) => s.status === "rejected")?.count || 0;
});

const inApprovalCount = computed(() => {
  return statusData.value.find((s) => s.status === "in_approval")?.count || 0;
});

const statusColorMap: Record<string, string> = {
  draft: "#909399",
  in_approval: "#E6A23C",
  approved: "#67C23A",
  rejected: "#F56C6C",
};

const statusLabelMap = computed(() => ({
  draft: t('common.status.draft'),
  in_approval: t('common.status.in_approval'),
  approved: t('common.status.approved'),
  rejected: t('common.status.rejected'),
}));

const pieOption = computed(() => {
  return {
    tooltip: { trigger: "item" },
    legend: { top: "5%", left: "center" },
    series: [
      {
        name: t('dashboard.documents'),
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: { show: false, position: "center" },
        emphasis: {
          label: {
            show: true,
            fontSize: 20,
            fontWeight: "bold",
          },
        },
        labelLine: { show: false },
        data: statusData.value.map((s) => ({
          value: s.count,
          name: (statusLabelMap.value as any)[s.status] || s.status,
          itemStyle: { color: statusColorMap[s.status] || "#ccc" },
        })),
      },
    ],
  };
});

const lineOption = computed(() => {
  return {
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: trendData.value.map((t) => {
        const d = new Date(t.date);
        return `${d.getMonth() + 1}/${d.getDate()}`;
      }),
    },
    yAxis: { type: "value" },
    series: [
      {
        name: t('dashboard.updatedDocs'),
        type: "line",
        areaStyle: { color: "rgba(64, 158, 255, 0.2)" },
        itemStyle: { color: "#409eff" },
        smooth: true,
        data: trendData.value.map((t) => t.count),
      },
    ],
  };
});

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get("/dashboard/stats");
    totalDocs.value = data.total_docs;
    totalUsers.value = data.total_users;
    statusData.value = data.status_data;
    trendData.value = data.trend_data;
  } catch (err) {
    console.error("Dashboard error", err);
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  loadData();
});
</script>

<style scoped>
.dashboard-page {
  padding: 24px;
  background-color: var(--el-bg-color-page);
  min-height: calc(100vh - 60px);
}
.header {
  margin-bottom: 24px;
}
.header h2 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.subtitle {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}
.kpi-row {
  margin-bottom: 24px;
}
.kpi-card {
  display: flex;
  align-items: center;
  border: none;
  border-radius: 12px;
}
.kpi-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 20px;
}
.kpi-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 16px;
}
.kpi-icon.total { background: var(--el-color-primary-light-9); color: var(--el-color-primary); }
.kpi-icon.active { background: var(--el-color-info-light-9); color: var(--el-color-info); }
.kpi-icon.warning { background: var(--el-color-warning-light-9); color: var(--el-color-warning); }
.kpi-icon.success { background: var(--el-color-success-light-9); color: var(--el-color-success); }
.kpi-info {
  display: flex;
  flex-direction: column;
}
.kpi-label {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
}
.kpi-value {
  font-size: 28px;
  font-weight: bold;
  color: var(--el-text-color-primary);
  line-height: 1;
}
.chart-card {
  border: none;
  border-radius: 12px;
}
.card-header {
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.echart-container {
  height: 350px;
  width: 100%;
}
</style>
