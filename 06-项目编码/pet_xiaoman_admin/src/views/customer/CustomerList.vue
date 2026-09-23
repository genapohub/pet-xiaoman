<!-- B-客户管理 Customers（对齐画布 2:1002）
     版式：B 端标准列表页；表格列为客户、手机号、累计消费、宠物、服务次数、回访状态、操作。
     行点击进入客户详情，会员等级与导出客户为已确认的后续规划，不在本期补。 -->
<template>
  <px-table-page
    title="客户档案"
    subtitle="手机号脱敏按登录账号角色决定：店长看全量，店员脱敏"
    :rows="rows"
    :loading="loading"
    :failed="failed"
    clickable
    @retry="load"
    @row-click="goDetail"
  >
    <template #actions />

    <el-table-column prop="nickname" label="客户" width="130" />
    <el-table-column prop="phone" label="手机号" width="140" />
    <!-- 累计消费：只算已完成订单；hover 提示实收合计，差额=已完成但未登记收款的单 -->
    <el-table-column label="累计消费" width="130" align="right">
      <template #default="{ row }">
        <el-tooltip
          :content="`已完成订单金额 ¥${fmtMoney(row.total_spent)}；其中已登记收款 ¥${fmtMoney(row.paid_total)}`"
          placement="top"
        >
          <span class="num spent">¥{{ fmtMoney(row.total_spent) }}</span>
        </el-tooltip>
      </template>
    </el-table-column>
    <el-table-column label="宠物" min-width="120">
      <template #default="{ row }">{{ row.pets.join("、") || "—" }}</template>
    </el-table-column>
    <el-table-column prop="order_count" label="服务次数" width="90" align="center" />
    <el-table-column label="回访状态" width="100">
      <template #default="{ row }"><PxStatusTag :value="row.visit_status" kind="visit" /></template>
    </el-table-column>
    <el-table-column label="操作" width="100" fixed="right">
      <template #default="{ row }">
        <PxActionButton label="查看" :icon="View" tone="primary" tip="查看客户详情与回访记录" @click="goDetail(row)" />
      </template>
    </el-table-column>

    <template #empty>
      <PxEmpty variant="customer" text="还没有客户档案" hint="客户在小程序下单或注册后会自动出现在这里" />
    </template>
  </px-table-page>
</template>

<script setup>
import { useRouter } from "vue-router";
import { View } from "@element-plus/icons-vue";
import { listCustomers } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtMoney } from "../../utils/format";

const router = useRouter();
const { rows, loading, failed, load, search } = useTable(() => listCustomers());

function goDetail(row) { router.push(`/customers/${row.customer_id}`); }
</script>

<style scoped>
.num { font-variant-numeric: tabular-nums; }
.spent { font-weight: 600; color: var(--px-text-1); }
</style>
