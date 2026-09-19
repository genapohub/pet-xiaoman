<!-- B-服务项目 ServiceItems（对齐画布 2:885）
     版式：B 端标准列表页；顶部为服务/加购 Tab，表格列为名称、价格、时长、体重分档、状态、价格版本、操作。
     新建/编辑使用右侧抽屉，价格变更与历史订单锁价分离。 -->
<template>
  <div>
    <px-table-page
      title="服务项目与价格"
      subtitle="改价会立即对 C 端公开生效，历史订单不受影响"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button type="primary" @click="openEdit()">
          <el-icon><Plus /></el-icon> 新建{{ activeTab }}
        </el-button>
      </template>

      <template #filters>
        <el-tabs v-model="activeTab" class="tabs" @tab-change="search">
          <el-tab-pane v-for="t in TABS" :key="t" :label="t" :name="t" />
        </el-tabs>
      </template>

      <el-table-column prop="name" label="名称" min-width="180" />
      <el-table-column label="价格" width="120" align="right">
        <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.price) }}</span></template>
      </el-table-column>
      <!-- 时长：画布要求列（「约 2 小时」「按里程」），自由文本，门店自己描述 -->
      <el-table-column label="时长" width="120">
        <template #default="{ row }">{{ row.duration_text || "—" }}</template>
      </el-table-column>
      <el-table-column label="体重分档" width="110">
        <template #default="{ row }">{{ row.weight_tier || "—" }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><PxStatusTag :value="row.status" kind="sale" /></template>
      </el-table-column>
      <el-table-column prop="version" label="价格版本" width="130" />
      <el-table-column label="操作" width="240" fixed="right">
        <template #default="{ row }">
          <PxActionButton label="编辑" :icon="EditPen" tone="primary" @click="openEdit(row)" />
          <PxActionButton label="版本" :icon="Clock" tip="查看价格版本历史" @click="showVersions(row)" />
          <PxActionButton
            v-if="row.status === '在售'"
            label="下架"
            :icon="Hide"
            tone="danger"
            tip="下架后 C 端不再展示"
            @click="doOffSale(row)"
          />
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="box" :text="`还没有${activeTab}项目`" hint="点右上角新建，录入名称与价格即可对外展示" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="editVisible"
      :title="form.id ? '编辑（改价将公开生效）' : '新建'"
      :subtitle="form.id ? '只影响新订单，历史订单继续使用原价格快照' : `新建${activeTab}后将同步给 C 端价格表`"
      :footer-hint="form.id && form.price !== originPrice ? '保存后会生成新的价格版本' : '请确认名称和价格对客户可读'"
      :icon="PriceTag"
      :saving="saving"
      :submit-text="form.id && form.price !== originPrice ? '保存并公开生效' : '保存'"
      @cancel="editVisible = false"
      @submit="save"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" maxlength="50" /></el-form-item>
        <el-form-item label="价格" prop="price"><el-input-number v-model="form.price" :min="0.01" :precision="2" class="w-full" /></el-form-item>
        <el-form-item label="时长" prop="duration_text">
          <div class="field-block">
            <el-input v-model="form.duration_text" maxlength="20" placeholder="如：约 2 小时 / 按里程" />
            <div class="hint">
              自由文本，不参与锁价计算。建议写门店能兑现的说法——
              善终服务受交通与仪式时长影响，写死分钟数容易与实际不符。
            </div>
          </div>
        </el-form-item>
        <el-form-item label="体重分档" prop="weight_tier">
          <el-select v-model="form.weight_tier" clearable placeholder="仅火化单项需要" class="w-full">
            <el-option v-for="t in ['0-10kg', '10-20kg', '20kg+']" :key="t" :label="t" :value="t" />
          </el-select>
        </el-form-item>
      </el-form>
    </px-form-drawer>

    <el-drawer v-model="versionVisible" title="价格版本历史" size="360px">
      <PxEmpty v-if="!versions.length" variant="doc" text="暂无历史版本" />
      <el-timeline v-else>
        <el-timeline-item v-for="v in versions" :key="v.version + v.created_at" :timestamp="fmtDateTime(v.created_at)">
          {{ v.version }} · ¥{{ fmtMoney(v.price) }}
        </el-timeline-item>
      </el-timeline>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Clock, EditPen, Hide, Plus, PriceTag } from "@element-plus/icons-vue";
import { createItem, listItems, listVersions, offSale, updateItem } from "../../api/service-item";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtDateTime, fmtMoney } from "../../utils/format";

const TABS = ["套餐", "单项", "加购"];
const activeTab = ref("套餐");

const { rows, loading, failed, load, search } = useTable(() => listItems(activeTab.value));

const editVisible = ref(false);
const versionVisible = ref(false);
const versions = ref([]);
const saving = ref(false);
const originPrice = ref(0);
const BLANK_FORM = { id: null, type: "套餐", name: "", price: 1, weight_tier: null, duration_text: null };
const form = ref({ ...BLANK_FORM });
const formRef = ref(null);
const rules = {
  name: [{ required: true, message: "请填写服务名称", trigger: "blur" }],
  price: [{ required: true, type: "number", min: 0.01, message: "价格需大于 0", trigger: "change" }],
};

function openEdit(row) {
  // 老数据可能没有 duration_text（本次迁移前建的项目）→ 用 BLANK_FORM 兜底，别让 undefined 进表单
  form.value = row ? { ...BLANK_FORM, ...row } : { ...BLANK_FORM, type: activeTab.value };
  originPrice.value = row ? row.price : 0;
  editVisible.value = true;
}

async function save() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    const payload = {
      type: form.value.type,
      name: form.value.name.trim(),
      price: form.value.price,
      weight_tier: form.value.weight_tier || null,
      // 空串统一转 null：留空表示「不承诺时长」，而不是存一个空字符串
      duration_text: (form.value.duration_text || "").trim() || null,
    };
    if (form.value.id) await updateItem(form.value.id, payload);
    else await createItem(payload);
    editVisible.value = false;
    ElMessage.success("已保存");
    load();
  } finally { saving.value = false; }
}

async function doOffSale(row) {
  try {
    await ElMessageBox.confirm(`确认下架「${row.name}」？C 端将不再展示该项目，历史订单不受影响。`, "下架服务项目", {
      type: "warning",
      confirmButtonText: "确认下架",
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
  await offSale(row.id);
  ElMessage.success("已下架（历史订单不受影响）");
  load();
}

async function showVersions(row) {
  versions.value = await listVersions(row.id);
  versionVisible.value = true;
}
</script>

<style scoped>
.tabs { margin-bottom: var(--px-sp-2); }
/* 「控件 + 说明」竖排块（Element 的 form-item content 默认横向 flex，不加包裹会挤一行） */
.field-block { width: 100%; }
.hint { margin-top: var(--px-sp-2); color: var(--px-text-3); font-size: var(--px-fs-xs); line-height: 1.6; }
.num { font-variant-numeric: tabular-nums; }
.w-full { width: 100%; }
</style>
