<!-- B-工作台 Dashboard（对齐画布 2:647）
     版式：B 端标准骨架，左侧 220px 侧栏 + 64px 顶栏 + 内容区 24px padding。
     主体：页头 → SLA 告警 → 统计卡横排 → 流转订单列表；强调待确认订单与 30 分钟 SLA。 -->
<template>
  <div>
    <PxPageHeader title="今日工作台" :subtitle="`${today} · 共 ${rows.length} 单在流转`">
      <template #actions>
        <el-button :loading="loading" @click="load">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </PxPageHeader>

    <!-- SLA 告警：30 分钟未确认要立刻处理，是最容易漏的一步 -->
    <el-alert v-if="slaOrders.length" type="error" :closable="false" show-icon class="sla">
      <template #title>
        {{ slaOrders.length }} 单等待确认已超 15 分钟（SLA 30 分钟）
        <el-button text type="danger" size="small" @click="goFirst(slaOrders)">去处理</el-button>
      </template>
    </el-alert>

    <div class="stat-row">
      <PxStatCard v-for="s in stats" :key="s.label" :label="s.label" :value="s.value" :unit="s.unit" :hint="s.hint" />
    </div>

    <PxErrorState v-if="failed" text="工作台数据加载失败" :loading="loading" @retry="load" />

    <el-row :gutter="16">
      <el-col v-for="col in columns" :key="col.name" :span="6">
        <el-card shadow="never" class="lane">
          <template #header>
            <span class="lane__name">{{ col.name }}</span>
            <span class="lane__count">{{ col.items.length }}</span>
          </template>
          <PxEmpty v-if="!col.items.length" variant="doc" text="今日暂无" />
          <div v-for="o in col.items" :key="o.order_no" class="order"
               :class="{ 'is-night': o.is_night }" @click="go(o)">
            <div class="order__no">{{ o.order_no }}</div>
            <div class="order__meta">¥{{ fmtMoney(o.total_amount) }} · {{ fmtShort(o.expect_time) }}</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="refresh-hint">最后刷新 {{ lastRefresh }}，数据每 5 分钟自动更新</div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { Refresh } from "@element-plus/icons-vue";
import { listOrders } from "../api/order";
import PxPageHeader from "../components/PxPageHeader.vue";
import PxEmpty from "../components/PxEmpty.vue";
import PxErrorState from "../components/PxErrorState.vue";
import PxStatCard from "../components/PxStatCard.vue";
import { fmtMoney, fmtShort } from "../utils/format";

const router = useRouter();
const rows = ref([]);
const loading = ref(false);
const failed = ref(false);
const lastRefresh = ref("");

const today = new Date().toLocaleDateString("zh-CN", { month: "long", day: "numeric", weekday: "long" });

const SLA_MINUTES = 15;
const STALE = { 待确认: true };
const slaOrders = computed(() =>
  rows.value.filter((o) => STALE[o.status] && Date.now() - new Date(o.created_at) > SLA_MINUTES * 60000));

const columns = computed(() => {
  const by = (s) => rows.value.filter((o) => o.status === s);
  return [
    { name: "待确认", items: by("待确认") },
    { name: "已预约·今日接宠", items: by("已预约") },
    { name: "服务中", items: by("服务中") },
    { name: "待交付", items: by("待交付") },
  ];
});

const stats = computed(() => {
  const pending = rows.value.filter((o) => o.status === "待确认").length;
  const todayDone = rows.value.filter((o) => o.status === "已完成").length;
  const amount = rows.value.reduce((a, o) => a + Number(o.total_amount || 0), 0);
  return [
    { label: "待确认", value: pending, unit: "单", hint: pending ? "优先处理" : "无积压" },
    { label: "今日完成", value: todayDone, unit: "单", hint: "含本次拉取全部订单" },
    { label: "今日流水", value: `¥${fmtMoney(amount)}`, unit: "", hint: "下单金额合计" },
    { label: "夜间单", value: rows.value.filter((o) => o.is_night).length, unit: "单", hint: "夜间服务加收" },
  ];
});

async function load() {
  loading.value = true;
  failed.value = false;
  try {
    const data = await listOrders({ size: 100 });
    rows.value = data.items;
    lastRefresh.value = new Date().toLocaleTimeString("zh-CN", { hour12: false }).slice(0, 8);
  } catch {
    failed.value = true;
  } finally { loading.value = false; }
}

function go(row) { router.push(`/orders/${row.order_no}`); }
function goFirst(list) { if (list.length) go(list[0]); }

// 门店电脑常年开着，5 分钟自动拉一次，避免员工忘刷新错过新单
let timer;
onMounted(() => {
  load();
  timer = setInterval(load, 5 * 60 * 1000);
});
onUnmounted(() => clearInterval(timer));
</script>

<style scoped>
.sla { margin-bottom: var(--px-sp-4); }
.stat-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--px-sp-4);
  margin-bottom: var(--px-sp-4);
}
.lane :deep(.el-card__header) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--px-sp-3) var(--px-sp-4);
  background: var(--px-bg-card);
}
.lane {
  border-top: 3px solid var(--px-primary);
}
.lane:nth-child(2) { border-top-color: var(--px-chart-2); }
.lane:nth-child(3) { border-top-color: var(--px-chart-3); }
.lane:nth-child(4) { border-top-color: var(--px-chart-1); }
.lane__name { font-weight: 600; color: var(--px-text-1); }
.lane__count {
  min-width: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: var(--px-primary-weak);
  color: var(--px-primary);
  font-size: var(--px-fs-xs);
  font-weight: 600;
  text-align: center;
}
.order {
  padding: var(--px-sp-2) var(--px-sp-3);
  margin-bottom: var(--px-sp-2);
  border: 1px solid var(--px-border);
  border-left: 3px solid transparent;
  border-radius: var(--px-radius-md);
  cursor: pointer;
  transition: all var(--px-motion-fast) linear;
}
.order:hover {
  border-color: var(--px-primary);
  background: var(--px-bg-hover);
}
.order:active { background: var(--px-primary-weak); }
.order:focus-visible {
  outline: 2px solid var(--px-primary);
  outline-offset: 1px;
}
.order.is-night { border-left-color: var(--px-error); }
.order__no {
  font-weight: 600;
  font-size: var(--px-fs-sm);
  color: var(--px-text-1);
}
.order__meta {
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-xs);
  color: var(--px-text-2);
  font-variant-numeric: tabular-nums;
}
.refresh-hint {
  margin-top: var(--px-sp-3);
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
}
@media (max-width: 1366px) {
  .stat-row { grid-template-columns: repeat(2, 1fr); }
}
</style>
