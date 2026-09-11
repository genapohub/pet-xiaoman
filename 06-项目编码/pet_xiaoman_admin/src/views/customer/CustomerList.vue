<template>
  <px-table-page
    title="客户档案"
    :subtitle="`${role}视角 · 共 ${rows.length} 位客户`"
    :rows="rows"
    :loading="loading"
    :failed="failed"
    clickable
    @retry="load"
    @row-click="goDetail"
  >
    <template #actions>
      <el-radio-group v-model="role" @change="search">
        <el-radio-button value="店长" label="店长" />
        <el-radio-button value="店员" label="店员" />
      </el-radio-group>
    </template>

    <el-table-column prop="nickname" label="客户" width="130" />
    <el-table-column prop="phone" label="手机号" width="140" />
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
      <PxEmpty variant="user" text="还没有客户档案" hint="客户在小程序下单或注册后会自动出现在这里" />
    </template>
  </px-table-page>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { View } from "@element-plus/icons-vue";
import { listCustomers } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";

const router = useRouter();
const role = ref("店长");
const { rows, loading, failed, load, search } = useTable(() => listCustomers(role.value));

function goDetail(row) { router.push(`/customers/${row.customer_id}`); }
</script>
