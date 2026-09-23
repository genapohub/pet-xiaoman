<!-- B-平台门店详情 StoreDetail（对齐画布 门店详情三 Tab：品牌与UI / 小程序入口 / 门店账号）。
     版式：页头（店名 + slug｜账号数 + 营业状态 + 编辑资料/停用/启用）＋ 概览四卡 ＋ 三 Tab。
     平台超管维护白标品牌、独立小程序入口和账号；门店端不可自行修改品牌（租户写恒 403）。 -->
<template>
  <div class="store-detail">
    <PxPageHeader
      :title="store?.name || '门店'"
      :subtitle="subtitle"
      back
    >
      <template #actions>
        <span class="status-badge" :class="store?.status === 'active' ? 'is-on' : 'is-off'">
          {{ store?.status === "active" ? "营业中" : "已停用" }}
        </span>
        <el-button v-if="store?.status === 'active'" @click="goBrand">
          <el-icon><Edit /></el-icon> 编辑资料
        </el-button>
        <el-button
          v-if="store?.status === 'active'"
          type="danger" plain
          @click="doStatus('disabled')"
        >
          停用门店
        </el-button>
        <el-button v-else-if="store" type="primary" @click="doStatus('active')">启用门店</el-button>
      </template>
    </PxPageHeader>

    <PxErrorState v-if="failed" text="门店信息加载失败" :loading="loading" @retry="load" />

    <template v-else>
      <!-- 概览四卡：品牌白标 / 门店联系 / 独立小程序 / 后台账号 -->
      <div v-if="store" class="summary-row" aria-label="门店配置概览">
        <section
          v-for="item in storeSummary"
          :key="item.label"
          class="summary-card"
          :class="item.done ? 'summary-card--done' : 'summary-card--todo'"
        >
          <div class="summary-card__top">
            <span>{{ item.label }}</span>
            <span class="summary-card__tag">{{ item.done ? "已就绪" : "待完善" }}</span>
          </div>
          <strong>{{ item.value }}</strong>
          <p>{{ item.hint }}</p>
        </section>
      </div>

      <!-- 三 Tab 导航（画布药丸样式） -->
      <div class="tab-nav">
        <button class="tab-nav__item" :class="{ active: tab === 'brand' }" @click="tab = 'brand'">品牌与UI</button>
        <button class="tab-nav__item" :class="{ active: tab === 'miniapp' }" @click="tab = 'miniapp'">小程序入口</button>
        <button class="tab-nav__item" :class="{ active: tab === 'staff' }" @click="tab = 'staff'">门店账号</button>
      </div>

      <!-- Tab 1：品牌与UI -->
      <section v-show="tab === 'brand'" class="tab-panel">
        <div class="note-tab">门店详情 · 品牌与UI Tab · 品牌资产由平台统一配置，门店端只读（租户写恒 403）</div>
        <div class="detail-grid">
          <section class="card form-card">
            <h3 class="card__title">品牌白标</h3>

            <div class="logo-row">
              <div class="logo-box">
                <img v-if="brand.logo_url && !broken" :src="mediaUrl(brand.logo_url)" alt="品牌 Logo" @error="broken = true" />
                <template v-else><span>爪印</span><span>Logo</span></template>
              </div>
              <div class="logo-hint">
                <div class="logo-hint__t">上传品牌 Logo</div>
                <div class="logo-hint__s">建议 PNG 透明底，480×480 以上</div>
                <div class="logo-hint__actions">
                  <el-upload
                    class="logo-upload"
                    action="#"
                    :auto-upload="false"
                    :show-file-list="false"
                    accept="image/png,image/jpeg,image/webp"
                    :on-change="onLogoChange"
                  >
                    <el-button :icon="Upload">{{ brand.logo_url ? "更换 Logo" : "选择图片" }}</el-button>
                  </el-upload>
                  <el-button v-if="brand.logo_url" text type="danger" :icon="Delete" @click="clearLogo">移除</el-button>
                </div>
              </div>
            </div>

            <div class="form-row">
              <div class="field">
                <label>门店名称</label>
                <el-input v-model="brand.name" maxlength="50" placeholder="门店名称" />
              </div>
              <div class="field">
                <label>品牌标语</label>
                <el-input v-model="brand.slogan" maxlength="50" placeholder="品牌标语" />
              </div>
            </div>

            <div class="form-row">
              <div class="field">
                <label>品牌主色</label>
                <div class="swatch-row">
                  <el-color-picker v-model="brand.primary_color" />
                  <span class="swatch-hex">{{ brand.primary_color }}</span>
                </div>
              </div>
              <div class="field">
                <label>辅助色</label>
                <div class="swatch-row">
                  <el-color-picker v-model="brand.secondary" />
                  <span class="swatch-hex">{{ brand.secondary }}</span>
                  <span class="field__hint">仅本地预览，暂未接入后端</span>
                </div>
              </div>
            </div>

            <div class="action-bar">
              <el-button @click="resetBrand">取消</el-button>
              <el-button type="primary" :loading="brandSaving" @click="saveBrand">保存</el-button>
            </div>
          </section>

          <section class="card preview-card">
            <h3 class="card__title">C 端换肤预览</h3>
            <div class="preview-mock">
              <div class="preview-mock__bar" :style="{ background: brand.primary_color }" />
              <div class="preview-mock__body">
                <div class="preview-mock__logo" :style="{ background: brand.primary_color }">
                  <img v-if="brand.logo_url && !broken" :src="mediaUrl(brand.logo_url)" alt="logo" @error="broken = true" />
                  <template v-else>{{ initial }}</template>
                </div>
                <div class="preview-mock__name">{{ brand.name || "门店名称" }}</div>
                <div class="preview-mock__slogan">{{ brand.slogan || "品牌标语预览" }}</div>
                <button class="preview-mock__btn" :style="{ background: brand.primary_color }">主行动按钮</button>
                <button
                  class="preview-mock__btn preview-mock__btn--ghost"
                  :style="{ color: brand.secondary, borderColor: brand.secondary }"
                >次行动按钮</button>
              </div>
            </div>
            <p class="preview-note">保存后 C 端小程序按此配置实时换肤（logo / 主色 / 店名 / 标语）。</p>
          </section>
        </div>
      </section>

      <!-- Tab 2：小程序入口 -->
      <section v-show="tab === 'miniapp'" class="tab-panel">
        <div class="note-tab">门店详情 · 小程序入口 Tab · 查看独立小程序状态、入口路径与二维码</div>
        <div class="detail-grid">
          <div class="detail-grid__left">
            <section class="card info-card">
              <h3 class="card__title">小程序信息</h3>
              <div class="kv"><span class="kv__k">AppID</span><span class="kv__v">{{ miniappAppid || "未配置" }}</span></div>
              <div class="kv">
                <span class="kv__k">运行状态</span>
                <span class="kv__v">
                  <span class="status-badge" :class="miniappEntryEnabled ? 'is-on' : 'is-off'">
                    {{ miniappEntryEnabled ? "已上线" : "未上线" }}
                  </span>
                </span>
              </div>
              <div class="kv"><span class="kv__k">所属门店</span><span class="kv__v">{{ storeName }}</span></div>
            </section>

            <section class="card path-card">
              <h3 class="card__title">页面路径</h3>
              <div v-for="p in miniappPaths" :key="p.path" class="kv">
                <span class="kv__k">{{ p.label }}</span>
                <code class="kv__v">{{ p.path }}</code>
              </div>
            </section>
          </div>

          <section class="card qr-card">
            <h3 class="card__title">小程序码</h3>
            <div class="qr-box">
              <img v-if="qrDataUrl" :src="qrDataUrl" alt="门店小程序码参数二维码" />
              <span v-else>生成中</span>
            </div>
            <p class="qr-note">扫码进入门店独立小程序；需在微信小程序后台发布新版本后刷新。</p>
            <div class="qr-actions">
              <el-button type="primary" @click="downloadQr">
                <el-icon><Download /></el-icon> 下载小程序码
              </el-button>
              <el-button @click="copyText(launchPath, '路径已复制')">
                <el-icon><CopyDocument /></el-icon> 复制路径
              </el-button>
            </div>
          </section>
        </div>
      </section>

      <!-- Tab 3：门店账号 -->
      <section v-show="tab === 'staff'" class="tab-panel">
        <div class="note-tab">门店详情页 · 门店账号 Tab：角色 / 姓名 / 账号 / 手机号 / 状态 / 操作[改密·停用·启用]。</div>
        <div class="detail-grid">
          <section class="card account-card">
            <el-table :data="staffRows" v-loading="staffLoading">
              <el-table-column label="角色" width="92">
                <template #default="{ row }">
                  <el-tag v-if="row.role === 'manager'" type="warning" effect="plain">店长</el-tag>
                  <el-tag v-else type="info" effect="plain">店员</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column label="账号" width="160">
                <template #default="{ row }"><code class="slug">{{ row.username }}</code></template>
              </el-table-column>
              <el-table-column label="手机号" width="140">
                <template #default="{ row }">{{ row.phone || "—" }}</template>
              </el-table-column>
              <el-table-column label="状态" width="88">
                <template #default="{ row }">
                  <el-tag v-if="row.status === 'active'" type="success" effect="light">可登录</el-tag>
                  <el-tag v-else type="info" effect="plain">已停用</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="操作" width="190" fixed="right">
                <template #default="{ row }">
                  <PxActionButton
                    label="改密" :icon="Key" tone="default"
                    tip="重置该账号密码（用户无法自助找回，只能由你或店长重置）"
                    @click="resetPassword(row)"
                  />
                  <PxActionButton
                    v-if="row.status === 'active'"
                    label="停用" :icon="Hide" tone="danger"
                    tip="停用后该账号立即无法登录后台" @click="doDisableStaff(row)"
                  />
                  <PxActionButton
                    v-else label="启用" :icon="Check" tone="success" @click="doEnableStaff(row)"
                  />
                </template>
              </el-table-column>

              <template #empty>
                <PxEmpty
                  variant="staff" text="该门店还没有账号"
                  hint="正常情况开户时会同时建好首位店长；若缺失，用右侧表单补上"
                />
              </template>
            </el-table>
          </section>

          <section class="card create-card">
            <h3 class="card__title card__title--serif">新增门店账号</h3>
            <el-form ref="createFormRef" :model="form" :rules="createRules" label-width="76px">
              <el-form-item label="登录账号" prop="username">
                <el-input v-model="form.username" maxlength="32" placeholder="请输入账号" />
              </el-form-item>
              <el-form-item label="初始密码" prop="password">
                <el-input v-model="form.password" maxlength="32" placeholder="至少 6 位" />
              </el-form-item>
              <el-form-item label="姓名" prop="name">
                <el-input v-model="form.name" maxlength="50" placeholder="请输入姓名" />
              </el-form-item>
              <el-form-item label="角色" prop="role">
                <el-select v-model="form.role" placeholder="请选择角色">
                  <el-option label="店长" value="manager" />
                  <el-option label="店员" value="employee" />
                </el-select>
              </el-form-item>
              <el-form-item label="手机号" prop="phone">
                <el-input v-model="form.phone" maxlength="20" placeholder="选填" />
              </el-form-item>
            </el-form>
            <el-button type="primary" class="create-card__submit" :loading="saving" @click="save">创建账号</el-button>
            <p class="create-card__note">店长可在门店后台自行添加店员；此处为平台代开户 / 改密 / 停用入口</p>
          </section>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import QRCode from "qrcode";
