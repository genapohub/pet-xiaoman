<template>
  <div class="px-stat">
    <div class="px-stat__label">{{ label }}</div>
    <div class="px-stat__value">
      {{ value }}<span v-if="unit" class="px-stat__unit">{{ unit }}</span>
    </div>
    <div v-if="hint" class="px-stat__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
// 刻意不做「彩色左边框 + 大图标」那套：后台是工具，数字本身要最显眼
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: 0 },
  unit: { type: String, default: "" },
  hint: { type: String, default: "" },
});
</script>

<style scoped>
.px-stat {
  padding: var(--px-sp-4);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
}
.px-stat__label {
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.px-stat__value {
  margin-top: var(--px-sp-2);
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--px-text-1);
  font-variant-numeric: tabular-nums;
}
.px-stat__unit {
  margin-left: 2px;
  font-size: var(--px-fs-sm);
  font-weight: 400;
  color: var(--px-text-3);
}
.px-stat__hint {
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
}
</style>
