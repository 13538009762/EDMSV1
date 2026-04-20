<template>
  <div class="dashboard-page" v-loading="loading">
    <div class="header">
      <div class="header-left">
        <h2>{{ t('dashboard.title', 'Data Dashboard') }}</h2>
        <p class="subtitle">{{ t('dashboard.subtitle', 'Overview of your document management system statistics.') }}</p>
      </div>
      <div class="header-right">
        <el-input
          v-model="widgetSearch"
          :placeholder="t('dashboard.searchCharts')"
          prefix-icon="Search"
          clearable
          style="width: 250px"
        />
      </div>
    </div>

    <el-row :gutter="20" class="kpi-row">
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon total"><el-icon><Document /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('dashboard.totalDocs', 'Total Documents') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs')">{{ totalDocs }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon active"><el-icon><EditPen /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.draft') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'draft')">{{ draftsCount }}</div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="4">
        <el-card shadow="hover" class="kpi-card">
          <div class="kpi-icon warning"><el-icon><Stamp /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.in_approval') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'in_approval')">{{ inApprovalCount }}</div>
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
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'approved')">{{ approvedCount }}</div>
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
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'rejected')">{{ rejectedCount }}</div>
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
            <div class="kpi-value clickable" @click="handleMetricClick('users')">{{ totalUsers }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row">
      <el-col :span="12" v-if="shouldShow('statusDistribution')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.statusDistribution') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('statusDistribution')" />
            </div>
          </template>
          <v-chart class="echart-container" :option="statusDistributionOption" autoresize />
        </el-card>
      </el-col>

      <el-col :span="12" v-if="shouldShow('departmentDist')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.departmentDist', 'Department Distribution') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('departmentDist')" />
            </div>
          </template>
          <v-chart class="echart-container" :option="donutOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;">
      <el-col :span="8" v-if="shouldShow('spaceDistribution')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.spaceDistribution') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('spaceDistribution')" />
            </div>
          </template>
          <v-chart class="echart-container small" :option="spaceOption" autoresize />
        </el-card>
      </el-col>

      <el-col :span="8" v-if="shouldShow('storageBreakdown')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.storageBreakdown') }}</span>
              <small>{{ storageInfo.total_size_mb }} MB</small>
            </div>
          </template>
          <v-chart class="echart-container small" :option="storageOption" autoresize />
        </el-card>
      </el-col>

      <el-col :span="8" v-if="shouldShow('myWorkflow')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.myWorkflow') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('myWorkflow')" />
            </div>
          </template>
          <div class="my-workflow-stats">
            <div class="stat-item">
              <div class="label">{{ t('dashboard.myDocs') }}</div>
              <div class="val">{{ myStats.docs }}</div>
            </div>
            <div class="stat-item highlight">
              <div class="label">{{ t('dashboard.myPending') }}</div>
              <div class="val">{{ myStats.pending }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- Row for Insights: Full width for users, Split for Admins -->
    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;">
      <el-col :span="isAdmin ? 12 : 24" v-if="shouldShow('trendingDocs')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.trendingDocs', 'Trending Documents (Top 5)') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('trendingDocs')" />
            </div>
          </template>
          <div class="trending-list" :class="{ 'is-wide': !isAdmin }">
            <div v-for="(doc, i) in trendingDocs" :key="doc.id" class="trending-item">
              <div class="rank">{{ i + 1 }}</div>
              <div class="info">
                <el-link class="title" @click="$router.push(`/doc/${doc.id}`)">{{ doc.title }}</el-link>
                <div class="hits">{{ doc.hits }} {{ t('dashboard.hits', 'views') }}</div>
              </div>
              <el-progress 
                :percentage="calculatePercentage(doc.hits)" 
                :show-text="false" 
                :stroke-width="6"
                :style="{ width: isAdmin ? '80px' : '200px' }"
              />
            </div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="12" v-if="isAdmin && shouldShow('activityHeatmap')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.activityHeatmap', 'User Activity Heatmap') }}</span>
            </div>
          </template>
          <v-chart class="echart-container" :option="heatmapOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;">
      <el-col :span="24" v-if="shouldShow('activityTrend')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.activityTrend30', 'Activity Trend (Last 30 Days)') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('activityTrend')" />
            </div>
          </template>
          <v-chart class="echart-container" :option="lineOption" autoresize />
        </el-card>
      </el-col>
    </el-row>

    <!-- Zoom Dialog -->
    <el-dialog
      v-model="zoomVisible"
      :title="zoomedWidgetTitle"
      width="80%"
      destroy-on-close
      class="zoom-dialog"
    >
      <div style="height: 60vh;">
        <v-chart v-if="zoomedType === 'chart'" :option="zoomedOption" autoresize />
        <div v-else-if="zoomedType === 'list'" class="timeline-container">
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in activities"
                :key="index"
                :timestamp="formatLocalDate(activity.updated_at)"
                :type="activity.status === 'approved' ? 'success' : (activity.status === 'rejected' ? 'danger' : 'primary')"
              >
                <strong>{{ activity.owner_name }}</strong> {{ t('dashboard.updatedDoc') }} "<strong><el-link @click="$router.push(`/doc/${activity.id}`)">{{ activity.title }}</el-link></strong>"
                <el-tag size="small" style="margin-left: 8px;" :type="statusTagType(activity.status)">{{ activity.status }}</el-tag>
              </el-timeline-item>
            </el-timeline>
        </div>
      </div>
    </el-dialog>

    <!-- Metric Detail Dialog -->
    <el-dialog
      v-model="metricVisible"
      :title="metricTitle"
      width="800px"
      destroy-on-close
    >
      <div v-loading="metricLoading" style="min-height: 300px">
        <el-table v-if="metricType === 'docs'" :data="metricData" stripe style="width: 100%" max-height="500">
          <el-table-column prop="doc_number" :label="t('library.colId')" width="140" />
          <el-table-column prop="title" :label="t('library.colTitle')" min-width="180">
            <template #default="{ row }">
               <el-link @click="$router.push(`/editor/${row.id}`)">{{ row.title }}</el-link>
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="t('library.colStatus')" width="120">
            <template #default="{ row }">
              <el-tag size="small" :type="statusTagType(row.status)">{{ t('common.status.' + row.status) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="owner_name" :label="t('library.colOwner')" min-width="120" />
          <el-table-column prop="updated_at" :label="t('library.colUpdatedAt')" width="160">
            <template #default="{ row }">
              {{ formatLocalDate(row.updated_at) }}
            </template>
          </el-table-column>
        </el-table>

        <el-table v-else-if="metricType === 'users'" :data="metricData" stripe style="width: 100%" max-height="500">
          <el-table-column prop="employee_no" :label="t('profile.employeeNo')" width="120" />
          <el-table-column prop="display_name" :label="t('common.name')" min-width="120" />
          <el-table-column prop="login_name" :label="t('profile.loginName')" width="120" />
          <el-table-column prop="department_name" :label="t('profile.dept')" min-width="150">
            <template #default="{ row }">
              {{ t('dept.' + row.department_name, row.department_name) }}
            </template>
          </el-table-column>
          <el-table-column prop="is_manager" :label="t('profile.mgr')" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.is_manager" type="success" size="small">{{ t('common.yes', 'Yes') }}</el-tag>
              <el-tag v-else type="info" size="small">{{ t('common.no', 'No') }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-dialog>

    <el-row class="feed-row" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.recentActivity', 'Recent Document Activity') }}</span>
            </div>
          </template>
          <div class="timeline-container">
            <el-timeline>
              <el-timeline-item
                v-for="(activity, index) in activities"
                :key="index"
                :timestamp="formatLocalDate(activity.updated_at)"
                :type="activity.status === 'approved' ? 'success' : (activity.status === 'rejected' ? 'danger' : 'primary')"
              >
                <strong>{{ activity.owner_name }}</strong> {{ t('dashboard.updatedDoc') }} "<strong><el-link @click="$router.push(`/doc/${activity.id}`)">{{ activity.title }}</el-link></strong>"
                <el-tag size="small" style="margin-left: 8px;" :type="statusTagType(activity.status)">{{ activity.status }}</el-tag>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { Document, EditPen, Stamp, User, CircleCheck, CircleClose, Search, FullScreen, Folder } from "@element-plus/icons-vue";
import { formatLocalDate } from "@/utils/date";
import { useAuthStore } from "@/stores/auth";

// ECharts imports
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { PieChart, LineChart, HeatmapChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  CalendarComponent,
} from "echarts/components";
import VChart from "vue-echarts";

// Register ECharts core components manually
use([
  CanvasRenderer,
  PieChart,
  LineChart,
  HeatmapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  VisualMapComponent,
  CalendarComponent,
]);

const { t } = useI18n();

const loading = ref(true);
const totalDocs = ref(0);
const totalUsers = ref(0);
const statusData = ref<{ status: string; count: number }[]>([]);
const deptData = ref<{ name: string; count: number }[]>([]);
const spaceData = ref<{ name: string; count: number }[]>([]);
const trendData = ref<{ date: string; docs: number; approvals: number }[]>([]);
const activities = ref<any[]>([]);
const trendingDocs = ref<any[]>([]);
const storageInfo = ref({ total_size_mb: 0, by_type: [] });
const heatmapData = ref<any[]>([]);
const myStats = ref({ docs: 0, pending: 0 });

const authStore = useAuthStore();
const isAdmin = computed(() => authStore.user?.is_manager);

const widgetSearch = ref("");
const zoomVisible = ref(false);
const zoomedWidget = ref("");

const metricVisible = ref(false);
const metricLoading = ref(false);
const metricType = ref("");
const metricTitle = ref("");
const metricData = ref<any[]>([]);

async function handleMetricClick(type: string, status?: string) {
  if (!isAdmin.value) return;
  
  metricType.value = type;
  metricVisible.value = true;
  metricLoading.value = true;
  metricData.value = [];
  
  if (status) {
    metricTitle.value = t('common.status.' + status);
  } else if (type === 'docs') {
    metricTitle.value = t('dashboard.totalDocs');
  } else if (type === 'users') {
    metricTitle.value = t('dashboard.totalUsers');
  }

  try {
    if (type === 'docs') {
      const params: any = { scope: 'all' };
      if (status) params.status = status;
      const { data } = await api.get("/documents", { params });
      metricData.value = data.items;
    } else if (type === 'users') {
      const { data } = await api.get("/users", { params: { pageSize: 1000 } });
      metricData.value = data.items;
    }
  } catch (err) {
    console.error(err);
  } finally {
    metricLoading.value = false;
  }
}

function shouldShow(key: string) {
  if (!widgetSearch.value) return true;
  const label = t(`dashboard.${key}`).toLowerCase();
  return label.includes(widgetSearch.value.toLowerCase());
}

function zoomWidget(key: string) {
  zoomedWidget.value = key;
  zoomVisible.value = true;
}

const zoomedType = computed(() => {
    if (zoomedWidget.value === 'recentActivity') return 'list';
    if (zoomedWidget.value === 'myWorkflow') return 'none';
    return 'chart';
});

const zoomedWidgetTitle = computed(() => {
    if (!zoomedWidget.value) return '';
    return t(`dashboard.${zoomedWidget.value}`);
});

const zoomedOption = computed(() => {
    if (zoomedWidget.value === 'departmentDist') return donutOption.value;
    if (zoomedWidget.value === 'spaceDistribution') return spaceOption.value;
    if (zoomedWidget.value === 'activityTrend') return lineOption.value;
    if (zoomedWidget.value === 'statusDistribution') return statusDistributionOption.value;
    return {};
});

const statusDistributionOption = computed(() => {
  const colorMap = {
      'draft': '#909399',
      'in_approval': '#E6A23C',
      'approved': '#67C23A',
      'rejected': '#F56C6C'
  };
  return {
    tooltip: { trigger: "item", confine: true },
    legend: { bottom: "0%", left: "center", textStyle: { fontSize: 11 } },
    series: [
      {
        name: t('dashboard.statusDistribution'),
        type: "pie",
        radius: ["35%", "60%"],
        center: ["50%", "45%"],
        avoidLabelOverlap: true,
        data: statusData.value.map((s) => ({
          value: s.count,
          name: t(`common.status.${s.status}`),
          itemStyle: { color: colorMap[s.status as keyof typeof colorMap] }
        })),
        itemStyle: { borderRadius: 6 }
      },
    ],
  };
});



const draftsCount = computed(() => statusData.value.find((s) => s.status === "draft")?.count || 0);
const approvedCount = computed(() => statusData.value.find((s) => s.status === "approved")?.count || 0);
const rejectedCount = computed(() => statusData.value.find((s) => s.status === "rejected")?.count || 0);
const inApprovalCount = computed(() => statusData.value.find((s) => s.status === "in_approval")?.count || 0);

function statusTagType(status: string) {
  if (status === 'approved') return 'success';
  if (status === 'rejected') return 'danger';
  if (status === 'in_approval') return 'warning';
  return 'info';
}

const donutOption = computed(() => {
  return {
    tooltip: { trigger: "item", confine: true },
    legend: { bottom: "5%", left: "center" },
    series: [
      {
        name: t('dashboard.documents'),
        type: "pie",
        radius: ["35%", "60%"],
        center: ["50%", "45%"],
        avoidLabelOverlap: true,
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
            formatter: '{b}\n{c} ({d}%)'
          },
        },
        labelLine: { show: false },
        data: deptData.value.map((s) => ({
          value: s.count,
          name: t('dept.' + (s.name || ''), s.name || t('common.unknown')),
        })),
      },
    ],
  };
});

const lineOption = computed(() => {
  return {
    legend: { data: [t('dashboard.updatedDoc'), t('dashboard.completedApprovals')] },
    tooltip: { trigger: 'axis', confine: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: trendData.value.map((t) => {
        const d = new Date(t.date);
        return `${d.getMonth() + 1}/${d.getDate()}`;
      }).reverse(),
    },
    yAxis: [
      { type: "value", name: t('dashboard.documents') },
      { type: "value", name: t('dashboard.approvals') }
    ],
    series: [
      {
        name: t('dashboard.updatedDoc'),
        type: "line",
        areaStyle: { color: "rgba(64, 158, 255, 0.2)" },
        itemStyle: { color: "#409eff" },
        smooth: true,
        data: trendData.value.map((t) => t.docs).reverse(),
      },
      {
        name: t('dashboard.completedApprovals'),
        type: "line",
        yAxisIndex: 1,
        itemStyle: { color: "#67C23A" },
        smooth: true,
        data: trendData.value.map((t) => t.approvals).reverse(),
      },
    ],
  };
});

const spaceOption = computed(() => {
  return {
    tooltip: { trigger: "item", confine: true },
    legend: { bottom: "0%", left: "center", textStyle: { fontSize: 11 } },
    series: [
      {
        name: t('dashboard.spaceDistribution'),
        type: "pie",
        radius: "60%",
        center: ["50%", "45%"],
        avoidLabelOverlap: true,
        data: spaceData.value.map((s) => ({
          value: s.count,
          name: s.name || 'Unassigned',
        })),
        itemStyle: {
            borderRadius: 6,
        }
      },
    ],
  };
});

const storageOption = computed(() => {
    return {
        tooltip: { trigger: 'item', formatter: '{b}: {c} MB ({d}%)' },
        series: [{
            type: 'pie',
            radius: ['40%', '70%'],
            avoidLabelOverlap: false,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: '14', fontWeight: 'bold' } },
            data: storageInfo.value.by_type
        }]
    };
});

const heatmapOption = computed(() => {
    const today = new Date();
    const year = today.getFullYear();
    return {
        tooltip: { position: 'top' },
        visualMap: {
            min: 0,
            max: 10,
            type: 'piecewise',
            orient: 'horizontal',
            left: 'center',
            top: 0,
            textStyle: { fontSize: 10 },
            inRange: { color: ['#ebedf0', '#9be9a8', '#40c463', '#30a14e', '#216e39'] }
        },
        calendar: {
            top: 40,
            left: 30,
            right: 10,
            cellSize: ['auto', 13],
            range: [new Date(today.getTime() - 90 * 24 * 3600 * 1000), today],
            itemStyle: { borderWidth: 0.5 },
            yearLabel: { show: false },
            dayLabel: { fontSize: 10 },
            monthLabel: { fontSize: 10 }
        },
        series: {
            type: 'heatmap',
            coordinateSystem: 'calendar',
            data: heatmapData.value
        }
    };
});

function calculatePercentage(hits: number) {
    const max = trendingDocs.value.length > 0 ? trendingDocs.value[0].hits : 1;
    return Math.round((hits / max) * 100);
}

async function loadData() {
  loading.value = true;
  try {
    const { data } = await api.get("/dashboard/stats");
    totalDocs.value = data.total_docs;
    totalUsers.value = data.total_users;
    statusData.value = data.status_data;
    deptData.value = data.dept_data || [];
    spaceData.value = data.space_data || [];
    myStats.value = data.my_stats || { docs: 0, pending: 0 };
    trendData.value = data.trend_data || [];
    activities.value = data.activities || [];
    trendingDocs.value = data.trending_docs || [];
    storageInfo.value = data.storage_info || { total_size_mb: 0, by_type: [] };
    heatmapData.value = data.heatmap_data || [];
    console.log("[DEBUG] Loaded data extensions:", data);
  } catch (err) {
    console.error("[DEBUG] Dashboard API Error:", err);
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
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.header h2 {
  margin: 0;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.subtitle {
  margin: 4px 0 0 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.kpi-row {
  margin-bottom: 24px;
}

.kpi-card {
  height: 100px;
  border-radius: 8px;
  display: flex;
}

.kpi-card :deep(.el-card__body) {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 16px;
}

.kpi-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28px;
  margin-right: 16px;
}

.kpi-icon.total {
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
}
.kpi-icon.active {
  background: var(--el-bg-color-page);
  color: var(--el-text-color-regular);
}
.kpi-icon.warning {
  background: var(--el-color-warning-light-9);
  color: var(--el-color-warning);
}

.kpi-info {
  display: flex;
  flex-direction: column;
}

.kpi-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-bottom: 4px;
}

.kpi-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.kpi-value.clickable {
  cursor: pointer;
  transition: color 0.3s;
}
.kpi-value.clickable:hover {
  color: var(--el-color-primary);
  text-decoration: underline;
}

.chart-row {
  margin-bottom: 24px;
}

.chart-card {
  border-radius: 8px;
}

.card-header {
  font-weight: 600;
  color: var(--el-text-color-regular);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.my-workflow-stats {
    display: flex;
    justify-content: space-around;
    padding: 20px 0;
    height: 100%;
    align-items: center;
}
.stat-item {
    text-align: center;
}
.stat-item .label {
    font-size: 14px;
    color: var(--el-text-color-secondary);
    margin-bottom: 10px;
}
.stat-item .val {
    font-size: 32px;
    font-weight: bold;
}
.stat-item.highlight .val {
    color: var(--el-color-warning);
}

.echart-container {
  width: 100%;
  height: 350px;
}
.echart-container.small {
  height: 250px;
}
.timeline-container {
  height: 400px;
  overflow-y: auto;
  padding-right: 20px;
}

.trending-list {
  height: 250px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px 0;
}
.trending-item {
  display: flex;
  align-items: center;
  gap: 12px;
}
.trending-item .rank {
  width: 24px;
  height: 24px;
  background: var(--el-color-primary-light-9);
  color: var(--el-color-primary);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 12px;
}
.trending-item .info {
  flex: 1;
  min-width: 0;
}
.trending-item .title {
  display: block;
  font-size: 14px;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.trending-item .hits {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.trending-list.is-wide {
    height: auto;
    padding: 10px 0;
}
.trending-list.is-wide .trending-item {
    padding: 12px 0;
    border-bottom: 1px solid var(--el-border-color-lighter);
}
.trending-list.is-wide .trending-item:last-child {
    border-bottom: none;
}
</style>
