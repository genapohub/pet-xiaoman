<template>
  <div class="px-stat" :class="{ 'is-flat': flat }">
    <div class="px-stat__top">
      <div class="px-stat__label">{{ label }}</div>
      <span class="px-stat__dot" aria-hidden="true" />
    </div>
    <div class="px-stat__value">
      {{ value }}<span v-if="unit" class="px-stat__unit">{{ unit }}</span>
    </div>
    <div v-if="hint" class="px-stat__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
// 默认带「彩色顶边 + 圆点」强调（后台工具风，数字最显眼）；
// flat=true 时去掉顶边与圆点、改用画布柔影，用于工作台/看板等画布纯描边白卡场景。
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: 0 },
  unit: { type: String, default: "" },
  hint: { type: String, default: "" },
  flat: { type: Boolean, default: false },
});
</script>

<style scoped>
.px-stat {
  position: relative;
  overflow: hidden;
  padding: var(--px-sp-4);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-top: 3px solid var(--px-primary);
  border-radius: var(--px-radius-lg);
  box-shadow: var(--px-shadow-card);
}
/* flat：对齐画布 v2.0 纯描边白卡（无彩色顶边、无圆点、柔影） */
.px-stat.is-flat {
  border-top-width: 1px;
  box-shadow: var(--px-shadow-card-soft);
}
.px-stat.is-flat .px-stat__dot { display: none; }
.px-stat__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--px-sp-2);
}
.px-stat__label {
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.px-stat__dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: var(--px-chart-2);
}
.px-stat__value {
  margin-top: var(--px-sp-2);
  font-size: 28px;
  font-weight: 600;
  line-height: 1.2;
  color: var(--px-text-1);
  font-family: var(--px-font-num);
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