import {
  Check, CopyDocument, Delete, Download, Edit, Hide, Key, Upload,
} from "@element-plus/icons-vue";
import {
  createStoreStaff, disableStoreStaff, getStore, listStoreStaff, setStoreStatus,
  updateStoreBrand, updateStoreStaff, uploadStoreLogo,
} from "../../api/platform";
import { isValidHex, mix, DEFAULT_PRIMARY } from "../../utils/theme";
import { mediaUrl } from "../../utils/url";
import PxActionButton from "../../components/PxActionButton.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxErrorState from "../../components/PxErrorState.vue";
import PxPageHeader from "../../components/PxPageHeader.vue";

const route = useRoute();
const storeId = Number(route.params.storeId);

const store = ref(null);
const staffRows = ref([]);
const loading = ref(false);
const staffLoading = ref(false);
const failed = ref(false);
const tab = ref("brand");
const qrDataUrl = ref("");

const profile = computed(() => store.value?.profile || null);
const slug = computed(() => profile.value?.slug || "");
const storeName = computed(() => store.value?.name || "门店");
const profileName = computed(() => profile.value?.name || storeName.value);
const miniappAppid = computed(() => profile.value?.miniapp_appid || "");
const miniappEntryEnabled = computed(() => profile.value?.miniapp_entry_enabled !== false);
const miniappName = computed(() => profile.value?.miniapp_name || profileName.value);

