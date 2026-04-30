<template>
  <div class="notifications-page">
    <div class="page-header">
      <div class="title-area">
        <h1>{{ t('nav.notifications', 'Notifications') }}</h1>
        <p class="subtitle">管理您的系统消息、协作提醒与审批通知</p>
      </div>
      <div class="actions">
        <el-button type="primary" plain @click="loadNotifications" :loading="loading" :icon="Refresh">
          {{ t('library.refresh') }}
        </el-button>
        <el-button type="success" ghost @click="markAllRead" v-if="unreadCount > 0" :icon="Check">
          {{ t('common.markAllRead') }}
        </el-button>
      </div>
    </div>

    <el-card shadow="never" class="list-card">
      <template v-if="notifications.length > 0">
        <div v-for="n in notifications" :key="n.id" class="notif-row" :class="{ 'is-unread': !n.is_read }">
          <div class="status-dot" v-if="!n.is_read"></div>
          
          <div class="notif-icon">
            <el-icon :size="24" :class="n.type">
              <component :is="getTypeIcon(n.type)" />
            </el-icon>
          </div>

          <div class="notif-main" @click="readNotification(n)">
            <div class="notif-header">
              <span class="notif-title">{{ n.title }}</span>
              <el-tag size="small" :type="getTypeTag(n.type)" effect="light" class="type-tag">
                {{ n.type }}
              </el-tag>
            </div>
            <div class="notif-body">{{ n.content }}</div>
            <div class="notif-footer">
              <span class="notif-time">{{ formatLocalDate(n.created_at) }}</span>
              <span v-if="n.expires_at" class="expiry-hint">
                将于 {{ formatLocalDate(n.expires_at) }} 自动删除
              </span>
            </div>
          </div>

          <div class="notif-actions">
            <el-tooltip :content="n.is_starred ? '取消星标' : '添加星标'" placement="top">
              <el-button 
                circle
                :type="n.is_starred ? 'warning' : 'info'" 
                :plain="!n.is_starred"
                :icon="n.is_starred ? StarFilled : Star" 
                @click="toggleStar(n)"
              />
            </el-tooltip>
            <el-tooltip content="删除通知" placement="top">
              <el-button 
                circle
                type="danger" 
                plain
                :icon="Delete" 
                @click="deleteNotif(n)"
              />
            </el-tooltip>
          </div>
        </div>
      </template>

      <div v-else class="empty-state">
        <el-empty :description="t('nav.noNotifications')" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from "vue";
import { useI18n } from "vue-i18n";
import { useRouter } from "vue-router";
import api from "@/api/client";
import { 
  Bell, Star, StarFilled, Delete, Refresh, Check, 
  Monitor, Edit, Warning
} from "@element-plus/icons-vue";
import { formatLocalDate } from "@/utils/date";
import { ElMessage } from "element-plus";

const { t } = useI18n();
const router = useRouter();
const notifications = ref<any[]>([]);
const unreadCount = ref(0);
const loading = ref(false);

async function loadNotifications() {
  loading.value = true;
  try {
    const { data } = await api.get('/notifications');
    notifications.value = data.items;
    unreadCount.value = data.unread_count;
  } catch {
    ElMessage.error("获取通知失败");
  } finally {
    loading.value = false;
  }
}

async function markAllRead() {
  try {
    await api.post('/notifications/read-all');
    loadNotifications();
    ElMessage.success(t('common.markAllRead'));
  } catch {}
}

async function readNotification(n: any) {
  try {
    if (!n.is_read) {
      await api.post(`/notifications/${n.id}/read`);
      n.is_read = true;
      unreadCount.value = Math.max(0, unreadCount.value - 1);
    }
    if (n.link_url) {
      router.push(n.link_url);
    }
  } catch {}
}

async function toggleStar(n: any) {
  try {
    const { data } = await api.post(`/notifications/${n.id}/star`);
    n.is_starred = data.is_starred;
    ElMessage.success(n.is_starred ? "已收藏" : "已取消收藏");
    // 更新列表中的 expires_at (如果不取消星标，后端返回的 expires_at 可能为空)
    loadNotifications(); 
  } catch {}
}

async function deleteNotif(n: any) {
  try {
    await api.delete(`/notifications/${n.id}`);
    notifications.value = notifications.value.filter(x => x.id !== n.id);
    ElMessage.success("已删除");
  } catch {}
}

function getTypeIcon(type: string) {
  switch (type) {
    case '审批': return Warning;
    case '协作': return Edit;
    case '系统': return Monitor;
    default: return Bell;
  }
}

function getTypeTag(type: string) {
  switch (type) {
    case '审批': return 'warning';
    case '协作': return 'primary';
    case '系统': return 'success';
    default: return 'info';
  }
}

onMounted(loadNotifications);
</script>

<style scoped>
.notifications-page {
  padding: 24px;
  max-width: 1000px;
  margin: 0 auto;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}
.title-area h1 {
  font-size: 28px;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
}
.subtitle {
  color: var(--el-text-color-secondary);
  font-size: 14px;
  margin: 0;
}
.list-card {
  border-radius: 12px;
  border: 1px solid var(--el-border-color-lighter);
}

.notif-row {
  display: flex;
  align-items: flex-start;
  padding: 20px;
  border-bottom: 1px solid var(--el-border-color-extra-light);
  transition: all 0.2s;
  position: relative;
  cursor: pointer;
}
.notif-row:last-child {
  border-bottom: none;
}
.notif-row:hover {
  background-color: var(--el-fill-color-light);
}

.notif-row.is-unread {
  background-color: var(--el-color-primary-light-9);
}
.status-dot {
  position: absolute;
  left: 8px;
  top: 28px;
  width: 8px;
  height: 8px;
  background-color: var(--el-color-primary);
  border-radius: 50%;
}

.notif-icon {
  margin-right: 16px;
  padding-top: 4px;
}
.notif-icon .审批 { color: var(--el-color-warning); }
.notif-icon .协作 { color: var(--el-color-primary); }
.notif-icon .系统 { color: var(--el-color-success); }

.notif-main {
  flex: 1;
}
.notif-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 6px;
}
.notif-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
.notif-body {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 8px;
  line-height: 1.6;
}
.notif-footer {
  display: flex;
  align-items: center;
  gap: 16px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.expiry-hint {
  color: var(--el-color-info);
  background: var(--el-fill-color-darker);
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.notif-actions {
  display: flex;
  gap: 8px;
  margin-left: 20px;
}

.empty-state {
  padding: 80px 0;
}
</style>
