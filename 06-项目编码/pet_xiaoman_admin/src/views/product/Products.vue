<!-- B-纪念品 Products（对齐画布 2:937）
     版式：B 端标准列表页；表格列为图片、名称、分类、价格、库存备注、履约方式、状态、操作。
     库存仅做备注，不做扣减；邮寄能力和制作工期服务于 C 端确认订单分组。 -->
<template>
  <div>
    <px-table-page
      title="纪念品管理"
      subtitle="支持纪念清单下单与「到店自取 / 顺丰邮寄」两种履约，不扣减库存"
      :rows="rows"
      :loading="loading"
      :failed="failed"
      @retry="load"
    >
      <template #actions>
        <el-button type="primary" @click="openEdit()">
          <el-icon><Plus /></el-icon> 新建纪念品
        </el-button>
      </template>

      <el-table-column label="图片" width="88">
        <template #default="{ row }">
          <el-image v-if="row.images?.length" :src="row.images[0]" fit="cover" class="thumb"
            :preview-src-list="row.images" preview-teleported />
          <span v-else class="muted">无图</span>
        </template>
      </el-table-column>
      <el-table-column prop="name" label="名称" min-width="150" />
      <el-table-column label="分类" width="110">
        <template #default="{ row }">{{ row.category || "—" }}</template>
      </el-table-column>
      <el-table-column label="价格" width="120" align="right">
        <template #default="{ row }"><span class="num">¥{{ fmtMoney(row.price) }}</span></template>
      </el-table-column>
      <el-table-column label="库存备注" width="140">
        <template #default="{ row }">{{ row.stock_note || "—" }}</template>
      </el-table-column>
      <!-- 履约方式是门店最需要一眼看清的配置：开错会让客户看不到邮寄选项 -->
      <el-table-column label="履约方式" width="150">
        <template #default="{ row }">
          <div class="ful">
            <el-tag :type="row.ship_enabled ? 'success' : 'info'" size="small" effect="light">
              {{ row.ship_enabled ? "可邮寄" : "仅自取" }}
            </el-tag>
            <span class="muted lead">
              {{ row.lead_days > 0 ? `定制 ${row.lead_days} 天` : "现货" }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="90">
        <template #default="{ row }"><PxStatusTag :value="row.status" kind="sale" /></template>
      </el-table-column>
      <el-table-column label="操作" width="160" fixed="right">
        <template #default="{ row }">
          <PxActionButton label="编辑" :icon="EditPen" tone="primary" @click="openEdit(row)" />
          <PxActionButton
            :label="row.status === '在售' ? '下架' : '上架'"
            :icon="row.status === '在售' ? Hide : Top"
            :tone="row.status === '在售' ? 'danger' : 'success'"
            :tip="row.status === '在售' ? '下架后 C 端不再展示' : '上架后 C 端可见'"
            @click="doToggle(row)"
          />
        </template>
      </el-table-column>

      <template #empty>
        <PxEmpty variant="image" text="还没有上架的纪念品" hint="录入后将出现在小程序的纪念品列表" />
      </template>
    </px-table-page>

    <px-form-drawer
      v-model="editVisible"
      :title="form.id ? '编辑纪念品' : '新建纪念品'"
      :subtitle="form.id ? '调整图文、价格、履约方式或库存备注，会同步影响 C 端纪念品展示与结算选项' : '纪念品强调温情说明，避免写成促销商品'"
      footer-hint="图片建议使用温和实拍图，避免强营销海报；履约方式决定客户能否选择邮寄"
      :icon="Present"
      :saving="saving"
      @cancel="editVisible = false"
      @submit="save"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="80px">
        <el-form-item label="名称" prop="name"><el-input v-model="form.name" maxlength="50" /></el-form-item>
        <el-form-item label="分类" prop="category">
          <div class="field-block">
            <el-input v-model="form.category" maxlength="20" placeholder="如：纪念饰品 / 影像纪念 / 骨灰纪念" />
            <div class="hint">
              自由文本，用于后台归类与筛选；不填也可以（列表显示「—」）。
              不同门店卖的纪念品差异大，故不做固定枚举。
            </div>
          </div>
        </el-form-item>
        <el-form-item label="价格" prop="price"><el-input-number v-model="form.price" :min="0.01" :precision="2" class="w-full" /></el-form-item>
        <el-form-item label="图片URL" prop="image">
          <el-input v-model="firstImage" placeholder="首图地址（一期图片URL直填）" />
        </el-form-item>
        <el-form-item label="描述" prop="description"><el-input v-model="form.description" type="textarea" :rows="2" maxlength="200" /></el-form-item>
        <el-form-item label="库存备注" prop="stock_note"><el-input v-model="form.stock_note" placeholder="如：现货 5 件（不做扣减）" maxlength="100" /></el-form-item>
        <el-form-item label="履约方式" prop="ship_enabled">
          <div class="field-block">
            <el-switch v-model="form.ship_enabled" active-text="支持顺丰邮寄" inactive-text="仅到店自取" />
            <div class="hint">
              不开启时该纪念品<b>只能到店自取</b>；开启后客户在确认页可二选一。
              现货类建议到店自取（当场交付、免运费、无物流破损风险），
              刻字定制类建议开启邮寄（客户不必为一件小物再跑一趟）。
            </div>
          </div>
        </el-form-item>
        <el-form-item label="制作工期" prop="lead_days">
          <div class="field-block">
            <el-input-number v-model="form.lead_days" :min="0" :max="60" :step="1" />
            <div class="hint">
              0 = 现货，到店即可取；大于 0 表示定制（如刻字件 5 天），
              客户在确认页会看到「N 天后寄出」。
            </div>
          </div>
        </el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { EditPen, Hide, Plus, Present, Top } from "@element-plus/icons-vue";
import { createProduct, listProducts, toggleProduct, updateProduct } from "../../api/batch2";
import { useTable } from "../../composables/useTable";
import PxActionButton from "../../components/PxActionButton.vue";
import PxTablePage from "../../components/PxTablePage.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxStatusTag from "../../components/PxStatusTag.vue";
import { fmtMoney } from "../../utils/format";

const { rows, loading, failed, load } = useTable(listProducts);

// 新建时的履约默认值：仅到店自取 + 现货（最保守，避免误开邮寄让客户看到不存在的配送能力）
const BLANK_FORM = {
  id: null, name: "", price: 1, description: null, category: null, stock_note: null,
  ship_enabled: false, lead_days: 0,
};

const editVisible = ref(false);
const saving = ref(false);
const firstImage = ref("");
const form = ref({ ...BLANK_FORM });
const formRef = ref(null);
const urlPattern = /^$|^https?:\/\/.+|^\/uploads\/.+/i;
const rules = {
  name: [{ required: true, message: "请填写纪念品名称", trigger: "blur" }],
  price: [{ required: true, type: "number", min: 0.01, message: "价格需大于 0", trigger: "change" }],
  image: [{ validator: validateImage, trigger: "blur" }],
  description: [{ max: 200, message: "描述最多 200 字", trigger: "blur" }],
  stock_note: [{ max: 100, message: "库存备注最多 100 字", trigger: "blur" }],
};

function validateImage(_rule, _value, callback) {
  const value = firstImage.value.trim();
  if (!urlPattern.test(value)) return callback(new Error("图片地址需为 http(s) 地址或 /uploads/ 开头；不填也可以"));
  callback();
}

function openEdit(row) {
  // 老数据可能还没有这两个字段（本次迁移前建的商品），显式兜底而不是让 undefined 进表单
  form.value = row
    ? { ...BLANK_FORM, ...row, ship_enabled: Boolean(row.ship_enabled), lead_days: Number(row.lead_days || 0) }
    : { ...BLANK_FORM };
  firstImage.value = row?.images?.[0] || "";
  editVisible.value = true;
}

async function save() {
  await formRef.value?.validate();
  saving.value = true;
  try {
    const payload = {
      ...form.value,
      name: form.value.name.trim(),
      description: form.value.description?.trim() || null,
      category: (form.value.category || "").trim() || null,
      stock_note: form.value.stock_note?.trim() || null,
      images: firstImage.value.trim() ? [firstImage.value.trim()] : [],
      // 显式归一：el-switch 给 boolean、el-input-number 在清空时会变 null，
      // 直接透传会让后端 Pydantic 校验 422（lead_days 不接受 null）
      ship_enabled: Boolean(form.value.ship_enabled),
      lead_days: Number(form.value.lead_days || 0),
    };
    if (form.value.id) await updateProduct(form.value.id, payload);
    else await createProduct(payload);
    editVisible.value = false;
    ElMessage.success("已保存");
    load();
  } finally { saving.value = false; }
}

async function doToggle(row) {
  const nextAction = row.status === "在售" ? "下架" : "上架";
  try {
    await ElMessageBox.confirm(`确认${nextAction}「${row.name}」？${nextAction === "下架" ? "C 端将不再展示该纪念品。" : "C 端将恢复展示该纪念品。"}`, `${nextAction}纪念品`, {
      type: nextAction === "下架" ? "warning" : "success",
      confirmButtonText: `确认${nextAction}`,
      cancelButtonText: "取消",
    });
  } catch {
    return;
  }
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
/* 履约列：标签在上、工期在下，窄列里两行比一行挤着更好读 */
.ful { display: flex; flex-direction: column; align-items: flex-start; gap: 4px; }
.lead { font-size: var(--px-fs-xs); }
/* 表单里「控件 + 说明」的竖排块：Element 的 form-item content 默认横向 flex，
   不加这个包裹，说明文字会跟开关挤在同一行 */
.field-block { width: 100%; }
.hint {
  margin-top: var(--px-sp-2);
  color: var(--px-text-3);
  font-size: var(--px-fs-xs);
  line-height: 1.6;
}
</style>