// ---------- 品牌白标（Tab 1）----------
const brand = reactive({
  name: "", slogan: "", logo_url: "", primary_color: DEFAULT_PRIMARY, secondary: DEFAULT_PRIMARY,
});
const brandSaving = ref(false);
const broken = ref(false);
const initial = computed(() => (brand.name || "店").trim().slice(0, 1));

function syncBrand() {
  brand.name = profile.value?.name || "";
  brand.slogan = profile.value?.slogan || "";
  brand.logo_url = profile.value?.logo_url || "";
  brand.primary_color = isValidHex(profile.value?.primary_color)
    ? profile.value.primary_color
    : DEFAULT_PRIMARY;
  // 辅助色后端暂无字段，预览用主色提亮派生，仅本地展示
  brand.secondary = mix(brand.primary_color, "#ffffff", 0.35);
}
watch(profile, syncBrand, { immediate: true });

const brandReady = computed(() => Boolean(profile.value?.name && profile.value?.primary_color));
const contactReady = computed(() => Boolean(profile.value?.contact_phone && profile.value?.contact_address));
const miniappReady = computed(() => Boolean(profile.value?.miniapp_appid && miniappEntryEnabled.value));
const accountReady = computed(() => (store.value?.manager_count || 0) > 0);

const storeSummary = computed(() => [
  {
    label: "品牌白标",
    value: profileName.value,
    hint: brandReady.value ? "C 端与后台已使用该店品牌样式" : "需补齐对外店名与主色",
    done: brandReady.value,
  },
  {
    label: "门店联系",
    value: profile.value?.contact_phone || "未配置电话",
    hint: contactReady.value ? "顾客可在 C 端拨号和查看地址" : "建议补齐电话、地址与营业时间",
    done: contactReady.value,
  },
  {
    label: "独立小程序",
    value: miniappAppid.value || "未绑定 AppID",
    hint: miniappReady.value ? "可用于微信搜索入口发布" : "先配置 AppID，再按门店发布",
    done: miniappReady.value,
  },
  {
    label: "后台账号",
    value: `${store.value?.manager_count || 0} 名店长 · ${store.value?.staff_count || 0} 个账号`,
    hint: accountReady.value ? "门店可登录后台处理订单" : "至少需要 1 名店长账号",
    done: accountReady.value,
  },
]);

