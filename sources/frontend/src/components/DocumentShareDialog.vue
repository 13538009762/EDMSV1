<template>
  <el-dialog
    :model-value="modelValue"
    :title="t('editor.sharingTitle')"
    width="600px"
    destroy-on-close
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="sharing-dialog-content">
      <div style="margin-bottom: 20px; border-bottom: 1px solid var(--el-border-color-lighter); padding-bottom: 12px;">
        <el-switch v-model="isPublic" :active-text="t('editor.isPublic')" />
        <p class="hint" style="margin-top: 4px;">{{ t('editor.isPublicHint') }}</p>
      </div>

      <!-- 可编辑 (Only for Drafts) -->
      <div class="perm-section" v-if="docStatus === 'draft'">
        <div class="section-header">
          <el-tag type="primary" effect="plain">{{ t('editor.roleEdit') }}</el-tag>
          <span class="section-desc">可以修改文档内容和设置</span>
        </div>
        <el-select
          v-model="editIds"
          multiple
          filterable
          collapse-tags
          :placeholder="t('editor.sharingUser')"
          style="width: 100%"
        >
          <el-option
            v-for="u in optionsForEdit"
            :key="u.id"
            :label="u.login_name"
            :value="u.id"
          />
        </el-select>
      </div>

      <!-- 可批注 -->
      <div class="perm-section">
        <div class="section-header">
          <el-tag type="warning" effect="plain">{{ t('editor.roleComment') }}</el-tag>
          <span class="section-desc">可以针对内容发表批注</span>
        </div>
        <el-select
          v-model="commentIds"
          multiple
          filterable
          collapse-tags
          :placeholder="t('editor.sharingUser')"
          style="width: 100%"
        >
          <el-option
            v-for="u in optionsForComment"
            :key="u.id"
            :label="u.login_name"
            :value="u.id"
          />
        </el-select>
      </div>

      <!-- 只读 -->
      <div class="perm-section">
        <div class="section-header">
          <el-tag type="info" effect="plain">{{ t('editor.roleView') }}</el-tag>
          <span class="section-desc">仅允许查看文档</span>
        </div>
        <el-select
          v-model="viewIds"
          multiple
          filterable
          collapse-tags
          :placeholder="t('editor.sharingUser')"
          style="width: 100%"
        >
          <el-option
            v-for="u in optionsForView"
            :key="u.id"
            :label="u.login_name"
            :value="u.id"
          />
        </el-select>
      </div>
    </div>

    <template #footer>
      <el-button @click="emit('update:modelValue', false)">{{ t("inbox.cancel") }}</el-button>
      <el-button type="primary" :icon="Check" :loading="saving" @click="save">
        {{ t("editor.sharingSave") }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useI18n } from "vue-i18n";
import api from "@/api/client";
import { ElMessage } from "element-plus";
import { Check } from "@element-plus/icons-vue";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{
  modelValue: boolean;
  documentId: number | null;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
  (e: "saved"): void;
}>();

const { t } = useI18n();
const auth = useAuthStore();

const users = ref<Array<{ id: number; login_name: string }>>([]);
const editIds = ref<number[]>([]);
const commentIds = ref<number[]>([]);
const viewIds = ref<number[]>([]);
const isPublic = ref(false);
const docStatus = ref("");
const saving = ref(false);

const availableUsers = computed(() => {
  return users.value.filter(u => u.id !== auth.user?.id);
});

/**
 * 规则逻辑：
 * 1. 只读 (View) 选择后，不可选择编辑和批注 (V disjoint E,C)
 * 2. 编辑 (Edit) 选择后，不可选择只读，但可以选择批注 (E disjoint V, E can overlap C)
 * 3. 批注 (Comment) 选择后，不可选择其他两个 (C disjoint V, C disjoint E ??) 
 *    注：用户说“编辑后可选批注”，但又说“批注后不可选其他两个”。
 *    理解为：Edit 是最高级，选了 Edit 可以顺便选 Comment（或在 Comment 列表里看到）；
 *    但如果一个人没选 Edit 而是直接选了 Comment，就不能选 Edit 了。
 */

const optionsForView = computed(() => {
  // 只读选项：排除已经选了编辑或批注的人
  return availableUsers.value.filter(u => !editIds.value.includes(u.id) && !commentIds.value.includes(u.id));
});

const optionsForEdit = computed(() => {
  // 编辑选项：排除已经选了只读的人；
  // 另外根据“批注后不可选其他”，如果已经在批注里且不在编辑里，也排除？
  return availableUsers.value.filter(u => {
    const inView = viewIds.value.includes(u.id);
    const inCommentOnly = commentIds.value.includes(u.id) && !editIds.value.includes(u.id);
    return !inView && !inCommentOnly;
  });
});

const optionsForComment = computed(() => {
  // 批注选项：排除只读；编辑的人可以选批注
  return availableUsers.value.filter(u => !viewIds.value.includes(u.id));
});

async function loadAll() {
  if (!props.documentId) return;
  const [{ data: u }, { data: p }, { data: doc }] = await Promise.all([
    api.get("/users"),
    api.get(`/documents/${props.documentId}/permissions`),
    api.get(`/documents/${props.documentId}`),
  ]);
  users.value = u.items;
  isPublic.value = doc.is_public;
  docStatus.value = doc.status;

  editIds.value = [];
  commentIds.value = [];
  viewIds.value = [];

  (p.items as Array<{ user_id: number; role: string }>).forEach(perm => {
    if (perm.role === 'edit' && doc.status === 'draft') editIds.value.push(perm.user_id);
    else if (perm.role === 'comment') commentIds.value.push(perm.user_id);
    else if (perm.role === 'edit' && doc.status !== 'draft') viewIds.value.push(perm.user_id); // 降级
    else viewIds.value.push(perm.user_id);
  });
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open && props.documentId) {
      try {
        await loadAll();
      } catch {
        editIds.value = [];
        commentIds.value = [];
        viewIds.value = [];
      }
    }
  },
);

async function save() {
  if (!props.documentId) return;
  
  // 权限映射回后端 role
  const grantsMap = new Map<number, string>();
  
  // 优先级顺序：View < Comment < Edit
  viewIds.value.forEach(id => grantsMap.set(id, 'view'));
  commentIds.value.forEach(id => grantsMap.set(id, 'comment'));
  editIds.value.forEach(id => grantsMap.set(id, 'edit'));

  const grants = Array.from(grantsMap.entries()).map(([user_id, role]) => ({ user_id, role }));

  saving.value = true;
  try {
    await Promise.all([
      api.post(`/documents/${props.documentId}/permissions`, { grants }),
      api.patch(`/documents/${props.documentId}`, { is_public: isPublic.value })
    ]);
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
.perm-section {
  margin-bottom: 24px;
}
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}
.section-desc {
  font-size: 13px;
  color: var(--el-text-color-secondary);
}
</style>
