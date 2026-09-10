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
        <el-button type="primary" @click="openEdit()">新建{{ activeTab }}</el-button>
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
      <el-table-column label="体重分档" width="110">
        <template #default="{ row }">{{ row.weight_tier || "—" }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><PxStatusTag :value="row.status" kind="sale" /></template>
      </el-table-column>
      <el-table-column prop="version" label="价格版本" width="130" />
      <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button text @click="showVersions(row)">版本</el-button>
          <el-button text type="danger" v-if="row.status === '在售'" @click="doOffSale(row)">下架</el-button>
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="box" :text="`还没有${activeTab}项目`" hint="点右上角新建，录入名称与价格即可对外展示" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="editVisible"
      :title="form.id ? '编辑（改价将公开生效）' : '新建'"
      :saving="saving"
      :submit-text="form.id && form.price !== originPrice ? '保存并公开生效' : '保存'"
      @cancel="editVisible = false"
      @submit="save"
    >
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" maxlength="50" /></el-form-item>
        <el-form-item label="价格"><el-input-number v-model="form.price" :min="0.01" :precision="2" class="w-full" /></el-form-item>
        <el-form-item label="体重分档">
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
import { ElMessage } from "element-plus";
import { createItem, listItems, listVersions, offSale, updateItem } from "../../api/service-item";
import { useTable } from "../../composables/useTable";
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
const form = ref({ id: null, type: "套餐", name: "", price: 1, weight_tier: null });

function openEdit(row) {
  form.value = row ? { ...row } : { id: null, type: activeTab.value, name: "", price: 1, weight_tier: null };
  originPrice.value = row ? row.price : 0;
  editVisible.value = true;
}

async function save() {
  if (!form.value.name) return ElMessage.warning("请填写名称");
  saving.value = true;
  try {
    const payload = { type: form.value.type, name: form.value.name,
                      price: form.value.price, weight_tier: form.value.weight_tier };
    if (form.value.id) await updateItem(form.value.id, payload);
    else await createItem(payload);
    editVisible.value = false;
    ElMessage.success("已保存");
    load();
  } finally { saving.value = false; }
}

async function doOffSale(row) {
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
.num { font-variant-numeric: tabular-nums; }
.w-full { width: 100%; }
</style>
