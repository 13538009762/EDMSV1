<template>
  <div class="page-wrapper" v-loading="loading">
    <div class="card-header">
       <div>
         <h2>{{ t('dashboard.title', 'Data Dashboard') }}</h2>
         <p class="subtitle">{{ t('dashboard.subtitle', 'Overview of your document management system statistics.') }}</p>
       </div>
       <el-input
          v-model="widgetSearch"
          :placeholder="t('dashboard.searchCharts')"
          :prefix-icon="Search"
          clearable
          style="width: 250px"
        />
    </div>
 
    <!-- 🔗 区块链核心安全监控 -->
    <div v-if="!loading" class="blockchain-section">
      <div class="section-title cyber">
        <el-icon><Connection /></el-icon> {{ t('dashboard.blockchainTitle') }}
      </div>
      <el-row :gutter="20" class="blockchain-kpi-row">
        <el-col :xs="24" :sm="12" :md="8">
          <el-card shadow="hover" class="kpi-card blockchain cyber-blue">
            <div class="kpi-icon blue"><el-icon><Cpu /></el-icon></div>
            <div class="kpi-info">
              <div class="kpi-label">{{ t('dashboard.notarizedDocs') }}</div>
              <div class="kpi-value glow clickable" @click="handleMetricClick('blockchain_docs')">{{ blockchainStats.on_chain_count }}</div>
            </div>
            <div class="blockchain-status-tag">REAL-TIME</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card shadow="hover" class="kpi-card blockchain cyber-red">
            <div class="kpi-icon orange"><el-icon><Lock /></el-icon></div>
            <div class="kpi-info">
              <div class="kpi-label">{{ t('dashboard.tamperAlerts') }}</div>
              <div class="kpi-value glow-red clickable" @click="handleMetricClick('tamper_alerts')">{{ blockchainStats.tamper_alerts }}</div>
            </div>
            <div class="blockchain-status-tag danger">GUARDED</div>
          </el-card>
        </el-col>
        <el-col :xs="24" :sm="12" :md="8">
          <el-card shadow="hover" class="kpi-card blockchain cyber-green">
            <div class="kpi-icon green"><el-icon><Box /></el-icon></div>
            <div class="kpi-info">
              <div class="kpi-label">{{ t('dashboard.blockHeight') }}</div>
              <div class="kpi-value">{{ blockchainStats.block_height }}</div>
            </div>
            <div class="blockchain-status-tag success">STABLE</div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div class="section-title">
      <el-icon><DataLine /></el-icon> {{ t('dashboard.businessStats') }}
    </div>

    <el-row :gutter="16" class="kpi-row">
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-blue-soft">
          <div class="kpi-icon total"><el-icon><Document /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('dashboard.totalDocs') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs')">{{ totalDocs }}</div>
          </div>
          <div class="blockchain-status-tag">GLOBAL</div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-grey">
          <div class="kpi-icon active"><el-icon><EditPen /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.draft') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'draft')">{{ draftsCount }}</div>
          </div>
          <div class="blockchain-status-tag info">DRAFTING</div>
        </el-card>
      </el-col>
      
      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-orange">
          <div class="kpi-icon warning"><el-icon><Stamp /></el-icon></div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.in_approval') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'in_approval')">{{ inApprovalCount }}</div>
          </div>
          <div class="blockchain-status-tag warning">WAITING</div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-green-soft">
          <div class="kpi-icon success">
            <el-icon><CircleCheck /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.approved') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'approved')">{{ approvedCount }}</div>
          </div>
          <div class="blockchain-status-tag success">FINALIZED</div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-red-soft">
          <div class="kpi-icon danger">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('common.status.rejected') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('docs', 'rejected')">{{ rejectedCount }}</div>
          </div>
          <div class="blockchain-status-tag danger">RECALLED</div>
        </el-card>
      </el-col>

      <el-col :xs="12" :sm="8" :md="4">
        <el-card shadow="hover" class="kpi-card blockchain cyber-indigo">
          <div class="kpi-icon info">
            <el-icon><User /></el-icon>
          </div>
          <div class="kpi-info">
            <div class="kpi-label">{{ t('dashboard.totalUsers') }}</div>
            <div class="kpi-value clickable" @click="handleMetricClick('users')">{{ totalUsers }}</div>
          </div>
          <div class="blockchain-status-tag info">NETWORK</div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row" v-if="!loading">
      <el-col :xs="24" :md="12" v-if="shouldShow('statusDistribution')">
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

      <el-col :xs="24" :md="12" v-if="shouldShow('departmentDist')">
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

    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;" v-if="!loading">
      <el-col :xs="24" :sm="12" :md="8" v-if="shouldShow('spaceDistribution')">
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

      <el-col :xs="24" :sm="12" :md="8" v-if="shouldShow('storageBreakdown')">
        <el-card shadow="hover" class="chart-card">
          <template #header>
            <div class="card-header">
              <span>{{ t('dashboard.storageBreakdown', 'Storage by File Type') }}</span>
              <div class="header-actions">
                  <small style="margin-right: 8px">{{ storageInfo.total_size_mb }} MB</small>
                  <el-button link :icon="FullScreen" @click="zoomWidget('storageBreakdown')" />
              </div>
            </div>
          </template>
          <v-chart class="echart-container small" :option="storageOption" autoresize />
        </el-card>
      </el-col>

      <el-col :xs="24" :sm="12" :md="8" v-if="shouldShow('myWorkflow')">
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
    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;" v-if="!loading">
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
                <el-link class="title" @click="$router.push({ name: 'editor', params: { id: doc.id } })">{{ doc.title }}</el-link>
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
              <span>{{ t('dashboard.activityTrend90', 'Activity Trend (90 Days)') }}</span>
              <el-button link :icon="FullScreen" @click="zoomWidget('activityHeatmap')" />
            </div>
          </template>
          <div class="heatmap-wrapper">
             <v-chart class="echart-container heatmap" :option="heatmapOption" autoresize />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;" v-if="!loading">
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
                <strong>{{ activity.owner_name }}</strong> {{ t('dashboard.updatedDoc') }} "<strong><el-link @click="zoomVisible = false; $router.push(`/doc/${activity.id}`)">{{ activity.title }}</el-link></strong>"
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
        <el-table v-if="metricType === 'docs' || metricType === 'blockchain_docs'" :data="metricData" stripe style="width: 100%" max-height="500">
          <el-table-column prop="doc_number" :label="t('library.colId')" width="140" />
          <el-table-column prop="title" :label="t('library.colTitle')" min-width="180">
            <template #default="{ row }">
               <el-link @click="metricVisible = false; $router.push({ name: 'editor', params: { id: row.id } })">{{ row.title }}</el-link>
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
              {{ formatDeptName(row.department_name, row.department_name_en) }}
            </template>
          </el-table-column>
          <el-table-column prop="is_manager" :label="t('profile.mgr')" width="100">
            <template #default="{ row }">
              <el-tag v-if="row.is_manager" type="success" size="small">{{ t('common.yes', 'Yes') }}</el-tag>
              <el-tag v-else type="info" size="small">{{ t('common.no', 'No') }}</el-tag>
            </template>
          </el-table-column>
        </el-table>
        
        <el-table v-else-if="metricType === 'tamper_alerts'" :data="metricData" stripe style="width: 100%" max-height="500">
          <el-table-column prop="created_at" label="拦截时间" width="180">
            <template #default="{ row }">
              {{ formatLocalDate(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="user_name" label="操作用户" width="120" />
          <el-table-column prop="ip_address" label="来源 IP" width="140" />
          <el-table-column prop="description" label="拦截描述" min-width="200" />
        </el-table>
      </div>
    </el-dialog>
    <el-row :gutter="20" class="chart-row" style="margin-top: 20px;" v-if="!loading">
      <el-col :span="14">
        <el-card shadow="hover" class="chart-card blockchain-card">
          <template #header>
            <div class="card-header cyber">
              <span><el-icon><Link /></el-icon> 实时确权哈希流 (Live Blockchain Feed)</span>
              <el-tag type="success" effect="dark" size="small" class="pulse-tag">CONNECTED</el-tag>
            </div>
          </template>
          <div class="hash-feed-container">
            <div v-for="item in blockchainHistory" :key="item.id" class="hash-item">
               <div class="hash-time">{{ formatLocalDate(item.time) }}</div>
               <div class="hash-content">
                  文档 <strong>"{{ item.title }}"</strong> 已确权固化
               </div>
               <div class="hash-value">交易凭证: <span>{{ item.tx_hash }}</span></div>
            </div>
            <div v-if="blockchainHistory.length === 0" class="empty-state">暂无上链记录</div>
          </div>
        </el-card>
      </el-col>

      <el-col :span="10">
        <el-card shadow="hover" class="chart-card security-card">
          <template #header>
            <div class="card-header danger">
              <span><el-icon><WarnTriangleFilled /></el-icon> 零信任安全雷达 (Security Alerts)</span>
            </div>
          </template>
          <div class="security-radar-container">
            <div v-if="securityAlerts.length > 0" class="alert-list">
              <div v-for="alert in securityAlerts" :key="alert.id" class="alert-item animate__animated animate__headShake">
                <div class="alert-header">
                  <el-tag type="danger" size="small" effect="dark">非法篡改拦截</el-tag>
                  <span class="alert-time">{{ formatLocalDate(alert.time) }}</span>
                </div>
                <div class="alert-body">{{ alert.description }}</div>
                <div class="alert-footer">来源 IP: {{ alert.ip }} | 用户: {{ alert.user }}</div>
              </div>
            </div>
            <div v-else class="secure-state">
               <el-result icon="success" title="系统安全运行中" sub-title="底层物理指纹哈希校验一致"></el-result>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row class="feed-row" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card shadow="hover" class="chart-card">
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
                <strong>{{ activity.owner_name }}</strong> {{ t('dashboard.updatedDoc') }} "<strong><el-link @click="$router.push({ name: 'editor', params: { id: activity.id } })">{{ activity.title }}</el-link></strong>"
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
import { 
  Document, EditPen, Stamp, User, CircleCheck, CircleClose, Search, FullScreen, Folder,
  Link, Lock, Box, Cpu, Connection, WarnTriangleFilled, DataLine
} from "@element-plus/icons-vue";
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
import * as echarts from "echarts";

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

const { t, locale, te } = useI18n();

const loading = ref(true);
const totalDocs = ref(0);
const totalUsers = ref(0);
const statusData = ref<{ status: string; count: number }[]>([]);
const deptData = ref<{ name: string; name_en?: string; count: number }[]>([]);
const spaceData = ref<{ name: string; count: number }[]>([]);
const trendData = ref<{ date: string; docs: number; approvals: number }[]>([]);
const activities = ref<any[]>([]);
const trendingDocs = ref<any[]>([]);
interface StorageItem {
  name: string;
  value: number;
}

const storageInfo = ref<{ total_size_mb: number; by_type: StorageItem[] }>({ total_size_mb: 0, by_type: [] });
const heatmapData = ref<any[]>([]);
const myStats = ref({ docs: 0, pending: 0 });
const blockchainStats = ref({ on_chain_count: 0, tamper_alerts: 0, block_height: 15000 });
const blockchainHistory = ref<any[]>([]);
const securityAlerts = ref<any[]>([]);

const formatDeptName = (name: string, nameEn?: string) => {
  if (!name || name === 'Unknown') return t('common.unknown');
  // Try translating the primary name (usually Chinese)
  if (te(`dept.${name}`)) return t(`dept.${name}`);
  // Try translating the English name if available
  if (nameEn && te(`dept.${nameEn}`)) return t(`dept.${nameEn}`);
  // Fallback to raw values based on current locale
  return locale.value === 'zh-CN' ? name : (nameEn || name);
};

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
  } else if (type === 'blockchain_docs') {
    metricTitle.value = '已上链存证文档明细';
  } else if (type === 'tamper_alerts') {
    metricTitle.value = '零信任安全拦截日志详情';
  }

  try {
    if (type === 'docs' || type === 'blockchain_docs') {
      const params: any = { scope: 'all' };
      if (status) params.status = status;
      if (type === 'blockchain_docs') params.on_chain = 'true';
      const { data } = await api.get("/documents", { params });
      metricData.value = data.items;
    } else if (type === 'users') {
      const { data } = await api.get("/users", { params: { pageSize: 1000 } });
      metricData.value = data.items;
    } else if (type === 'tamper_alerts') {
      const { data } = await api.get("/dashboard/tamper-alerts");
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
    if (zoomedWidget.value === 'storageBreakdown') return storageOption.value;
    if (zoomedWidget.value === 'activityHeatmap') return heatmapOption.value;
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
    backgroundColor: 'transparent',
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
        itemStyle: { borderRadius: 6 },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n{c}',
          overflow: 'break',
          width: 70,
          fontSize: 11
        },
        labelLine: { length: 10, length2: 5 }
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
    backgroundColor: 'transparent',
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
        label: {
          show: true,
          formatter: '{b}\n({d}%)',
          overflow: 'break',
          width: 80,
          fontSize: 11
        },
        labelLine: { length: 15, length2: 10 },
        data: deptData.value.map((s) => ({
          value: s.count,
          name: formatDeptName(s.name, s.name_en),
        })),
      },
    ],
  };
});

