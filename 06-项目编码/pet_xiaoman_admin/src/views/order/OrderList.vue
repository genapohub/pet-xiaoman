<!-- B-订单列表 Orders（对齐画布 2:730）
     版式（画布实测）：B 端标准骨架；页头/表格/分页走 PxTablePage。
     筛选区 = 状态分段 pill（全部/待确认/服务中/已完成，对齐画布 2:735~2:744：
       高 32 / radius 999 / padding 8·16 / 13px；激活=松绿填充白字 Medium，未激活=白底描边 #ECE9E3 墨字）
       + 订单号/宠物名搜索。
     表格列按画布 2:747（与画布列序一致，已去掉画布未单列的下单时间）：
       订单号(含宠物名副行) / 服务项目 / 期望服务时间 / 金额 / 状态 / 操作。
     画布有「新建订单」主按钮（2:745，松绿 width150），但代客下单后端尚未对齐
     （《业务流程图》归「有意不做」），故按钮保留、点击给明确待上线提示，不造空表单。 -->
<template>
  <px-table-page class="tp-orders"
    title="订单管理"
    :subtitle="subtitle"
    :rows="rows"
    :loading="loading"
    :failed="failed"
    :total="total"
    :page="query.page"
    :page-size="query.size"
    @retry="load"
    @page-change="setPage"
    @size-change="setSize"
    @row-click="goDetail"
  >
    <template #actions>
      <el-button type="primary" @click="onCreate">
        <el-icon><Plus /></el-icon> 新建订单
      </el-button>
      <el-button :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </template>

    <template #filters>
      <div class="status-pills" role="tablist" aria-label="订单状态">
        <button
          v-for="p in statusPills"
          :key="p.value"
          type="button"
          class="pill"
          :class="{ 'is-active': activeStatus === p.value }"
          @click="setStatus(p.value)"
        >
          {{ p.label }}<span class="pill__n">{{ counts[p.value] }}</span>
        </button>
      </div>
      <el-input v-model="query.keyword" placeholder="订单号 / 宠物名" clearable class="w200" @input="debouncedLoad" />
    </template>

    <!-- 订单号 + 宠物名（副行：门店靠宠物认单，画布单列只给订单号，宠物名作副行补充） -->
    <el-table-column label="订单号" width="190">
      <template #default="{ row }">
        <div class="ono">{{ row.order_no }}</div>
        <div v-if="row.pet_name" class="pet">{{ row.pet_name }}</div>
      </template>
    </el-table-column>
    <el-table-column label="服务项目" min-width="180">
      <template #default="{ row }">{{ row.pkg_name || "—" }}</template>
    </el-table-column>
    <el-table-column label="期望服务时间" width="150">
      <template #default="{ row }">{{ fmtDateTime(row.expect_time) }}</template>
    </el-table-column>
    <el-table-column label="金额" width="100" align="right">
      <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.total_amount) }}</span></template>
    </el-table-column>
    <el-table-column label="状态" min-width="100">
      <template #default="{ row }">
        <PxStatusTag :value="row.status" />
        <el-tag v-if="row.is_night" type="danger" size="small" effect="plain" class="gap-left">夜</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="100" fixed="right">
      <template #default="{ row }">
        <PxActionButton label="查看" :icon="View" tone="primary" tip="进入订单详情与服务记录" @click="goDetail(row)" />
      </template>
    </el-table-column>

    <template #empty>
      <PxEmpty variant="order" text="暂无订单" hint="可切换状态或搜索关键词查看历史订单" />
    </template>
  </px-table-page>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { Plus, Refresh, View } from "@element-plus/icons-vue";
import { listOrders } from "../../api/order";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney } from "../../utils/format";

const router = useRouter();

// 画布 2:735 状态分段：全部 / 待确认 / 服务中 / 已完成（设计稿合并为 4 档，真实 7 态经后端单值过滤）
const statusPills = [
  { value: "", label: "全部" },
  { value: "待确认", label: "待确认" },
  { value: "服务中", label: "服务中" },
  { value: "已完成", label: "已完成" },
];
const counts = reactive({ "": 0, 待确认: 0, 服务中: 0, 已完成: 0 });

const { rows, total, loading, failed, query, load, search, setPage, setSize, debouncedLoad } = useTable(
  (params) => listOrders({ ...params, keyword: params.keyword || undefined }),
  { defaultQuery: { status: "", keyword: "" } }
);

const activeStatus = computed(() => query.status || "");

// 状态分段计数：一次性快照（不改筛选时不重拉，省请求）。失败不影响主列表
async function loadCounts() {
  try {
    const [all, pend, ing, done] = await Promise.all([
      listOrders({ size: 1 }),
      listOrders({ status: "待确认", size: 1 }),
      listOrders({ status: "服务中", size: 1 }),
      listOrders({ status: "已完成", size: 1 }),
    ]);
    counts[""] = all.total ?? 0;
    counts["待确认"] = pend.total ?? 0;
    counts["服务中"] = ing.total ?? 0;
    counts["已完成"] = done.total ?? 0;
  } catch {
    /* 计数缺失时 pill 仍显示标签，仅无数字 */
  }
}

function setStatus(value) {
  query.status = value;
  search();
}

const subtitle = computed(() => {
  if (!query.status && !query.keyword) return `全部订单 · 共 ${total.value} 条`;
  return `共 ${total.value} 条订单`;
});

function goDetail(row) { router.push(`/orders/${row.order_no}`); }

// 代客下单后端未对齐（归「有意不做」），按钮保留、给明确待上线提示，不造空表单
function onCreate() {
  ElMessage.info("代客下单功能后端对接中，敬请期待");
}

onMounted(loadCounts);
</script>

<style scoped>
.num { font-variant-numeric: tabular-nums; }
.gap-left { margin-left: var(--px-sp-1); }
.ono { font-variant-numeric: tabular-nums; }
.pet { margin-top: 2px; color: var(--px-text-3); font-size: var(--px-fs-xs); }
.w200 { width: 200px; }

/* 状态分段 pill：对齐画布 2:736~2:744 */
.status-pills {
  display: inline-flex;
  align-items: center;
  gap: var(--px-sp-2);
}
.pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 32px;
  padding: 0 16px;
  border: 1px solid var(--px-border);
  border-radius: 999px;
  background: var(--px-bg-card);
  color: var(--px-text-1);
  font-size: var(--px-fs-sm);
  font-family: var(--px-font-sans);
  font-weight: 400;
  cursor: pointer;
  transition: all var(--px-motion-fast) linear;
}
.pill:hover { border-color: var(--px-primary); color: var(--px-primary); }
.pill.is-active {
  border-color: var(--px-primary);
  background: var(--px-primary);
  color: var(--px-text-inverse);
  font-weight: 500;
}
.pill__n {
  font-family: var(--px-font-num);
  font-variant-numeric: tabular-nums;
  opacity: 0.85;
}
.pill.is-active .pill__n { opacity: 0.9; }
</style>