const subtitle = computed(() => {
  if (!store.value) return "";
  const s = store.value.profile?.slug;
  const counts = `${store.value.manager_count} 名店长 · ${store.value.staff_count} 个账号`;
  return s ? `C 端入口标识 ${s} ｜ ${counts}` : counts;
});

async function onLogoChange(uploadFile) {
  const file = uploadFile?.raw;
  if (!file) return;
  const allowed = ["image/png", "image/jpeg", "image/webp"];
  if (!allowed.includes(file.type)) {
    ElMessage.warning("Logo 仅支持 PNG、JPG 或 WEBP 图片");
    return;
  }
  if (file.size > 2 * 1024 * 1024) {
    ElMessage.warning("Logo 文件不能超过 2MB");
    return;
  }
  broken.value = false;
  try {
    const result = await uploadStoreLogo(storeId, file);
    brand.logo_url = result.logo_url;
    ElMessage.success("Logo 上传成功，点击「保存」后正式生效");
  } catch {
    ElMessage.error("Logo 上传失败，请重试");
  }
}
function clearLogo() {
  brand.logo_url = "";
  broken.value = false;
  ElMessage.info("Logo 已移除，点击「保存」后生效");
}
function resetBrand() {
  syncBrand();
  ElMessage.info("已还原为最后一次保存的内容");
}
async function saveBrand() {
  if (!brand.name.trim()) {
    ElMessage.warning("请填写门店名称");
    return;
  }
  brandSaving.value = true;
  try {
    const next = await updateStoreBrand(storeId, {
      name: brand.name.trim(),
      slogan: brand.slogan.trim(),
      logo_url: brand.logo_url.trim(),
      primary_color: brand.primary_color,
      // 辅助色暂未接入后端，仅作本地预览，不写入
    });
    store.value = { ...store.value, profile: next };
    ElMessage.success("品牌已保存，C 端与后台即刻生效");
  } finally {
    brandSaving.value = false;
  }
}

