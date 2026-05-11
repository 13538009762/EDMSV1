<template>
  <el-dialog
    v-model="visible"
    :title="t('library.createSpace', 'Create New Category')"
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
    // Note: We need to update backend to handle name_en if we want it saved.
    // The current create_space API only takes name and description.
    await api.post('/spaces', {
      name: form.name.trim(),
      name_en: form.name_en.trim() || undefined,
      description: form.description.trim()
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
</script>