const lineOption = computed(() => {
  return {
    backgroundColor: 'transparent',
    legend: { data: [t('dashboard.updatedDoc'), t('dashboard.completedApprovals')] },
    tooltip: { trigger: 'axis', confine: true },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: trendData.value.map((t) => {
        const d = new Date(t.date);
        return `${d.getMonth() + 1}/${d.getDate()}`;
      }),
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
        data: trendData.value.map((t) => t.docs),
      },
      {
        name: t('dashboard.completedApprovals'),
        type: "line",
        yAxisIndex: 1,
        itemStyle: { color: "#67C23A" },
        smooth: true,
        data: trendData.value.map((t) => t.approvals),
      },
    ],
  };
});

const spaceOption = computed(() => {
  return {
    backgroundColor: 'transparent',
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
        },
        label: {
          show: true,
          position: 'outside',
          formatter: '{b}\n({c})',
          overflow: 'break',
          width: 80,
          fontSize: 11
        },
        labelLine: { length: 15, length2: 10 }
      },
    ],
  };
});

const storageOption = computed(() => {
    const hasData = storageInfo.value.by_type.some(i => i.value > 0.001);
    
    // Map backend names to translation keys
    const nameMap: Record<string, string> = {
        "Rich Text (JSON)": t('dashboard.storage.richText'),
        "Real-time States": t('dashboard.storage.realtime'),
        "Binary Assets": t('dashboard.storage.binary'),
        "System Meta": t('dashboard.storage.meta')
    };

    const translatedData = storageInfo.value.by_type.map(item => ({
        ...item,
        name: nameMap[item.name] || item.name
    }));

    return {
        backgroundColor: 'transparent',
        tooltip: { trigger: 'item', formatter: '{b}: {c} MB ({d}%)' },
        legend: { 
            bottom: '0%', 
            left: 'center', 
            textStyle: { fontSize: 10 } 
        },
        color: ['#6366f1', '#a855f7', '#ec4899', '#f43f5e', '#94a3b8'],
        series: [{
            type: 'pie',
            radius: ['35%', '60%'],
            center: ['50%', '45%'],
            minAngle: 15,
            avoidLabelOverlap: true,
            itemStyle: { borderRadius: 10, borderColor: '#fff', borderWidth: 2 },
            label: { show: false },
            emphasis: { label: { show: true, fontSize: '14', fontWeight: 'bold' } },
            data: hasData ? translatedData : [
                { name: t('dashboard.storage.ready'), value: 1, itemStyle: { color: '#f1f5f9' } }
            ]
        }]
    };
});

