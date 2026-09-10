<template>
  <el-tag :type="type" size="small" effect="light" class="px-tag">
    {{ label }}
  </el-tag>
</template>

<script setup>
import { computed } from "vue";
import { BOARDING_SEVERITY, ORDER_STATUS, SALE_STATUS, VISIT_STATUS } from "../utils/status";

const props = defineProps({
  value: { type: String, default: "" },
  kind: { type: String, default: "order" }, // order | sale | visit | boarding
});

// 未知状态退回灰色：宁可不清真，也不要把「未知」显示成绿色让人以为正常
const MAPS = { order: ORDER_STATUS, sale: SALE_STATUS, visit: VISIT_STATUS, boarding: BOARDING_SEVERITY };
const type = computed(() => MAPS[props.kind]?.[props.value] ?? "info");
const label = computed(() => props.value || "未知");
</script>

<style scoped>
.px-tag {
  border-radius: var(--px-radius-sm);
  font-weight: 500;
}
</style>