// ---------- 小程序入口（Tab 2）----------
const miniappPaths = [
  { label: "首页", path: "/pages/index/index" },
  { label: "服务", path: "/pages/service/service" },
  { label: "纪念品", path: "/pages/products/products" },
  { label: "我的", path: "/pages/profile/profile" },
];
const launchPath = computed(() => (slug.value ? `pages/index/index?slug=${slug.value}` : "pages/index/index"));
const qrPayload = computed(() => JSON.stringify({
  type: "pet_xiaoman_store_entry",
  page: "pages/index/index",
  scene: `slug=${slug.value}`,
  slug: slug.value,
  name: profileName.value,
}));
watch(qrPayload, async (value) => {
  if (!slug.value) {
    qrDataUrl.value = "";
    return;
  }
  qrDataUrl.value = await QRCode.toDataURL(value, {
    width: 160,
    margin: 1,
    errorCorrectionLevel: "M",
    color: { dark: "rgb(29,33,41)", light: "rgb(255,255,255)" },
  });
}, { immediate: true });

// ---------- 门店账号（Tab 3）----------
const saving = ref(false);
const blank = () => ({ role: "employee", name: "", username: "", password: "", phone: "" });
const form = reactive(blank());
const createFormRef = ref(null);
const usernamePattern = /^[A-Za-z0-9_]{3,32}$/;
const phonePattern = /^$|^1\d{10}$|^0\d{2,3}-?\d{7,8}$/;
const createRules = {
  username: [
    { required: true, message: "请填写登录账号", trigger: "blur" },
    { pattern: usernamePattern, message: "账号需为 3-32 位字母、数字或下划线", trigger: "blur" },
  ],
  password: [
    { required: true, message: "请填写初始密码", trigger: "blur" },
    { min: 6, message: "初始密码至少 6 位", trigger: "blur" },
  ],
  name: [{ required: true, message: "请填写姓名", trigger: "blur" }],
  role: [{ required: true, message: "请选择账号角色", trigger: "change" }],
  phone: [{ pattern: phonePattern, message: "手机号或座机格式不正确；不填也可以", trigger: "blur" }],
};

async function save() {
  await createFormRef.value?.validate();
  saving.value = true;
  try {
    await createStoreStaff(storeId, {
      role: form.role,
      name: form.name.trim(),
      username: form.username.trim(),
      password: form.password,
      phone: form.phone.trim() || null,
    });
    ElMessage.success("账号已开通，可立即登录");
    Object.assign(form, blank());
    reloadStaff();
  } finally {
    saving.value = false;
  }
}

async function resetPassword(row) {
  let value;
  try {
    ({ value } = await ElMessageBox.prompt(
      `为「${row.name}」（${row.username}）设置新密码，至少 6 位。`,
      "重置密码",
      {
        confirmButtonText: "确认重置",
        cancelButtonText: "取消",
        inputType: "password",
        inputPlaceholder: "新密码",
        inputValidator: (v) => (v && v.length >= 6 ? true : "至少 6 位"),
      },
    ));
  } catch {
    return;
  }
  await updateStoreStaff(storeId, row.id, { password: value });
  ElMessage.success("密码已重置，请转告对方");
}