const heatmapOption = computed(() => {
  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'line',
        lineStyle: {
          color: 'rgba(16, 185, 129, 0.5)',
          width: 2,
          type: 'dashed'
        }
      },
      backgroundColor: 'rgba(255, 255, 255, 0.9)',
      borderColor: 'rgba(16, 185, 129, 0.2)',
      textStyle: { color: '#334155' }
    },
    grid: {
      left: '2%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: heatmapData.value.map(item => {
        const d = new Date(item[0]);
        return `${d.getMonth() + 1}/${d.getDate()}`;
      }),
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: '#94a3b8',
        margin: 16
      }
    },
    yAxis: {
      type: 'value',
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: { color: '#94a3b8' },
      splitLine: {
        lineStyle: {
          type: 'dashed',
          color: 'rgba(148, 163, 184, 0.15)'
        }
      }
    },
    series: [
      {
        name: t('dashboard.activityUnit', 'activities'),
        type: 'line',
        smooth: true,
        showSymbol: false,
        lineStyle: {
          width: 3,
          color: '#10b981'
        },
        itemStyle: {
          color: '#10b981'
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(16, 185, 129, 0.4)' },
            { offset: 1, color: 'rgba(16, 185, 129, 0.0)' }
          ])
        },
        data: heatmapData.value.map(item => item[1])
      }
    ]
  };
});

