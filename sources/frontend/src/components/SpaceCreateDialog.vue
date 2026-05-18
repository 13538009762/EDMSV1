<template>
  <el-dialog
    v-model="visible"
    :title="spaceData ? t('library.editSpace', 'Edit Category') : t('library.createSpace', 'Create New Category')"
    width="450px"
    @closed="handleClosed"
    append-to-body
  >
    <el-form :model="form" label-position="top">
      <el-form-item :label="t('library.spaceName', 'Category Name')" required>
        <el-input v-model="form.name" :placeholder="t('library.spaceNamePlaceholder', 'Enter space name...')" />
      </el-form-item>
      <el-form-item :label="t('library.spaceNameEn', 'Category Name (English)')">
        <el-input v-model="form.name_en" placeholder="Enter English name (optional)" />
      </el-form-item>
      <el-form-item :label="t('library.spaceDescription', 'Description')">
        <el-input 
          v-model="form.description" 
          type="textarea" 
          :rows="3" 
          :placeholder="t('library.spaceDescriptionPlaceholder', 'Briefly describe the purpose of this category')" 
        />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="visible = false">{{ t('common.cancel') }}</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        {{ t('common.confirm') }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import api from '@/api/client';
import { ElMessage } from 'element-plus';

const props = defineProps<{
  modelValue: boolean;
  spaceData?: {
    id: number;
    name: string;
    name_en?: string;
    description?: string;
  } | null;
}>();

const emit = defineEmits(['update:modelValue', 'saved']);

const { t } = useI18n();
const visible = ref(props.modelValue);
const submitting = ref(false);

const form = reactive({
  name: '',
  name_en: '',
  description: ''
});

watch(() => props.modelValue, (val) => {
  visible.value = val;
});

watch(visible, (val) => {
  emit('update:modelValue', val);
});

watch(() => props.spaceData, (val) => {
  if (val) {
    form.name = val.name || '';
    form.name_en = val.name_en || '';
    form.description = val.description || '';
  } else {
    form.name = '';
    form.name_en = '';
    form.description = '';
  }
}, { immediate: true });

function handleClosed() {
  form.name = '';
  form.name_en = '';
  form.description = '';
}

async function handleSubmit() {
  if (!form.name.trim()) {
    ElMessage.warning(t('library.spaceNameRequired', 'Please enter a name'));
    return;
  }
  
  submitting.value = true;
  try {
    const payload = {
      name: form.name.trim(),
      name_en: form.name_en.trim() || undefined,
      description: form.description.trim()
    };
    
    if (props.spaceData?.id) {
      await api.patch(`/spaces/${props.spaceData.id}`, payload);
    } else {
      await api.post('/spaces', payload);
    }
    
    ElMessage.success(t('common.success'));
    emit('saved');
    visible.value = false;
  } catch (err: any) {
    ElMessage.error(err.response?.data?.error || t('common.failed'));
  } finally {
    submitting.value = false;
  }
}
</script>
