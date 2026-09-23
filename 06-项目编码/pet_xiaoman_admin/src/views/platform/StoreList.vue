<!-- B-平台门店列表 StoreList（对齐画布 2:1118；开通门店抽屉对齐 5:5）
     版式：超管标准列表页，无独立页标题（画布此页无 PageHead）。
     结构：范围说明条 → 经营概览 4 卡 → 筛选工具条（状态分段 + 开通门店）→ 门店表格卡。
     数据全部来自后端 listStores()（_store_dict 返回 store_id/name/status/profile/manager_count/staff_count）。

     不虚构说明：
     - 画布 note-scope 原文含「【后端待对齐】需将 stats 加入超管 menus 方可放行 /stats 路由」等
       设计标注，属开发团队 TODO、非用户文案，故上线文案只保留范围说明，删去实现注解。
     - 概览与筛选计数均由后端真实 rows 派生，不写死画布示例数字（5/4/3/2）。 -->
<template>
  <div class="store-list">
    <!-- 范围说明条 -->
    <div class="scope-note">
      超管平台管理台 · 左侧菜单：数据看板 + 门店管理；开通门店为独立页；门店账号位于门店详情。
    </div>

    <!-- 经营概览 -->
    <div class="store-overview" aria-label="门店开通概览">
      <section
        v-for="item in storeOverview"
        :key="item.label"
        class="overview-card"
        :class="item.tone ? `overview-card--${item.tone}` : ''"
      >
        <span class="overview-card__label">{{ item.label }}</span>
        <strong class="overview-card__value">{{ item.value }}</strong>
        <span class="overview-card__hint">{{ item.hint }}</span>
      </section>
    </div>

    <!-- 工具条：状态分段筛选 + 开通门店 -->
    <div class="store-toolbar">
      <div class="seg">
        <button
          v-for="t in filters"
          :key="t.key"
          type="button"
          class="seg__item"
          :class="{ 'is-active': activeFilter === t.key }"
          @click="activeFilter = t.key"
        >
          {{ t.label }} {{ t.count }}
        </button>
      </div>
      <el-button class="store-add" @click="openCreate">
        <el-icon><Plus /></el-icon> 开通门店
      </el-button>
    </div>

    <!-- 门店表格卡 -->
    <div class="store-table-card">
      <el-table
        :data="filteredRows"
        v-loading="loading"
        class="clickable"
        @row-click="(row) => goDetail(row)"
      >
        <el-table-column label="门店" min-width="240">
          <template #default="{ row }">
            <div class="cell-main">
              <span class="cell-name">{{ row.name }}</span>
              <span v-if="brandName(row) !== row.name" class="cell-sub">对外：{{ brandName(row) }}</span>
              <span v-else class="cell-sub muted">对外名同内部名</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="C 端入口" min-width="150">
          <template #default="{ row }">
            <span v-if="row.profile?.slug" class="slug">{{ row.profile.slug }}</span>
            <span v-else class="muted">未配品牌</span>
          </template>
        </el-table-column>

        <el-table-column label="独立小程序" min-width="130">
          <template #default="{ row }">
            <span v-if="row.profile?.miniapp_appid" class="cell-sub">
              {{ row.profile.miniapp_appid }}·{{ row.profile.miniapp_entry_enabled ? "已启用" : "已关闭" }}
            </span>
            <span v-else class="muted">未绑定 AppID</span>
          </template>
        </el-table-column>

        <el-table-column label="主色" width="96">
          <template #default="{ row }">
            <div class="swatch-cell">
              <span class="swatch" :style="{ background: color(row) }" />
              <span class="mono">{{ color(row) }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="账号" min-width="170">
          <template #default="{ row }">
            <span>{{ row.staff_count }} 个</span>
            <span v-if="row.manager_count === 0" class="warn">· 待补店长</span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <span v-if="row.status === 'active'" class="status--on">营业中</span>
            <span v-else class="status--off">已停用</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" min-width="150" fixed="right">
          <template #default="{ row }">
            <div class="ops">
              <px-action-button
                label="账号与品牌"
                :icon="Setting"
                tone="primary"
                tip="配置该店品牌、UI 与登录账号"
                @click="goDetail(row)"
              />
              <px-action-button
                v-if="row.status === 'active'"
                label="停用"
                :icon="Hide"
                tone="danger"
                tip="停用后 C 端按该店标识访问一律 404，后台数据保留"
                @click="doStatus(row, 'disabled')"
              />
              <px-action-button
                v-else
                label="启用"
                :icon="Check"
                tone="success"
                tip="恢复该店 C 端接单"
                @click="doStatus(row, 'active')"
              />
            </div>
          </template>
        </el-table-column>

        <template #empty>
          <px-empty
            variant="store"
            text="还没有门店"
            hint="点右上角「开通门店」，一次填完门店信息、品牌与首位店长账号"
          />
        </template>
      </el-table>
    </div>

    <!-- 开通门店抽屉 -->
    <px-form-drawer
      v-model="createVisible"
      title="开通门店"
      desc="一次建好门店、品牌与首位店长。提交后该店长即可登录自己的后台"
      :footer-hint="`店长账号：${form.admin_username || '—'}，请创建后转告并催其改密`"
      :icon="Shop"
      :saving="saving"
      size="520px"
      submit-text="开通并去配置"
      @cancel="createVisible = false"
      @submit="save"
    >
      <el-form label-width="104px">
        <div class="group">门店</div>
        <el-form-item label="门店名称">
          <el-input v-model="form.store_name" maxlength="50" placeholder="内部使用，如：喵星人善终（郑州店）" />
        </el-form-item>
        <el-form-item label="C 端标识">
          <el-input v-model="form.slug" maxlength="50" placeholder="英文/数字/短横线，如 meow" />
          <span class="field-hint">小程序按此标识认门店 —— 建后不建议再改（改了对不上已发出的码）</span>
        </el-form-item>

        <div class="group">品牌与 UI（可留空，之后在详情页再调）</div>
        <el-form-item label="对外店名">
          <el-input v-model="form.brand_name" maxlength="50" placeholder="C 端展示店名，留空同门店名称" />
        </el-form-item>
        <el-form-item label="标语">
          <el-input v-model="form.slogan" maxlength="50" placeholder="如：给 ta 最后的体面（留空不展示）" />
        </el-form-item>
        <el-form-item label="主色">
          <el-color-picker v-model="form.primary_color" />
          <span class="mono sw-xs">{{ form.primary_color }}</span>
          <span class="field-hint">其余色阶由此派生（按钮 / 渐变 / 选中态）</span>
        </el-form-item>
        <el-form-item label="Logo 地址">
          <el-input v-model="form.logo_url" placeholder="站内路径 /uploads/logo.png 或 http(s) 地址" />
        </el-form-item>

        <div class="group">联系信息（C 端展示）</div>
        <el-form-item label="联系电话">
          <el-input v-model="form.contact_phone" maxlength="20" placeholder="如 0371-66668888 或 13800000000" />
        </el-form-item>
        <el-form-item label="门店地址">
          <el-input v-model="form.contact_address" maxlength="120" placeholder="C 端展示的门店地址" />
        </el-form-item>
        <el-form-item label="营业时间">
          <el-input v-model="form.business_hours" maxlength="50" placeholder="如 24 小时可约" />
        </el-form-item>

        <div class="group">独立小程序入口（可后补）</div>
        <el-form-item label="小程序名称">
          <el-input v-model="form.miniapp_name" maxlength="50" placeholder="微信侧可搜索的小程序名称，留空同对外店名" />
        </el-form-item>
        <el-form-item label="小程序 AppID">
          <el-input v-model="form.miniapp_appid" maxlength="64" placeholder="如 wx6677e0d8dd0ffb，暂未申请可留空" />
        </el-form-item>
        <el-form-item label="默认入口">
          <el-switch v-model="form.miniapp_entry_enabled" active-text="启用" inactive-text="关闭" />
          <span class="field-hint">启用后，微信搜索进入该 AppID 时默认绑定本门店；扫码参数仍可临时切到其他门店</span>
        </el-form-item>

        <div class="group">首位店长账号</div>
        <el-form-item label="店长姓名">
          <el-input v-model="form.admin_name" maxlength="50" placeholder="如：王店长" />
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input v-model="form.admin_username" maxlength="32" placeholder="全平台唯一，如 meow_boss" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="form.admin_password" maxlength="32" placeholder="至少 6 位" />
        </el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { computed, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Check, Hide, Plus, Setting, Shop } from "@element-plus/icons-vue";
import { createStore, listStores, setStoreStatus } from "../../api/platform";
import { useTable } from "../../composables/useTable";
import { DEFAULT_PRIMARY } from "../../utils/theme";
import PxActionButton from "../../components/PxActionButton.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";

const router = useRouter();
const { rows, loading, failed, load } = useTable(() => listStores());

const activeFilter = ref("all");
const filters = computed(() => {
  const list = rows.value || [];
  const active = list.filter((i) => i.status === "active").length;
  return [
    { key: "all", label: "全部", count: list.length },
    { key: "active", label: "营业中", count: active },
    { key: "disabled", label: "已停用", count: list.length - active },
  ];
});

const filteredRows = computed(() => {
  const list = rows.value || [];
  if (activeFilter.value === "all") return list;
  return list.filter((i) => i.status === activeFilter.value);
});

const storeOverview = computed(() => {
  const list = rows.value || [];
  const active = list.filter((i) => i.status === "active").length;
  const noManager = list.filter((i) => i.manager_count === 0).length;
  const miniappReady = list.filter((i) => i.profile?.miniapp_appid).length;
  return [
    { label: "门店总数", value: list.length, hint: "平台已开通门店" },
    { label: "营业中", value: active, hint: "C 端可正常接单", tone: "success" },
    { label: "独立小程序", value: miniappReady, hint: "已绑定 AppID 的门店", tone: "primary" },
    { label: "待补店长", value: noManager, hint: noManager ? "需尽快补齐账号" : "账号配置完整", tone: noManager ? "warning" : "success" },
  ];
});

const createVisible = ref(false);
const saving = ref(false);

const blank = () => ({
  store_name: "", slug: "", brand_name: "", slogan: "",
  primary_color: DEFAULT_PRIMARY, logo_url: "",
  contact_phone: "", contact_address: "", business_hours: "",
  miniapp_name: "", miniapp_appid: "", miniapp_entry_enabled: true,
  admin_name: "店长", admin_username: "", admin_password: "",
});
const form = reactive(blank());

const brandName = (row) => row.profile?.name || row.name;
const color = (row) => row.profile?.primary_color || DEFAULT_PRIMARY;

function openCreate() {
  Object.assign(form, blank());
  createVisible.value = true;
}

const SLUG_RE = /^[A-Za-z0-9_-]{2,50}$/;

async function save() {
  if (!form.store_name.trim()) return ElMessage.warning("请填写门店名称");
  if (!SLUG_RE.test(form.slug.trim())) {
    return ElMessage.warning("C 端标识只能用小写字母、数字、短横线或下划线，2-50 位");
  }
  if (!form.admin_username.trim()) return ElMessage.warning("请填写店长登录账号");
  if ((form.admin_password || "").length < 6) return ElMessage.warning("初始密码至少 6 位");

  saving.value = true;
  try {
    const created = await createStore({
      store_name: form.store_name.trim(),
      slug: form.slug.trim(),
      brand_name: form.brand_name.trim() || null,
      slogan: form.slogan.trim() || null,
      primary_color: form.primary_color,
      logo_url: form.logo_url.trim() || null,
      contact_phone: form.contact_phone.trim() || null,
      contact_address: form.contact_address.trim() || null,
      business_hours: form.business_hours.trim() || null,
      miniapp_name: form.miniapp_name.trim() || null,
      miniapp_appid: form.miniapp_appid.trim() || null,
      miniapp_entry_enabled: form.miniapp_entry_enabled,
      admin_username: form.admin_username.trim(),
      admin_password: form.admin_password,
      admin_name: form.admin_name.trim() || "店长",
    });
    createVisible.value = false;
    ElMessage.success(`门店已开通，C 端入口标识：${created.store.profile.slug}`);
    router.push(`/stores/${created.store.store_id}`);
  } finally {
    saving.value = false;
  }
}

async function doStatus(row, status) {
  const off = status === "disabled";
  try {
    await ElMessageBox.confirm(
      off
        ? `停用「${row.name}」后，C 端用标识 ${row.profile?.slug || "—"} 访问会直接 404（不再接单），后台数据与账号都会保留。确认停用？`
        : `启用「${row.name}」后，该门店 C 端恢复接单。确认启用？`,
      off ? "停用门店" : "启用门店",
      { type: "warning", confirmButtonText: off ? "确认停用" : "确认启用", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  await setStoreStatus(row.store_id, status);
  ElMessage.success(off ? "门店已停用" : "门店已启用");
  load();
}

function goDetail(row) {
  router.push(`/stores/${row.store_id}`);
}
</script>

<style scoped>
.store-list {
  display: flex;
  flex-direction: column;
}

/* 范围说明条 */
.scope-note {
  background: var(--px-primary-light);
  border-radius: 10px;
  padding: 9px 12px;
  margin-bottom: var(--px-sp-4);
  color: #3D5C57;
  font-size: 12px;
  line-height: 1.6;
}

/* 经营概览 */
.store-overview {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--px-sp-3);
  margin-bottom: var(--px-sp-4);
}
.overview-card {
  display: grid;
  gap: 6px;
  height: 88px;
  box-sizing: border-box;
  padding: 16px;
  border: 1px solid #ECE9E3;
  border-radius: 14px;
  background: var(--px-bg-card);
}
.overview-card__label {
  color: var(--px-text-2);
  font-size: 12px;
  font-weight: 600;
}
.overview-card__value {
  color: var(--px-text-1);
  font-size: 22px;
  line-height: 1.1;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
}
.overview-card__hint {
  color: var(--px-text-3);
  font-size: 11px;
}
.overview-card--primary { border-color: rgba(91, 140, 133, 0.22); }
.overview-card--success { border-color: rgba(64, 158, 111, 0.22); }
.overview-card--warning { border-color: rgba(217, 139, 43, 0.26); background: var(--px-bg-warning); }

/* 工具条 */
.store-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--px-sp-4);
  margin-bottom: var(--px-sp-4);
}
.seg {
  display: flex;
  align-items: center;
  gap: var(--px-sp-1);
}
.seg__item {
  border: none;
  background: transparent;
  border-radius: 999px;
  padding: 7px 14px;
  height: 32px;
  cursor: pointer;
  font-family: inherit;
  font-size: 13px;
  font-weight: 400;
  color: var(--px-text-2);
  transition: background-color var(--px-motion-fast) linear, color var(--px-motion-fast) linear;
}
.seg__item:hover { background: var(--px-bg-hover); }
.seg__item.is-active {
  background: var(--px-primary-light);
  color: #3D5C57;
  font-weight: 500;
}
.store-add {
  border-radius: 8px;
  height: 34px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 500;
}

/* 表格卡 */
.store-table-card {
  background: var(--px-bg-card);
  border: 1px solid #ECE9E3;
  border-radius: var(--px-radius-xl);
  box-shadow: var(--px-shadow-card-soft);
  overflow: hidden;
}
.store-table-card :deep(.el-table) {
  border: none;
  border-radius: 0;
  box-shadow: none;
}
.store-table-card :deep(.el-table th.el-table__cell) {
  padding: 14px 20px;
  background: var(--px-bg-paper);
}
.store-table-card :deep(.el-table td.el-table__cell) {
  padding: 15px 20px;
}
.store-table-card :deep(.el-table .cell) {
  padding-left: 0;
  padding-right: 0;
}

/* 单元格 */
.cell-main { display: flex; flex-direction: column; line-height: 1.35; gap: 2px; }
.cell-name { font-weight: 600; color: var(--px-text-1); font-size: 14px; }
.cell-sub { font-size: 12px; color: var(--px-text-2); }
.muted { color: var(--px-text-3); font-size: 13px; }
.slug {
  padding: 1px var(--px-sp-1);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-sm);
  background: var(--px-bg-warm);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
}
.warn {
  margin-left: var(--px-sp-1);
  font-size: 13px;
  color: var(--px-chart-2);
}
.mono { font-variant-numeric: tabular-nums; font-size: 12px; color: var(--px-text-2); }
.swatch-cell { display: flex; align-items: center; gap: var(--px-sp-1); }
.swatch {
  width: 14px;
  height: 14px;
  flex-shrink: 0;
  border: 1px solid var(--px-border);
  border-radius: 4px;
}
.sw-xs { margin-left: var(--px-sp-1); }
.status--on { color: var(--px-primary); font-size: 13px; }
.status--off { color: var(--px-text-3); font-size: 13px; }
.ops { display: flex; align-items: center; gap: var(--px-sp-2); flex-wrap: wrap; }

.group {
  margin: var(--px-sp-4) 0 var(--px-sp-2);
  padding-bottom: var(--px-sp-1);
  border-bottom: 1px dashed var(--px-border);
  color: var(--px-primary-pressed);
  font-size: var(--px-fs-xs);
  font-weight: 700;
}
.group:first-child { margin-top: 0; }
.field-hint {
  display: block;
  width: 100%;
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
  line-height: 1.5;
}
</style>
