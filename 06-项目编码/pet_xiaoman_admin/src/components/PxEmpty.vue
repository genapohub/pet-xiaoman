<template>
  <!-- 空状态要有教育意义：告诉员工「为什么是空的」和「下一步做什么」 -->
  <div class="px-empty">
    <img class="px-empty__icon" :src="iconSrc" alt="" />
    <p class="px-empty__text">{{ text }}</p>
    <p v-if="hint" class="px-empty__hint">{{ hint }}</p>
    <slot name="action" />
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  text: { type: String, default: "暂无数据" },
  hint: { type: String, default: "" },
  variant: { type: String, default: "box" },
});

// Ardot 画布 115:* 专属空态图标导出，避免后台空态都长成同一个通用图标。
const ICONS = {
  dashboard: "/ardot/empty/726317785762607/115_56-20260923_114246035.png",
  order: "/ardot/empty/726317785762607/115_12-20260923_114246046.png",
  service: "/ardot/empty/726317785762607/115_18-20260923_114246047.png",
  customer: "/ardot/empty/726317785762607/115_25-20260923_114246047.png",
  boarding: "/ardot/empty/726317785762607/115_31-20260923_114246049.png",
  stats: "/ardot/empty/726317785762607/115_37-20260923_114246050.png",
  staff: "/ardot/empty/726317785762607/115_43-20260923_114246051.png",
  store: "/ardot/empty/726317785762607/115_48-20260923_114246051.png",
};

const ALIASES = {
  box: "boarding",
  doc: "order",
  image: "service",
  user: "customer",
};

const iconSrc = computed(() => {
  const key = ICONS[props.variant] ? props.variant : (ALIASES[props.variant] || "order");
  return ICONS[key];
});
</script>

<style scoped>
.px-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--px-sp-2);
  padding: var(--px-sp-12) var(--px-sp-4);
  text-align: center;
}
.px-empty__icon {
  width: 64px;
  height: 64px;
  object-fit: contain;
}
.px-empty__text {
  margin: 0;
  font-size: var(--px-fs-base);
  color: var(--px-text-2);
}
.px-empty__hint {
  margin: 0;
  font-size: var(--px-fs-sm);
  color: var(--px-text-3);
  max-width: 42ch;
}
</style>
