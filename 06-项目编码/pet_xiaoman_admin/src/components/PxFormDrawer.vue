<template>
  <el-drawer
    :model-value="modelValue"
    :title="title"
    :size="size"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <slot />
    <template #footer>
      <div class="px-fd__footer">
        <el-button :disabled="saving" @click="$emit('cancel')">取消</el-button>
        <el-button type="primary" :loading="saving" @click="$emit('submit')">{{ submitText }}</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "" },
  saving: { type: Boolean, default: false },
  submitText: { type: String, default: "保存" },
  size: { type: String, default: "420px" },
});

defineEmits(["update:modelValue", "cancel", "submit"]);
</script>

<style scoped>
.px-fd__footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--px-sp-2);
}
</style>