function calculatePercentage(hits: number | null | undefined) {
    const val = hits || 0;
    const max = trendingDocs.value.length > 0 ? (trendingDocs.value[0].hits || 1) : 1;
    const p = Math.round((val / max) * 100);
    return isNaN(p) ? 0 : Math.min(100, Math.max(0, p));
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
    blockchainStats.value = data.blockchain_stats || { on_chain_count: 0, tamper_alerts: 0, block_height: 15000 };
    blockchainHistory.value = data.blockchain_history || [];
    securityAlerts.value = data.security_alerts || [];
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
  font-family: var(--app-font-title);
  font-size: 28px;
  font-weight: 800;
  color: #1e1b4b;
  letter-spacing: -0.02em;
}

.subtitle {
  margin: 4px 0 0 0;
  color: #64748b;
  font-size: 15px;
  font-weight: 500;
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
  background: rgba(99, 102, 241, 0.1);
  color: #4338ca;
}
.kpi-icon.active {
  background: var(--el-bg-color-page);
  color: var(--el-text-color-regular);
}
.kpi-icon.warning {
  background: rgba(245, 158, 11, 0.1);
  color: #b45309;
}
.kpi-icon.success {
  background: rgba(16, 185, 129, 0.1);
  color: #047857;
}
.kpi-icon.danger {
  background: rgba(239, 68, 68, 0.1);
  color: #b91c1c;
}
.kpi-icon.info {
  background: rgba(99, 102, 241, 0.1);
  color: #4338ca;
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
  border-radius: 16px;
  background-color: rgba(255, 255, 255, 0.4) !important;
  backdrop-filter: blur(20px) !important;
  -webkit-backdrop-filter: blur(20px) !important;
  border: 1px solid rgba(255, 255, 255, 0.5) !important;
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1) !important;
  transition: all 0.3s ease;
}

