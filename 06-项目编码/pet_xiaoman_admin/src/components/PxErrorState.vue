<template>
  <div class="px-error">
    <el-icon class="px-error__icon"><WarningFilled /></el-icon>
    <span class="px-error__text">{{ text }}</span>
    <el-button size="small" type="primary" text :loading="loading" @click="$emit('retry')">
      重新加载
    </el-button>
  </div>
</template>

<script setup>
import { WarningFilled } from "@element-plus/icons-vue";

defineProps({
  text: { type: String, default: "数据加载失败" },
  loading: { type: Boolean, default: false },
});
defineEmits(["retry"]);
</script>

<style scoped>
.px-error {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  padding: var(--px-sp-3) var(--px-sp-4);
  margin-bottom: var(--px-sp-4);
  background: var(--px-bg-card);
  border: 1px solid var(--px-error);
  border-radius: var(--px-radius-md);
  font-size: var(--px-fs-base);
  color: var(--px-text-1);
}
.px-error__icon {
  font-size: 18px;
  color: var(--px-error);
}
.px-error__text { flex: 1; }
</style>
