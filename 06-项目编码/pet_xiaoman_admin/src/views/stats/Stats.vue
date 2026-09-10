<template>
  <div>
    <PxPageHeader title="数据看板" subtitle="口径与后端一致，跨月对比仅在有上月数据时可用">
      <template #actions>
        <el-date-picker v-model="month" type="month" value-format="YYYY-MM" :clearable="false"
          class="w140" @change="load" />
      </template>
    </PxPageHeader>

    <PxErrorState v-if="failed" text="看板数据加载失败" :loading="loading" @retry="load" />

    <el-skeleton v-if="loading" :rows="8" animated />

    <template v-else>
      <!-- 北极星：一眼看本月完成单数与环比 -->
      <el-card shadow="never" class="block">
        <div class="north">
          <div>
            <div class="north__label">北极星 · {{ data.north_star.label }}</div>
            <div class="north__value">{{ data.north_star.value }}<span class="north__unit">单</span></div>
          </div>
          <div class="north__mom">
            <span>上月 {{ data.north_star.prev }} 单</span>
            <el-tag v-if="data.north_star.mom_pct !== null" size="small"
              :type="data.north_star.mom_pct >= 0 ? 'success' : 'danger'">
              {{ data.north_star.mom_pct >= 0 ? "+" : "" }}{{ data.north_star.mom_pct }}%
            </el-tag>
            <el-tag v-else type="info" size="small">上月无数据</el-tag>
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="block">
        <template #header><span class="card-title">KPI（PRD §3.3）</span></template>
        <div class="kpi-grid">
          <div v-for="k in kpis" :key="k.label" class="kpi">
            <PxStatCard :label="k.label" :value="k.value ?? 0" unit="%" />
            <el-progress :percentage="k.value || 0" :stroke-width="6" :show-text="false" :color="k.color"
              class="kpi__bar" />
          </div>
          <div>
            <PxStatCard label="本月回访数" :value="data.kpi.visit_count || 0" unit="次" />
          </div>
        </div>
      </el-card>

      <el-card shadow="never" class="block">
        <template #header><span class="card-title">订单状态分布（本月下单）</span></template>
        <PxEmpty v-if="!totalOrders" variant="doc" text="本月还没有订单" />
        <template v-else>
          <div v-for="(n, s) in data.status_dist" :key="s" class="bar-row">
            <span class="bar-label">{{ s }}</span>
            <div class="bar-track"><div class="bar" :style="{ width: `${(n / totalOrders) * 100}%` }" /></div>
            <span class="bar-value">{{ n }}</span>
          </div>
        </template>
      </el-card>

      <el-card shadow="never" class="block">
        <template #header><span class="card-title">客户来源分布</span></template>
        <PxEmpty v-if="!totalCustomers" variant="user" text="还没有客户来源数据" />
        <div v-for="(n, s) in data.source_dist" :key="s" class="bar-row">
          <span class="bar-label">{{ s }}</span>
          <div class="bar-track">
            <div class="bar bar--accent" :style="{ width: totalCustomers ? `${(n / totalCustomers) * 100}%` : '0%' }" />
          </div>
          <span class="bar-value">{{ n }}</span>
        </div>
      </el-card>

      <el-alert type="info" :closable="false" :title="data.funnel_note" />
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { getStats } from "../../api/stats";
import PxPageHeader from "../../components/PxPageHeader.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxErrorState from "../../components/PxErrorState.vue";
import PxStatCard from "../../components/PxStatCard.vue";

const month = ref(new Date().toISOString().slice(0, 7));
const loading = ref(false);
const failed = ref(false);
const data = ref({ north_star: { label: "-", value: 0, prev: 0, mom_pct: null },
                   kpi: {}, status_dist: {}, source_dist: {}, funnel_note: "" });

const totalOrders = computed(() => Object.values(data.value.status_dist).reduce((a, b) => a + b, 0));
const totalCustomers = computed(() => Object.values(data.value.source_dist).reduce((a, b) => a + b, 0));

// 图表色统一走 Token，避免页面上出现散装 hex
const kpis = computed(() => [
  { label: "线上支付渗透率", value: data.value.kpi.pay_penetration_pct, color: "var(--px-chart-1)" },
  { label: "纪念品/加购率", value: data.value.kpi.addon_rate_pct, color: "var(--px-chart-2)" },
  { label: "影像覆盖率", value: data.value.kpi.media_coverage_pct, color: "var(--px-chart-3)" },
  { label: "好评率（≥4 星）", value: data.value.kpi.good_rate_pct, color: "var(--px-chart-4)" },
]);

async function load() {
  loading.value = true;
  failed.value = false;
  try { data.value = await getStats(month.value); } catch { failed.value = true; }
  finally { loading.value = false; }
}
onMounted(load);
</script>

<style scoped>
.block { margin-bottom: var(--px-sp-4); }
.card-title { font-weight: 600; color: var(--px-text-1); }
.north { display: flex; justify-content: space-between; align-items: flex-end; }
.north__label { font-size: var(--px-fs-sm); color: var(--px-text-2); }
.north__value {
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-display);
  font-weight: 600;
  line-height: 1.1;
  color: var(--px-text-1);
  font-variant-numeric: tabular-nums;
}
.north__unit {
  margin-left: var(--px-sp-1);
  font-size: var(--px-fs-md);
  font-weight: 400;
  color: var(--px-text-2);
}
.north__mom {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: var(--px-sp-4);
}
.kpi__bar { margin-top: var(--px-sp-2); }
.bar-row { display: flex; align-items: center; gap: var(--px-sp-3); padding: var(--px-sp-1) 0; }
.bar-label { width: 96px; font-size: var(--px-fs-sm); color: var(--px-text-2); }
.bar-track {
  flex: 1;
  height: 14px;
  background: var(--px-bg-hover);
  border-radius: var(--px-radius-sm);
  overflow: hidden;
}
.bar {
  height: 100%;
  background: var(--px-chart-1);
  border-radius: var(--px-radius-sm);
  transition: width var(--px-motion-normal) var(--px-ease-out);
}
.bar--accent { background: var(--px-chart-4); }
.bar-value {
  width: 40px;
  text-align: right;
  font-size: var(--px-fs-sm);
  color: var(--px-text-1);
  font-variant-numeric: tabular-nums;
}
.w140 { width: 140px; }
@media (max-width: 1366px) {
  .kpi-grid { grid-template-columns: repeat(3, 1fr); }
}
</style>
