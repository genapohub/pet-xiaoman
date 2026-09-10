<template>
  <!-- 空状态要有教育意义：告诉员工「为什么是空的」和「下一步做什么」 -->
  <div class="px-empty">
    <el-icon class="px-empty__icon"><component :is="icon" /></el-icon>
    <p class="px-empty__text">{{ text }}</p>
    <p v-if="hint" class="px-empty__hint">{{ hint }}</p>
    <slot name="action" />
  </div>
</template>

<script setup>
import { Box, Document, Picture, User } from "@element-plus/icons-vue";
import { computed } from "vue";

const props = defineProps({
  text: { type: String, default: "暂无数据" },
  hint: { type: String, default: "" },
  variant: { type: String, default: "box" }, // box | doc | image | user
});

const ICONS = { box: Box, doc: Document, image: Picture, user: User };
const icon = computed(() => ICONS[props.variant] || Box);
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
  font-size: 40px;
  color: var(--px-text-4);
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
