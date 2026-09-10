<template>
  <div>
    <px-table-page
      title="纪念品管理"
      subtitle="一期只做单件直购与到店选购，不扣减库存"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button type="primary" @click="openEdit()">新建纪念品</el-button>
      </template>

      <el-table-column label="图片" width="88">
        <template #default="{ row }">
          <el-image v-if="row.images?.length" :src="row.images[0]" fit="cover" class="thumb"
            :preview-src-list="row.images" preview-teleported />
          <span v-else class="muted">无图</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column label="价格" width="120" align="right">
        <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.price) }}</span></template>
      </el-table-column>
      <el-table-column label="库存备注" width="140">
        <template #default="{ row }">{{ row.stock_note || "—" }}</template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><PxStatusTag :value="row.status" kind="sale" /></template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <el-button text type="primary" @click="openEdit(row)">编辑</el-button>
          <el-button text :type="row.status === '在售' ? 'danger' : 'success'" @click="doToggle(row)">
            {{ row.status === "在售" ? "下架" : "上架" }}
          </el-button>
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="image" text="还没有上架的纪念品" hint="录入后将出现在小程序的纪念品列表" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="editVisible"
      :title="form.id ? '编辑纪念品' : '新建纪念品'"
      :saving="saving"
      @cancel="editVisible = false"
      @submit="save"
    >
      <el-form label-width="80px">
        <el-form-item label="名称"><el-input v-model="form.name" maxlength="50" /></el-form-item>
        <el-form-item label="价格"><el-input-number v-model="form.price" :min="0.01" :precision="2" class="w-full" /></el-form-item>
        <el-form-item label="图片URL">
          <el-input v-model="firstImage" placeholder="首图地址（一期图片URL直填）" />
        </el-form-item>
        <el-form-item label="描述"><el-input v-model="form.description" type="textarea" :rows="2" maxlength="200" /></el-form-item>
        <el-form-item label="库存备注"><el-input v-model="form.stock_note" placeholder="如：现货 5 件（不做扣减）" maxlength="100" /></el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage } from "element-plus";
import { createProduct, listProducts, toggleProduct, updateProduct } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxTablePage from "../../components/PxTablePage.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtMoney } from "../../utils/format";

const { rows, loading, failed, load } = useTable(listProducts);

const editVisible = ref(false);
const saving = ref(false);
const firstImage = ref("");
const form = ref({ id: null, name: "", price: 1, description: null, stock_note: null });

function openEdit(row) {
  form.value = row ? { ...row } : { id: null, name: "", price: 1, description: null, stock_note: null };
  firstImage.value = row?.images?.[0] || "";
  editVisible.value = true;
}

async function save() {
  if (!form.value.name) return ElMessage.warning("请填写名称");
  saving.value = true;
  try {
    const payload = { ...form.value, images: firstImage.value ? [firstImage.value] : [] };
    if (form.value.id) await updateProduct(form.value.id, payload);
    else await createProduct(payload);
    editVisible.value = false;
    ElMessage.success("已保存");
    load();
  } finally { saving.value = false; }
}

async function doToggle(row) {
  await toggleProduct(row.id);
  ElMessage.success(row.status === "在售" ? "已下架" : "已上架");
  load();
}
</script>

<style scoped>
.thumb { width: 48px; height: 48px; border-radius: var(--px-radius-sm); }
.muted { color: var(--px-text-4); }
.num { font-variant-numeric: tabular-nums; }
.w-full { width: 100%; }
</style>