async function doDisableStaff(row) {
  try {
    await ElMessageBox.confirm(
      `停用「${row.name}」后，该账号立即无法登录后台，历史订单不受影响。确认停用？`,
      "停用账号",
      { type: "warning", confirmButtonText: "确认停用", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  await disableStoreStaff(storeId, row.id);
  ElMessage.success("账号已停用");
  reloadStaff();
}

async function doEnableStaff(row) {
  await updateStoreStaff(storeId, row.id, { status: "active" });
  ElMessage.success("账号已启用");
  reloadStaff();
}

// ---------- 通用 ----------
function goBrand() {
  tab.value = "brand";
}

async function copyText(text, message = "已复制") {
  const value = String(text || "");
  if (!value) return;
  try {
    await navigator.clipboard.writeText(value);
  } catch {
    const el = document.createElement("textarea");
    el.value = value;
    el.setAttribute("readonly", "");
    el.style.position = "fixed";
    el.style.left = "-9999px";
    document.body.appendChild(el);
    el.select();
    document.execCommand("copy");
    document.body.removeChild(el);
  }
  ElMessage.success(message);
}

function downloadQr() {
  if (!qrDataUrl.value) return ElMessage.warning("二维码还在生成中，请稍后再试");
  const a = document.createElement("a");
  a.href = qrDataUrl.value;
  a.download = `pet-xiaoman-${slug.value || "store"}-entry.png`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  ElMessage.success("参数码已下载");
}

async function doStatus(status) {
  const off = status === "disabled";
  try {
    await ElMessageBox.confirm(
      off
        ? `停用「${store.value.name}」后，C 端按该店标识访问会直接 404（不再接单），后台数据与账号都会保留。确认停用？`
        : `启用「${store.value.name}」后，该门店 C 端恢复接单。确认启用？`,
      off ? "停用门店" : "启用门店",
      { type: "warning", confirmButtonText: off ? "确认停用" : "确认启用", cancelButtonText: "取消" },
    );
  } catch {
    return;
  }
  store.value = await setStoreStatus(storeId, status);
  ElMessage.success(off ? "门店已停用" : "门店已启用");
}

async function load() {
  loading.value = true;
  failed.value = false;
  try {
    const [s, staff] = await Promise.all([getStore(storeId), listStoreStaff(storeId)]);
    store.value = s;
    staffRows.value = staff;
  } catch {
    failed.value = true;
  } finally {
    loading.value = false;
  }
}

async function reloadStaff() {
  staffLoading.value = true;
  try {
    staffRows.value = await listStoreStaff(storeId);
    const s = await getStore(storeId);
    store.value = s;
  } finally {
    staffLoading.value = false;
  }
}

load();
</script>

<style scoped>
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}
.status-badge::before {
  content: "";
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: currentColor;
}
.status-badge.is-on { background: var(--px-primary-light); color: var(--px-primary-pressed); }
.status-badge.is-off { background: rgba(134, 144, 156, 0.14); color: var(--px-text-3); }

/* 概览四卡 */
.summary-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--px-sp-3);
  margin-bottom: var(--px-sp-4);
}
.summary-card {
  min-width: 0;
  padding: var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-xl);
  background: var(--px-bg-card);
  box-shadow: var(--px-shadow-card-soft);
}
.summary-card--done { border-color: rgba(91, 140, 133, 0.20); }
.summary-card--todo { border-color: rgba(217, 139, 43, 0.26); background: var(--px-bg-warning); }
.summary-card__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--px-sp-2);
  color: var(--px-text-2);
  font-size: var(--px-fs-xs);
  font-weight: 600;
}
.summary-card__tag {
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 500;
}
.summary-card--done .summary-card__tag { background: var(--px-primary-light); color: var(--px-primary-pressed); }
.summary-card--todo .summary-card__tag { background: rgba(217, 139, 43, 0.14); color: var(--px-warning); }
.summary-card strong {
  display: block;
  margin-top: var(--px-sp-2);
  color: var(--px-text-1);
  font-size: var(--px-fs-md);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.summary-card p {
  margin: var(--px-sp-1) 0 0;
  color: var(--px-text-3);
  font-size: var(--px-fs-xs);
  line-height: 1.5;
}

/* Tab 导航（画布药丸） */
.tab-nav {
  display: flex;
  gap: 8px;
  height: 48px;
  align-items: center;
  margin-bottom: var(--px-sp-3);
}
.tab-nav__item {
  height: 40px;
  padding: 0 18px;
  border: none;
  border-radius: 999px;
  background: transparent;
  color: var(--px-text-2);
  font-size: 13px;
  cursor: pointer;
  transition: all var(--px-motion-fast) linear;
}
.tab-nav__item:hover { color: var(--px-primary-pressed); }
.tab-nav__item.active {
  background: var(--px-primary-light);
  color: var(--px-primary-pressed);
  font-weight: 500;
}

/* 画布 note-tab 提示条 */
.note-tab {
  padding: 9px 12px;
  border-radius: 10px;
  background: var(--px-primary-light);
  color: var(--px-primary-pressed);
  font-size: 12px;
  line-height: 1.5;
  margin-bottom: var(--px-sp-3);
}

/* 两栏布局 */
.detail-grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 360px;
  gap: var(--px-sp-4);
  align-items: start;
}
.detail-grid__left {
  display: grid;
  gap: var(--px-sp-4);
  min-width: 0;
}
.card {
  padding: var(--px-sp-5);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-xl);
  background: var(--px-bg-card);
  box-shadow: var(--px-shadow-card-soft);
}
.card__title {
  margin: 0 0 var(--px-sp-4);
  color: var(--px-text-1);
  font-size: 15px;
  font-weight: 600;
}
.card__title--serif { font-family: var(--px-font-serif); }

