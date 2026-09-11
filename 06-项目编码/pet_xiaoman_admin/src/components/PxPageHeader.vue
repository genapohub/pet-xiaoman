<template>
  <header class="px-header">
    <div class="px-header__main">
      <button v-if="back" class="px-header__back" type="button" @click="$router.back()">
        <el-icon><ArrowLeft /></el-icon>
      </button>
      <div>
        <span class="px-header__eyebrow">PET XIAOMAN ADMIN</span>
        <h1 class="px-header__title">{{ title }}</h1>
        <p v-if="subtitle" class="px-header__sub">{{ subtitle }}</p>
      </div>
    </div>
    <div class="px-header__actions"><slot name="actions" /></div>
  </header>
</template>

<script setup>
import { ArrowLeft } from "@element-plus/icons-vue";

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  back: { type: Boolean, default: false },
});
</script>

<style scoped>
.px-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--px-sp-4);
  margin-bottom: var(--px-sp-5, 20px);
  padding-bottom: var(--px-sp-3);
  border-bottom: 1px solid rgba(201, 205, 212, 0.55);
}
.px-header__main {
  display: flex;
  align-items: center;
  gap: var(--px-sp-3);
  min-width: 0;
}
.px-header__back {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-sm);
  background: var(--px-bg-card);
  color: var(--px-text-2);
  cursor: pointer;
  transition: all var(--px-motion-fast) linear;
}
.px-header__back:hover {
  color: var(--px-primary);
  border-color: var(--px-primary);
}
.px-header__back:focus-visible {
  outline: 2px solid var(--px-primary);
  outline-offset: 2px;
}
.px-header__title {
  margin: var(--px-sp-1) 0 0;
  font-size: var(--px-fs-xl);
  font-weight: 600;
  line-height: var(--px-lh-title);
  color: var(--px-text-1);
}
.px-header__eyebrow {
  display: inline-flex;
  align-items: center;
  gap: var(--px-sp-1);
  color: var(--px-primary-pressed);
  font-size: var(--px-fs-xs);
  font-weight: 700;
  letter-spacing: 0;
}
.px-header__eyebrow::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--px-chart-2);
}
.px-header__sub {
  margin: var(--px-sp-1) 0 0;
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.px-header__actions {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  flex-shrink: 0;
}
</style>
