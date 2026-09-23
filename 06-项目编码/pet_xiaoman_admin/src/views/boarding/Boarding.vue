<!-- B-骨灰寄存 Boarding（对齐画布 24:5）
     版式：B 端标准列表页。
     - 页头副标题动态提示临期数量；
     - 概览三卡：在寄存 / 7天内到期 / 已取回（画布 Summary 区）；
     - 表格列：宠物、位置、寄存日、到期日、状态（纯色文字，非标签）、操作；
     - 续存/取回用抽屉/弹窗完成，不新增独立页面。 -->
<template>
  <px-table-page class="tp-boarding"
    title="骨灰寄存"
    :subtitle="subtitle"
    :rows="rows"
    :loading="loading"
    :failed="failed"
    @retry="load"
  >
    <template #actions>
      <el-button type="primary" @click="registerVisible = true">
        <el-icon><Plus /></el-icon> 登记寄存
      </el-button>
    </template>

    <!-- 概览统计卡（对应画布 Summary 区） -->
    <template #summary>
      <div class="stat-row">
        <div class="stat-card">
          <span class="stat-card__v stat-card__v--pine">{{ stats.inStorage }}</span>
          <span class="stat-card__l">在寄存</span>
        </div>
        <div class="stat-card">
          <span class="stat-card__v stat-card__v--primary">{{ stats.expiring }}</span>
          <span class="stat-card__l">7天内到期</span>
        </div>
        <div class="stat-card">
          <span class="stat-card__v stat-card__v--ink">{{ stats.returned }}</span>
          <span class="stat-card__l">已取回</span>
        </div>
      </div>
    </template>

    <el-table-column prop="pet_name" label="宠物" min-width="110" />
    <el-table-column label="位置" min-width="90">
      <template #default="{ row }">{{ row.location || "—" }}</template>
    </el-table-column>
    <el-table-column label="寄存日" min-width="120">
      <template #default="{ row }">{{ row.start_date || "—" }}</template>
    </el-table-column>
    <el-table-column label="到期日" min-width="120">
      <template #default="{ row }">{{ row.expire_date || "—" }}</template>
    </el-table-column>
    <el-table-column label="状态" min-width="100">
      <template #default="{ row }">
        <span class="b-status" :class="statusClass(row)">{{ statusText(row) }}</span>
      </template>
    </el-table-column>
    <el-table-column label="操作" width="160" fixed="right">
      <template #default="{ row }">
        <span v-if="row.status !== '已取回'" class="b-op">
          <el-button link type="primary" @click="openRenew(row)">续存</el-button>
          <i class="b-op__sep">·</i>
          <el-button link type="primary" @click="openTake(row)">取回</el-button>
        </span>
        <span v-else class="b-op--dash">—</span>
      </template>
    </el-table-column>

    <template #empty>
      <px-empty variant="boarding" text="当前没有在寄存骨灰" hint="客户交付后登记位置与到期日，系统会提前提醒续存" />
    </template>
  </px-table-page>

  <px-form-drawer
    v-model="registerVisible"
    title="登记寄存"
    subtitle="记录寄存位置和到期日，系统会提前提示联系家属"
    footer-hint="位置建议使用货架编号，如 A-01"
    :icon="Box"
    @cancel="registerVisible = false"
    @submit="doRegister"
  >
    <el-form label-width="80px">
      <el-form-item label="宠物"><el-input-number v-model="form.pet_id" :min="1" class="w-full" placeholder="宠物ID" /></el-form-item>
      <el-form-item label="客户"><el-input-number v-model="form.customer_id" :min="1" class="w-full" placeholder="客户ID" /></el-form-item>
      <el-form-item label="位置"><el-input v-model="form.location" placeholder="如 A-01" /></el-form-item>
      <el-form-item label="到期日"><el-date-picker v-model="form.expire_date" value-format="YYYY-MM-DD" class="w-full" /></el-form-item>
    </el-form>
  </px-form-drawer>

  <el-dialog v-model="renewVisible" title="续存" width="360px">
    <el-date-picker v-model="renewDate" value-format="YYYY-MM-DD" class="w-full" />
    <template #footer>
      <el-button @click="renewVisible = false">取消</el-button>
      <el-button type="primary" @click="doRenew">确认续存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="takeVisible" title="取回确认" width="360px">
    <el-input v-model="takenBy" placeholder="取回人（必填）" />
    <template #footer>
      <el-button @click="takeVisible = false">取消</el-button>
      <el-button type="danger" @click="doTake">确认取回</el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Box, Plus } from "@element-plus/icons-vue";
import { createBoarding, listBoardings, renewBoarding, takeBoarding } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxTablePage from "../../components/PxTablePage.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxEmpty from "../../components/PxEmpty.vue";

