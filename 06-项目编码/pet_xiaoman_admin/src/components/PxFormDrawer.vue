<template>
  <el-drawer
    :model-value="modelValue"
    :size="size"
    @update:model-value="$emit('update:modelValue', $event)"
  >
    <template #header>
      <div class="px-fd__header">
        <span class="px-fd__mark" aria-hidden="true">
          <el-icon v-if="icon"><component :is="icon" /></el-icon>
        </span>
        <div>
          <h2 class="px-fd__title">{{ title }}</h2>
          <p v-if="subtitle" class="px-fd__sub">{{ subtitle }}</p>
        </div>
      </div>
    </template>

    <slot />
    <template #footer>
      <div class="px-fd__footer">
        <span v-if="footerHint" class="px-fd__hint">{{ footerHint }}</span>
        <div class="px-fd__actions">
          <el-button :disabled="saving" @click="$emit('cancel')">取消</el-button>
          <el-button type="primary" :loading="saving" @click="$emit('submit')">{{ submitText }}</el-button>
        </div>
      </div>
    </template>
  </el-drawer>
</template>

<script setup>
defineProps({
  modelValue: { type: Boolean, default: false },
  title: { type: String, default: "" },
  subtitle: { type: String, default: "" },
  footerHint: { type: String, default: "" },
  icon: { type: [Object, Function], default: null },
  saving: { type: Boolean, default: false },
  submitText: { type: String, default: "保存" },
  size: { type: String, default: "420px" },
});

defineEmits(["update:modelValue", "cancel", "submit"]);
</script>

<style scoped>
.px-fd__footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--px-sp-2);
}
.px-fd__header {
  display: flex;
  align-items: center;
  gap: var(--px-sp-3);
}
.px-fd__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: var(--px-radius-lg);
  background: var(--px-primary-weak);
  color: var(--px-primary-pressed);
}
.px-fd__title {
  margin: 0;
  color: var(--px-text-1);
  font-size: var(--px-fs-lg);
  font-weight: 600;
  line-height: var(--px-lh-title);
}
.px-fd__sub {
  margin: var(--px-sp-1) 0 0;
  color: var(--px-text-2);
  font-size: var(--px-fs-sm);
}
.px-fd__hint {
  color: var(--px-text-3);
  font-size: var(--px-fs-xs);
}
.px-fd__actions {
  display: flex;
  gap: var(--px-sp-2);
}
</style>
