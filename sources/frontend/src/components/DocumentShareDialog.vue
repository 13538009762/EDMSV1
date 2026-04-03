<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('editor.sharingTitle')"
    width="520px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <p class="hint">{{ t("editor.sharingHint") }}</p>
    <div v-for="(row, idx) in rows" :key="idx" class="row">
      <el-select
        v-model="row.user_id"
        filterable
        :placeholder="t('editor.sharingUser')"
        style="width: 200px"
      >
        <el-option v-for="u in filteredUsers" :key="u.id" :label="`${u.login_name}`" :value="u.id" />
      </el-select>

      <el-select v-model="row.role" style="width: 140px; margin-left: 8px">
        <template #label>
          <el-tag
            :type="row.role === 'edit' ? 'primary' : row.role === 'comment' ? 'warning' : 'info'"
            disable-transitions
          >
            {{ row.role === 'edit' ? t('editor.roleEdit') : row.role === 'comment' ? t('editor.roleComment') : t('editor.roleView') }}
          </el-tag>
        </template>
        <el-option value="view" :label="t('editor.roleView')">
          <el-tag type="info" size="small">{{ t('editor.roleView') }}</el-tag>
        </el-option>
        <el-option value="edit" :label="t('editor.roleEdit')">
          <el-tag type="primary" size="small">{{ t('editor.roleEdit') }}</el-tag>
        </el-option>
        <el-option value="comment" :label="t('editor.roleComment')">
          <el-tag type="warning" size="small">{{ t('editor.roleComment') }}</el-tag>
        </el-option>
      </el-select>

      <el-button type="danger" link :icon="Delete" style="margin-left: 12px" @click="rows.splice(idx, 1)">
        {{ t("editor.sharingRemove") }}
      </el-button>
    </div>

    <el-button
      type="primary"
      plain
      style="width: 100%; margin-top: 8px; margin-bottom: 16px; border-style: dashed;"
      :icon="Plus"
      @click="rows.push({ user_id: undefined, role: 'view' })"
    >
      {{ t("editor.sharingAdd") }}
    </el-button>
    <template #footer>
      <el-button @click="emit('update:modelValue', false)">{{ t("inbox.cancel") }}</el-button>
      <el-button type="primary" :icon="Check" :loading="saving" @click="save">
        {{ t("editor.sharingSave") }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage } from "element-plus";
// 💡 新增：引入图标
import { Plus, Delete, Check } from "@element-plus/icons-vue";

const props = defineProps<{
  modelValue: boolean;
  documentId: number | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
  (e: "saved"): void;
}>();

const { t } = useI18n();
import { useAuthStore } from "@/stores/auth";
import { computed } from "vue";
const auth = useAuthStore();

const users = ref<Array<{ id: number; login_name: string }>>([]);
const rows = ref<Array<{ user_id: number | undefined; role: string }>>([]);
const saving = ref(false);

const filteredUsers = computed(() => {
  if (!auth.user) return users.value;
  return users.value.filter((u) => u.id !== auth.user!.id);
});


async function loadAll() {
  if (!props.documentId) return;
  const [{ data: u }, { data: p }] = await Promise.all([
    api.get("/users"),
    api.get(`/documents/${props.documentId}/permissions`),
  ]);
  users.value = u.items;
  rows.value = (p.items as Array<{ user_id: number; role: string }>).map((x) => ({
    user_id: x.user_id,
    role: x.role,
  }));
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open && props.documentId) {
      try {
        await loadAll();
      } catch {
        rows.value = [];
      }
    }
  },
);

async function save() {
  if (!props.documentId) return;
  const grants = rows.value
    .filter((r) => r.user_id != null)
    .map((r) => ({ user_id: r.user_id, role: r.role }));
  saving.value = true;
  try {
    await api.post(`/documents/${props.documentId}/permissions`, { grants });
    ElMessage.success(t("editor.sharingSaved"));
    emit("saved");
    emit("update:modelValue", false);
  } catch {
    ElMessage.error(t("library.createFailed"));
  } finally {
    saving.value = false;
  }
}
</script>

<style scoped>
.hint {
  color: var(--el-text-color-secondary);
  font-size: 13px;
  margin-bottom: 12px;
}
.row {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  flex-wrap: wrap;
}
</style>
