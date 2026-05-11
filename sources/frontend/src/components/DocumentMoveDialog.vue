<template>
  <el-dialog
    v-model="visible"
    :title="t('library.moveToSpace', 'Move to Space')"
    width="400px"
    @closed="handleClosed"
  >
    <el-form label-position="top">
      <el-form-item :label="t('library.selectSpace', 'Select Target Spaces')">
        <el-select 
          v-model="selectedSpaceIds" 
          style="width: 100%" 
          filterable 
          multiple
          collapse-tags
          collapse-tags-indicator
          :placeholder="t('library.selectSpacePlaceholder', 'Select spaces...')"
        >
          <el-option
            v-for="s in spaces"
            :key="s.id"
            :label="formatSpaceName(s.name, s.name_en)"
            :value="s.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <div style="display: flex; justify-content: space-between; width: 100%">
        <el-button type="danger" plain @click="handleClearAll">
          {{ t('library.clearAllSpaces', 'Clear All Categories') }}
        </el-button>
        <div>
          <el-button @click="visible = false">{{ t('common.cancel') }}</el-button>
          <el-button type="primary" :loading="submitting" @click="handleSubmit">
            {{ t('common.confirm', 'Confirm') }}
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/api/client';
import { ElMessage, ElMessageBox } from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  docIds: number[];
}>();

const emit = defineEmits(['update:modelValue', 'saved']);

const { t, locale, te } = useI18n();
const visible = ref(props.modelValue);
const submitting = ref(false);
const selectedSpaceIds = ref<number[]>([]);
const spaces = ref<any[]>([]);

watch(() => props.modelValue, (val) => {
  visible.value = val;
  if (val) {
    loadSpaces();
    selectedSpaceIds.value = [];
  }
});

watch(visible, (val) => {
  emit('update:modelValue', val);
});

const formatSpaceName = (name: string, nameEn?: string) => {
  if (te(`space.${name}`)) return t(`space.${name}`);
  if (nameEn && te(`space.${nameEn}`)) return t(`space.${nameEn}`);
  return locale.value === 'zh-CN' ? name : (nameEn || name);
};

async function loadSpaces() {
  try {
    const { data } = await api.get('/spaces');
    spaces.value = data.items;
  } catch (err) {
    console.error('Failed to load spaces', err);
  }
}

async function handleClearAll() {
  try {
    await ElMessageBox.confirm(
      t('library.clearSpacesConfirm', 'Are you sure you want to remove all categories from selected documents?'),
      t('common.warning'),
      { type: 'warning' }
    );
    selectedSpaceIds.value = [];
    await handleSubmit();
  } catch {}
}

async function handleSubmit() {
  if (props.docIds.length === 0) return;
  
  submitting.value = true;
  try {
    await api.post('/documents/batch-move', {
      doc_ids: props.docIds,
      space_ids: selectedSpaceIds.value,
      append: false // Replace existing
    });
    ElMessage.success(t('common.success'));
    emit('saved');
    visible.value = false;
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('common.failed'));
  } finally {
    submitting.value = false;
  }
}

function handleClosed() {
  selectedSpaceIds.value = [];
}
</script>
