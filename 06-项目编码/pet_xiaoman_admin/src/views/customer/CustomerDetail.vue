<!-- B-客户详情 CustomerDetail（对齐画布 81:25）
     来源：代码已有 /customers/:customerId 详情页，承接客户管理列表 2:1002。
     版式：页头返回 → 客户基础资料 → 服务历史 → 回访记录/回访表单。 -->
<template>
  <el-skeleton v-if="loading" :rows="6" animated />
  <div v-else-if="c">
    <PxPageHeader :title="c.nickname" :subtitle="`${c.phone || '未留手机号'} · 来源：${c.source || '未填写'}`" back />

    <el-card shadow="never" class="block">
      <el-descriptions :column="3" size="small">
        <el-descriptions-item label="昵称">{{ c.nickname }}</el-descriptions-item>
        <el-descriptions-item label="手机号">{{ c.phone || "—" }}</el-descriptions-item>
        <el-descriptions-item label="来源">
          <el-select :model-value="c.source" class="w120" @change="onSource">
            <el-option v-for="s in SOURCES" :key="s" :label="s" :value="s" />
          </el-select>
        </el-descriptions-item>
        <el-descriptions-item label="宠物">
          {{ c.pets.map((p) => `${p.name}（${p.species}）`).join("、") || "—" }}
        </el-descriptions-item>
      </el-descriptions>
    </el-card>

    <el-card shadow="never" header="服务历史" class="block">
      <PxEmpty v-if="!c.orders?.length" variant="order" text="还没有服务记录" />
      <el-table v-else :data="c.orders" size="small">
        <el-table-column prop="order_no" label="订单号" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }"><PxStatusTag :value="row.status" /></template>
        </el-table-column>
        <el-table-column label="金额" width="110" align="right">
          <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.total_amount) }}</span></template>
        </el-table-column>
        <el-table-column label="时间">
          <template #default="{ row }">{{ fmtDateTime(row.created_at) }}</template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card shadow="never" header="回访" class="block">
      <PxEmpty v-if="!c.visits?.length" variant="customer" text="暂无回访记录" hint="服务完成后登记满意度，便于后续维护" />
      <el-timeline v-else>
        <el-timeline-item v-for="v in c.visits" :key="v.created_at" :timestamp="fmtDateTime(v.created_at)">
          满意度 {{ v.satisfaction }} 星 · {{ v.would_recommend ? "愿意推荐" : "暂不愿推荐" }}
          <div v-if="v.notes" class="visit-note">{{ v.notes }}</div>
        </el-timeline-item>
      </el-timeline>
      <el-divider />
      <el-form inline class="visit-form">
        <el-form-item label="满意度"><el-rate v-model="visitForm.satisfaction" /></el-form-item>
        <el-form-item label="愿意推荐"><el-switch v-model="visitForm.would_recommend" /></el-form-item>
        <el-form-item><el-input v-model="visitForm.notes" placeholder="回访备注" class="w180" /></el-form-item>
        <el-form-item><el-button type="primary" @click="doVisit">提交回访</el-button></el-form-item>
      </el-form>
    </el-card>
  </div>
  <PxEmpty v-else text="客户信息不存在或已删除" hint="返回列表重新选择" />
</template>

<script setup>
import { onMounted, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { getCustomer, registerVisit, setSource } from "../../api/batch2";
import PxPageHeader from "../../components/PxPageHeader.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney } from "../../utils/format";

const SOURCES = ["小红书", "转介绍", "自然搜索", "其他"];
const route = useRoute();
const customerId = Number(route.params.customerId);
const c = ref(null);
const loading = ref(true);
const visitForm = reactive({ satisfaction: 5, would_recommend: true, notes: "" });

async function load() {
  loading.value = true;
  try { c.value = await getCustomer(customerId); } finally { loading.value = false; }
}
async function onSource(source) {
  await setSource(customerId, source);
  ElMessage.success("来源已更新");
  load();
}
async function doVisit() {
  await registerVisit(customerId, visitForm);
  ElMessage.success("回访已登记");
  load();
}
onMounted(load);
</script>

<style scoped>
.block { margin-bottom: var(--px-sp-4); }
.visit-note {
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.visit-form { margin-top: var(--px-sp-2); }
.num { font-variant-numeric: tabular-nums; }
.w120 { width: 120px; }
.w180 { width: 180px; }
</style>