/* Tab1 品牌白标表单 */
.logo-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: var(--px-sp-4);
}
.logo-box {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  width: 88px;
  height: 88px;
  border: 1px solid var(--px-border);
  border-radius: 14px;
  background: var(--px-bg-warm);
  color: var(--px-text-3);
  font-size: 12px;
  line-height: 1.2;
  overflow: hidden;
  flex-shrink: 0;
}
.logo-box img { width: 100%; height: 100%; object-fit: contain; }
.logo-hint__t { color: var(--px-text-1); font-size: 13px; }
.logo-hint__s { color: var(--px-text-3); font-size: 12px; }
.logo-hint__actions { display: flex; align-items: center; gap: var(--px-sp-2); margin-top: 6px; }

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: var(--px-sp-4);
}
.field { min-width: 0; }
.field > label {
  display: block;
  margin-bottom: 8px;
  color: var(--px-text-1);
  font-size: 13px;
}
.field__hint { display: block; margin-top: 4px; font-size: 11px; color: var(--px-text-3); }
.swatch-row { display: flex; align-items: center; gap: 10px; }
.swatch-hex { font-size: 12px; color: var(--px-text-2); font-variant-numeric: tabular-nums; }

.action-bar {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  height: 56px;
  align-items: center;
}

/* Tab1 换肤预览 */
.preview-mock {
  border: 1px solid var(--px-border);
  border-radius: 12px;
  background: var(--px-bg-warm);
  overflow: hidden;
}
.preview-mock__bar { height: 28px; }
.preview-mock__body {
  display: grid;
  gap: 10px;
  padding: 12px;
  justify-items: start;
}
.preview-mock__logo {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 999px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}
.preview-mock__logo img { width: 28px; height: 28px; object-fit: contain; }
.preview-mock__name { color: var(--px-text-1); font-size: 15px; font-weight: 600; }
.preview-mock__slogan { color: var(--px-text-2); font-size: 12px; }
.preview-mock__btn {
  width: 100%;
  padding: 8px 0;
  border: none;
  border-radius: 8px;
  color: #fff;
  font-size: 13px;
  cursor: default;
}
.preview-mock__btn--ghost {
  background: #fff;
  border: 1px solid;
}
.preview-note {
  margin: var(--px-sp-3) 0 0;
  color: var(--px-text-3);
  font-size: 12px;
  line-height: 1.5;
}

/* Tab2 小程序信息 / 路径 */
.kv {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 10px 0;
  border-bottom: 1px solid rgba(236, 233, 227, 0.7);
}
.kv:last-child { border-bottom: none; }
.kv__k { color: var(--px-text-3); font-size: 13px; flex-shrink: 0; }
.kv__v {
  color: var(--px-text-1);
  font-size: 13px;
  min-width: 0;
  overflow-wrap: anywhere;
}
.kv__v code, .slug {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 13px;
  color: var(--px-text-2);
}

/* Tab2 小程序码 */
.qr-card { display: flex; flex-direction: column; }
.qr-box {
  display: grid;
  place-items: center;
  width: 160px;
  height: 160px;
  margin: 0 auto;
  border: 1px solid var(--px-border);
  border-radius: 12px;
  background: var(--px-bg-card);
  color: var(--px-text-3);
  overflow: hidden;
}
.qr-box img { width: 160px; height: 160px; }
.qr-note {
  margin: var(--px-sp-3) auto 0;
  max-width: 240px;
  text-align: center;
  color: var(--px-text-3);
  font-size: 12px;
  line-height: 1.5;
}
.qr-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-top: var(--px-sp-4);
}
.qr-actions :deep(.el-button) { margin-left: 0; }

/* Tab3 账号表格 + 新增卡 */
.account-card { padding: 0; overflow: hidden; }
.account-card :deep(.el-table) { border-radius: var(--px-radius-xl); }
.create-card__submit {
  width: 100%;
  margin-top: var(--px-sp-2);
  border-radius: 10px;
}
.create-card__note {
  margin: var(--px-sp-3) 0 0;
  color: var(--px-text-3);
  font-size: 11px;
  line-height: 1.5;
}
.create-card :deep(.el-form) { margin-top: var(--px-sp-1); }

@media (max-width: 1100px) {
  .detail-grid { grid-template-columns: 1fr; }
}
@media (max-width: 760px) {
  .summary-row { grid-template-columns: 1fr 1fr; }
  .form-row { grid-template-columns: 1fr; }
}
@media (max-width: 520px) {
  .summary-row { grid-template-columns: 1fr; }
}
</style>
