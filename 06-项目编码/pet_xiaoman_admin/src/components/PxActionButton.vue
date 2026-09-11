<template>
  <el-tooltip :content="tip || label" placement="top" :show-after="360">
    <el-button
      class="px-action"
      :class="`px-action--${tone}`"
      text
      :type="buttonType"
      :aria-label="label"
      @click="onClick"
    >
      <el-icon><component :is="icon" /></el-icon>
      <span>{{ label }}</span>
    </el-button>
  </el-tooltip>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  label: { type: String, required: true },
  icon: { type: [Object, Function], required: true },
  tone: { type: String, default: "default" }, // default | primary | success | warning | danger
  tip: { type: String, default: "" },
});

const emit = defineEmits(["click"]);

const buttonType = computed(() => {
  if (props.tone === "primary") return "primary";
  if (props.tone === "success") return "success";
  if (props.tone === "warning") return "warning";
  if (props.tone === "danger") return "danger";
  return "";
});

function onClick(event) {
  event.stopPropagation();
  emit("click", event);
}
</script>

<style scoped>
.px-action {
  min-width: 0;
  height: 28px;
  padding: 0 var(--px-sp-2);
  border-radius: 999px;
  font-size: var(--px-fs-sm);
}
.px-action + .px-action {
  margin-left: var(--px-sp-1);
}
.px-action :deep(.el-icon) {
  margin-right: var(--px-sp-1);
}
.px-action--default {
  color: var(--px-text-2);
}
.px-action--default:hover {
  background: var(--px-primary-softer);
  color: var(--px-primary-pressed);
}
.px-action--primary:hover,
.px-action--success:hover,
.px-action--warning:hover,
.px-action--danger:hover {
  background: var(--px-bg-card);
}
</style>
