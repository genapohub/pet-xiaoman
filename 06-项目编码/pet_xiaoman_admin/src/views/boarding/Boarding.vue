<template>
  <div>
    <px-table-page
      title="骨灰寄存"
      :subtitle="expiringHint"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button type="primary" @click="registerVisible = true">登记寄存</el-button>
      </template>

      <el-table-column prop="pet_name" label="宠物" width="110" />
      <el-table-column label="位置" width="90">
        <template #default="{ row }">{{ row.location || "—" }}</template>
      </el-table-column>
      <el-table-column label="寄存日" width="110">
        <template #default="{ row }">{{ row.start_date || "—" }}</template>
      </el-table-column>
      <el-table-column label="到期日" width="110">
        <template #default="{ row }">{{ row.expire_date || "—" }}</template>
      </el-table-column>
      <el-table-column label="状态" width="160">
        <template #default="{ row }">
          <PxStatusTag :value="row.severity" kind="boarding" />
          <span class="days">{{ row.days_left }} 天</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="170" fixed="right">
        <template #default="{ row }">
          <template v-if="row.status !== '已取回'">
            <el-button text type="primary" @click="openRenew(row)">续存</el-button>
            <el-button text type="danger" @click="openTake(row)">取回</el-button>
          </template>
          <PxStatusTag v-else value="已取回" kind="sale" />
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="box" text="当前没有在寄存骨灰" hint="客户交付后登记位置与到期日，系统会提前提醒续存" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="registerVisible"
      title="登记寄存"
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
  </div>
</template>

<script setup>
import { computed, ref } from "vue";
import { ElMessage } from "element-plus";
import { createBoarding, listBoardings, renewBoarding, takeBoarding } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxTablePage from "../../components/PxTablePage.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";

const { rows, loading, failed, load } = useTable(listBoardings);

// 副标题直接说清今天的动作：几条到期要打电话
const expiringHint = computed(() => {
  const pending = rows.value.filter((r) => r.severity !== "正常" && r.status !== "已取回").length;
  return pending ? `${pending} 条需要联系家属（临期/已到期）` : `在寄存 ${rows.value.length} 份，状态正常`;
});

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
  await takeBoarding(currentId.value, takenBy.value);
  takeVisible.value = false;
  ElMessage.success("已取回");
  load();
}
</script>

<style scoped>
.days {
  margin-left: var(--px-sp-2);
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
}
.w-full { width: 100%; }
</style>