:deep(.el-card.chart-card) {
  background-color: transparent !important;
  border: none !important;
}

:deep(.chart-card .el-card__header) {
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.1);
}

:deep(.chart-card .el-card__body) {
  background: transparent !important;
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
.echart-container.heatmap {
  height: 320px;
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

/* Blockchain & Cyber Styles */
.blockchain-section {
  margin-bottom: 30px;
  background: rgba(64, 158, 255, 0.02);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(64, 158, 255, 0.1);
}
.header h2 {
  font-family: var(--app-font-title);
  font-size: 28px;
  font-weight: 800;
  color: #1e1b4b;
  letter-spacing: -0.02em;
}

.section-title {
  font-family: var(--app-font-title);
  font-size: 18px;
  font-weight: 700;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
  color: #1e293b;
  letter-spacing: -0.01em;
}
.section-title.cyber {
  color: #409eff;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.blockchain-kpi-row {
  margin-bottom: 24px;
}
.kpi-card.blockchain {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(64, 158, 255, 0.2);
}
.kpi-card.blockchain.cyber-blue { background: linear-gradient(135deg, #f0f7ff 0%, #e6f1ff 100%); }
.kpi-card.blockchain.cyber-red { background: linear-gradient(135deg, #fff5f5 0%, #fff0f0 100%); }
.kpi-card.blockchain.cyber-green { background: linear-gradient(135deg, #f6ffed 0%, #f0f9eb 100%); }
.kpi-card.blockchain.cyber-blue-soft { background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%); }
.kpi-card.blockchain.cyber-grey { background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%); }
.kpi-card.blockchain.cyber-orange { background: linear-gradient(135deg, #fffaf5 0%, #fff4e6 100%); }
.kpi-card.blockchain.cyber-green-soft { background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); }
.kpi-card.blockchain.cyber-red-soft { background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%); }
.kpi-card.blockchain.cyber-indigo { background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%); }

.kpi-icon.blue { color: #409eff; }
.kpi-icon.orange { color: #e6a23c; }
.kpi-icon.green { color: #67c23a; }

.kpi-value.glow {
  text-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
  color: #409eff;
}
.kpi-value.glow-red {
  text-shadow: 0 0 8px rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.blockchain-status-tag {
  position: absolute;
  top: 0;
  right: 0;
  font-size: 10px;
  padding: 2px 8px;
  background: rgba(64, 158, 255, 0.1);
  color: #409eff;
  border-bottom-left-radius: 8px;
  font-weight: bold;
}
.blockchain-status-tag.danger { background: rgba(245, 108, 108, 0.1); color: #f56c6c; }
.blockchain-status-tag.success { background: rgba(103, 194, 58, 0.1); color: #67c23a; }

.blockchain-card, .security-card {
  min-height: 400px;
}

.hash-feed-container {
  height: 320px;
  overflow-y: auto;
}
.hash-item {
  padding: 12px;
  border-bottom: 1px dashed var(--el-border-color-lighter);
  transition: all 0.3s;
}
.hash-item:hover { background: #f9fbff; }
.hash-time { font-size: 11px; color: var(--el-text-color-secondary); }
.hash-content { font-size: 13px; margin: 4px 0; color: var(--el-text-color-primary); }
.hash-value { font-size: 11px; color: var(--el-color-primary); font-family: monospace; }
.hash-value span { word-break: break-all; opacity: 0.8; }

.security-radar-container {
  height: 320px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.alert-item {
  background: #fff5f5;
  border-left: 4px solid #f56c6c;
  padding: 12px;
  margin-bottom: 12px;
  border-radius: 4px;
}
.alert-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.alert-time { font-size: 11px; color: #f56c6c; }
.alert-body { font-size: 13px; color: #303133; font-weight: bold; }
.alert-footer { font-size: 11px; color: #909399; margin-top: 8px; }

.secure-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
}

.card-header.cyber { color: #409eff; }
.card-header.danger { color: #f56c6c; }

@keyframes pulse {
  0% { opacity: 0.6; }
  50% { opacity: 1; }
  100% { opacity: 0.6; }
}
.pulse-tag { animation: pulse 2s infinite; }
</style>
