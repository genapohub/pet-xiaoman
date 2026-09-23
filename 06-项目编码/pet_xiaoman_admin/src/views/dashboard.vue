<!-- B-工作台 Dashboard（对齐画布 104:355 店长今日工作台）
     版式：KPI 四卡 + 近 7 日服务趋势柱 + 服务项目排行。无页头（画布直接进 KPI 区）。
     数据：今日订单 / 本周服务 / 待处理 / 客户总数 + 趋势 + 排行 全部由本地聚合真实接口得出
           （/api/b/orders, /api/b/customers），不虚构。 -->
<template>
  <div class="dash">
    <PxErrorState v-if="failed" text="工作台数据加载失败" :loading="loading" @retry="load" />
    <el-skeleton v-else-if="loading" :rows="6" animated />

    <template v-else>
      <!-- KPI 四卡 -->
      <div class="kpis">
        <div v-for="k in kpis" :key="k.label" class="kpi">
          <div class="kpi__label">{{ k.label }}</div>
          <div class="kpi__value" :class="k.accent ? `is-${k.accent}` : ''">{{ k.value }}</div>
        </div>
      </div>

      <!-- 近 7 日服务趋势（真实日单量，按峰值缩放到 110px，末日高亮陶土橙） -->
      <section class="card trend">
        <h3 class="card__title">近 7 日服务趋势</h3>
        <div class="bars">
          <div
            v-for="(d, i) in trend"
            :key="d.day"
            class="bar"
            :class="{ 'is-accent': i === trend.length - 1 }"
            :style="{ height: d.h + 'px' }"
          />
        </div>
      </section>

      <!-- 服务项目排行（按 pkg_name 聚合营收，取前 3） -->
      <section class="card rank">
        <h3 class="card__title">服务项目排行</h3>
        <PxEmpty v-if="!ranks.length" variant="dashboard" text="暂无服务数据" />
        <div v-for="(r, i) in ranks" :key="r.name" class="rank__row">
          <span class="rank__name">{{ i + 1 }}. {{ r.name }}</span>
          <span class="rank__val">¥{{ fmtMoney(r.value) }}</span>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from "vue";
import { listOrders } from "../api/order";
import { listCustomers } from "../api/batch2";
import PxEmpty from "../components/PxEmpty.vue";
import PxErrorState from "../components/PxErrorState.vue";
import { fmtMoney } from "../utils/format";

const orders = ref([]);
const customerTotal = ref(0);
const loading = ref(false);
const failed = ref(false);

// 日期工具（刻意走本地时区，避免 toISOString 的 UTC 偏移把日期算到前一天）
const pad = (n) => String(n).padStart(2, "0");
const ymd = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const today = new Date();
const todayYmd = ymd(today);

// 本周一（周一为一周起点，本地时区）
function mondayOf(date) {
  const d = new Date(date);
  const day = (d.getDay() + 6) % 7;
  d.setDate(d.getDate() - day);
  d.setHours(0, 0, 0, 0);
  return d;
}
const weekStart = mondayOf(today);

const isToday = (iso) => (iso || "").slice(0, 10) === todayYmd;
const inWeek = (iso) => {
  const t = new Date(iso);
  return t >= weekStart && t <= today;
};
// 待处理 = 仍需人介入的单（待确认 / 已预约），不含已结算与已取消
const isPending = (s) => s === "待确认" || s === "已预约";

const kpis = computed(() => {
  const all = orders.value;
  const todayOrders = all.filter((o) => isToday(o.created_at)).length;
  const weekSvc = all.filter((o) => inWeek(o.created_at)).length;
  const pending = all.filter((o) => isPending(o.status)).length;
  return [
    { label: "今日订单", value: todayOrders, accent: "primary" },
    { label: "本周服务", value: weekSvc, accent: "" },
    { label: "客户总数", value: customerTotal.value, accent: "" },
    { label: "待处理事项", value: pending, accent: "warning" },
  ];
});

// 近 7 日服务趋势：真实日单量，按峰值缩放到 110px
const trend = computed(() => {
  const days = [];
  for (let i = 6; i >= 0; i--) {
    const d = new Date(today);
    d.setDate(d.getDate() - i);
    days.push({ day: ymd(d), count: 0 });
  }
  const map = Object.fromEntries(days.map((d) => [d.day, d]));
  for (const o of orders.value) {
    const k = (o.created_at || "").slice(0, 10);
    if (map[k]) map[k].count++;
  }
  const max = Math.max(1, ...days.map((d) => d.count));
  return days.map((d) => ({ day: d.day, h: Math.round((d.count / max) * 110) }));
});

// 服务项目排行：按 pkg_name 聚合营收，取前 3
const ranks = computed(() => {
  const sum = {};
  for (const o of orders.value) {
    const name = o.pkg_name || "未命名服务";
    sum[name] = (sum[name] || 0) + Number(o.total_amount || 0);
  }
  return Object.entries(sum)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 3)
    .map(([name, value]) => ({ name, value }));
});

async function load() {
  loading.value = true;
  failed.value = false;
  try {
    const [o, c] = await Promise.all([listOrders({ size: 200 }), listCustomers()]);
    orders.value = o.items || o || [];
    const custList = Array.isArray(c) ? c : (c.items || []);
    customerTotal.value = c.total != null ? c.total : custList.length;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<style scoped>
.dash { display: flex; flex-direction: column; gap: var(--px-sp-4); }

/* KPI 四卡 */
.kpis {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--px-sp-4);
}
.kpi {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: 14px;
  box-shadow: var(--px-shadow-card-soft);
}
.kpi__label { font-size: var(--px-fs-sm); color: var(--px-text-2); }
.kpi__value {
  font-family: var(--px-font-num);
  font-size: 22px;
  font-weight: 600;
  line-height: 1.1;
  color: var(--px-text-1);
  font-variant-numeric: tabular-nums;
}
.kpi__value.is-primary { color: var(--px-primary); }
.kpi__value.is-warning { color: var(--px-chart-2); }

/* 通用卡片 */
.card {
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: 14px;
  box-shadow: var(--px-shadow-card-soft);
}
.card__title {
  margin: 0;
  font-family: var(--px-font-serif);
  font-size: 15px;
  font-weight: 600;
  color: var(--px-text-1);
}

/* 趋势柱 */
.trend { padding: 18px; }
.trend .bars {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 110px;
  margin-top: 12px;
}
.bar {
  width: 28px;
  background: var(--px-primary);
  border-radius: 6px;
}
.bar.is-accent { background: var(--px-chart-2); }

/* 服务项目排行 */
.rank { padding: 18px; display: flex; flex-direction: column; gap: 16px; }
.rank__row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.rank__name { font-size: 14px; color: var(--px-text-1); }
.rank__val {
  font-family: var(--px-font-num);
  font-size: 14px;
  font-weight: 500;
  color: var(--px-primary);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1366px) {
  .kpis { grid-template-columns: repeat(2, 1fr); }
}
</style>