const { rows, loading, failed, load } = useTable(listBoardings);

// 概览三卡：直接由列表数据派生（无需额外接口）
const stats = computed(() => {
  const all = rows.value || [];
  const active = all.filter((r) => r.status !== "已取回");
  return {
    inStorage: active.length,
    expiring: active.filter((r) => r.severity === "临期" || r.severity === "已到期").length,
    returned: all.filter((r) => r.status === "已取回").length,
  };
});

// 副标题动态提示临期数量（画布：安心托管 · N 个寄存将在 7 天内到期）
const subtitle = computed(() =>
  stats.value.expiring
    ? `安心托管 · ${stats.value.expiring} 个寄存将在 7 天内到期`
    : "安心托管 · 当前寄存状态平稳"
);

// 状态列：纯色文字，对照画布 在寄存(深松绿) / 临期(陶土橙) / 已到期(红) / 已取回(灰)
function statusText(row) {
  if (row.status === "已取回") return "已取回";
  if (row.severity === "临期") return "临期";
  if (row.severity === "已到期") return "已到期";
  return "在寄存";
}
function statusClass(row) {
  if (row.status === "已取回") return "b-status--returned";
  if (row.severity === "已到期") return "b-status--due";
  if (row.severity === "临期") return "b-status--soon";
  return "b-status--active";
}

const registerVisible = ref(false);
const renewVisible = ref(false);
const takeVisible = ref(false);
const currentId = ref(null);
const renewDate = ref("");
const takenBy = ref("");
const form = ref({ pet_id: 1, customer_id: 1, location: "", expire_date: "" });

function openRenew(row) { currentId.value = row.id; renewDate.value = row.expire_date; renewVisible.value = true; }
function openTake(row) { currentId.value = row.id; takenBy.value = ""; takeVisible.value = true; }

async function doRegister() {
  if (!form.value.location || !form.value.expire_date) return ElMessage.warning("请填写位置与到期日");
  await createBoarding(form.value);
  registerVisible.value = false;
  ElMessage.success("已登记");
  load();
}
async function doRenew() {
  await renewBoarding(currentId.value, renewDate.value);
  renewVisible.value = false;
  ElMessage.success("已续存");
  load();
}
async function doTake() {
  if (!takenBy.value) return ElMessage.warning("请填写取回人");
  try {
    await ElMessageBox.confirm("确认骨灰已完成取回？该状态会影响后续续存提醒。", "确认取回", {
      type: "warning",
      confirmButtonText: "确认取回",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  await takeBoarding(currentId.value, takenBy.value);
  takeVisible.value = false;
  ElMessage.success("已取回");
  load();
}
</script>

<style scoped>
/* 概览统计卡（画布 Summary 区：三等分、白底、#ECE9E3 描边、radius 14、柔影） */
.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--px-sp-4);
}
.stat-card {
  display: flex;
  flex-direction: column;
  gap: var(--px-sp-1);
  padding: 16px 18px;
  background: var(--px-bg-card);
  border: 1px solid #ECE9E3;
  border-radius: var(--px-radius-lg);
  box-shadow: var(--px-shadow-card-soft);
}
.stat-card__v {
  font-family: var(--px-font-serif);
  font-weight: 600;
  font-size: 24px;
  line-height: 1.1;
  font-variant-numeric: tabular-nums;
}
.stat-card__v--pine { color: var(--px-primary-pressed); } /* 在寄存：深松绿 */
.stat-card__v--primary { color: var(--px-primary); }      /* 7天内到期：松绿 */
.stat-card__v--ink { color: var(--px-text-1); }           /* 已取回：墨 */
.stat-card__l {
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
}

/* 状态列：纯色文字（非标签） */
.b-status { font-size: var(--px-fs-base); font-weight: 500; }
.b-status--active { color: var(--px-primary-pressed); } /* 在寄存：深松绿 */
.b-status--soon { color: var(--px-chart-2); }            /* 临期：陶土橙 */
.b-status--due { color: var(--px-error); }               /* 已到期：告警红 */
.b-status--returned { color: var(--px-text-3); }         /* 已取回：灰 */

/* 操作列：续存 · 取回（画布为松绿 Medium 文字链） */
.b-op { display: inline-flex; align-items: center; gap: var(--px-sp-1); }
.b-op :deep(.el-button) { padding: 0 4px; font-weight: 500; }
.b-op__sep { color: var(--px-text-4); font-style: normal; }
.b-op--dash { color: var(--px-text-4); }

/* 行高对齐画布：表头 48 / 数据行 56 */
:deep(.el-table th.el-table__cell) { height: 48px; }
:deep(.el-table td.el-table__cell) { height: 56px; }

.w-full { width: 100%; }
</style>
