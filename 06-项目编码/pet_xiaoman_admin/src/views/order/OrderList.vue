<template>
  <px-table-page
    title="订单管理"
    :subtitle="`共 ${total} 条订单`"
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
      <el-button :loading="loading" @click="load">
        <el-icon><Refresh /></el-icon> 刷新
      </el-button>
    </template>

    <template #filters>
      <el-select v-model="query.status" placeholder="全部状态" clearable class="w140" @change="search">
        <el-option v-for="s in ORDER_STATUS_LIST" :key="s" :label="s" :value="s" />
      </el-select>
      <el-date-picker v-model="query.date" type="date" value-format="YYYY-MM-DD"
        placeholder="期望服务日期" class="w160" @change="search" />
      <el-checkbox v-model="query.is_night" label="仅夜间单" @change="search" />
      <el-input v-model="query.keyword" placeholder="订单号/宠物名" clearable class="w180"
        @input="debouncedLoad" />
    </template>

    <el-table-column prop="order_no" label="订单号" width="170" />
    <el-table-column label="金额" width="120" align="right">
      <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.total_amount) }}</span></template>
    </el-table-column>
    <el-table-column label="状态" width="150">
      <template #default="{ row }">
        <PxStatusTag :value="row.status" />
        <el-tag v-if="row.is_night" type="danger" size="small" effect="plain" class="gap-left">夜</el-tag>
      </template>
    </el-table-column>
    <el-table-column label="期望服务时间" width="160">
      <template #default="{ row }">{{ fmtDateTime(row.expect_time) }}</template>
    </el-table-column>
    <el-table-column label="下单时间" min-width="160">
      <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
    </el-table-column>

    <template #empty>
      <PxEmpty variant="doc" text="没有符合条件的订单" hint="换个状态筛选，或清空关键字试试" />
    </template>
  </px-table-page>
</template>

<script setup>
import { useRouter } from "vue-router";
import { Refresh } from "@element-plus/icons-vue";
import { listOrders } from "../../api/order";
import { useTable } from "../../composables/useTable";
import PxTablePage from "../../components/PxTablePage.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney, todayStr } from "../../utils/format";
import { ORDER_STATUS_LIST } from "../../utils/status";

const router = useRouter();
const { rows, total, loading, failed, query, load, search, setPage, setSize, debouncedLoad } = useTable(
  (params) => listOrders({ ...params, is_night: params.is_night || undefined }),
  // 日期默认「今日」：与「今日工作台」的日常运营动线一致，进页面即看到当天要服务的单
  { defaultQuery: { status: "", date: todayStr(), keyword: "", is_night: false } }
);

function goDetail(row) { router.push(`/orders/${row.order_no}`); }
</script>

<style scoped>
.num { font-variant-numeric: tabular-nums; }
.gap-left { margin-left: var(--px-sp-1); }
.w140 { width: 140px; }
.w160 { width: 160px; }
.w180 { width: 180px; }
</style>
