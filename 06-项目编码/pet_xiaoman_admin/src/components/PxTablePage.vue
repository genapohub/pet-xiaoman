<template>
  <div class="px-table-page">
    <PxPageHeader :title="title" :subtitle="subtitle">
      <template #actions><slot name="actions" /></template>
    </PxPageHeader>

    <!-- 错误态：整页内联重试，Toast 不重复打扰（request.js 已统一提示） -->
    <PxErrorState v-if="failed" :text="failedText" :loading="loading" @retry="$emit('retry')" />

    <template v-else>
      <section v-if="$slots.filters" class="px-tp__filters" aria-label="筛选条件">
        <div class="px-tp__filters-head">
          <span class="px-tp__filters-dot" aria-hidden="true" />
          <span>筛选条件</span>
        </div>
        <div class="px-tp__filters-body"><slot name="filters" /></div>
      </section>

      <el-table
        :data="rows"
        v-loading="loading"
        :class="{ clickable }"
        @row-click="(row, col, ev) => $emit('row-click', row, col, ev)"
      >
        <slot />
        <template #empty>
          <slot name="empty">
            <PxEmpty variant="doc" text="暂无数据" />
          </slot>
        </template>
      </el-table>

      <el-pagination
        v-if="total > 0"
        class="px-tp__pager"
        layout="total, sizes, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :page-sizes="pageSizes"
        :current-page="page"
        @current-change="$emit('page-change', $event)"
        @size-change="$emit('size-change', $event)"
      />
    </template>
  </div>
</template>

<script setup>
import PxPageHeader from "./PxPageHeader.vue";
import PxErrorState from "./PxErrorState.vue";
import PxEmpty from "./PxEmpty.vue";

defineProps({
  title: { type: String, required: true },
  subtitle: { type: String, default: "" },
  rows: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
  failed: { type: Boolean, default: false },
  failedText: { type: String, default: "数据加载失败" },
  total: { type: Number, default: 0 },
  page: { type: Number, default: 1 },
  pageSize: { type: Number, default: 20 },
  pageSizes: { type: Array, default: () => [20, 50, 100] },
  clickable: { type: Boolean, default: false },
});

defineEmits(["retry", "page-change", "size-change", "row-click"]);
</script>

<style scoped>
.px-tp__filters {
  padding: var(--px-sp-3);
  margin-bottom: var(--px-sp-4);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-lg);
  box-shadow: var(--px-shadow-card);
}
.px-tp__filters-head {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  margin-bottom: var(--px-sp-2);
  color: var(--px-text-2);
  font-size: var(--px-fs-xs);
  font-weight: 600;
}
.px-tp__filters-dot {
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: var(--px-primary);
}
.px-tp__filters-body {
  display: flex;
  flex-wrap: wrap;
  gap: var(--px-sp-2);
  align-items: center;
}
.px-tp__pager {
  margin-top: var(--px-sp-4);
  justify-content: flex-end;
}
</style>
