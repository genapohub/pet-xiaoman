<template>
  <div class="store-detail">
    <PxPageHeader
      :title="store?.name || '门店'"
      :subtitle="subtitle"
      back
    >
      <template #actions>
        <el-tag v-if="store" :type="store.status === 'active' ? 'success' : 'info'" effect="light">
          {{ store.status === "active" ? "营业中" : "已停用" }}
        </el-tag>
        <el-button
          v-if="store?.status === 'active'"
          @click="doStatus('disabled')"
        >
          停用门店
        </el-button>
        <el-button v-else-if="store" type="primary" @click="doStatus('active')">启用门店</el-button>
      </template>
    </PxPageHeader>

    <PxErrorState v-if="failed" text="门店信息加载失败" :loading="loading" @retry="load" />

    <template v-else>
      <el-tabs v-model="tab" class="tabs">
        <el-tab-pane label="品牌与 UI" name="brand">
          <div class="panel">
            <div class="panel__head">
              <h3 class="panel__title">对外展示</h3>
              <p class="panel__hint">
                这里配的店名 / 标语 / Logo / 主色会同时作用到 C 端小程序与本后台的配色。
                门店自己的账号看不到、也改不了这一页。
              </p>
            </div>
            <PxBrandForm :store-id="storeId" @saved="load" />
          </div>
        </el-tab-pane>

        <el-tab-pane label="小程序入口" name="miniapp">
          <div class="panel">
            <div class="panel__head panel__head--row">
              <div>
                <h3 class="panel__title">C 端小程序入口</h3>
                <p class="panel__hint">
                  同一套小程序源码支持两种入口：顾客微信搜索该店独立小程序时默认进入本门店；
                  顾客扫码时则按二维码里的门店标识切换品牌与数据。
                </p>
              </div>
              <el-tag :type="miniappEntryEnabled ? 'success' : 'info'" effect="light">
                {{ miniappEntryEnabled ? "独立入口已启用" : "独立入口已关闭" }}
              </el-tag>
            </div>

            <div v-if="!slug" class="miniapp-empty">
              <PxEmpty
                variant="box"
                text="该门店还没有 C 端入口标识"
                hint="先到「品牌与 UI」确认门店白标资料，再生成小程序码"
              />
            </div>

            <div v-else class="miniapp-grid">
              <section class="entry-config">
                <div class="entry-config__head">
                  <div>
                    <h4>独立小程序搜索入口</h4>
                    <p>微信侧搜索小程序名称进入时，没有二维码参数，系统使用默认门店标识绑定品牌与业务数据。</p>
                  </div>
                  <el-button type="primary" :loading="miniappSaving" @click="saveMiniappEntry">
                    保存入口
                  </el-button>
                </div>

                <el-form class="entry-form" label-width="112px">
                  <el-form-item label="小程序名称">
                    <el-input v-model="miniappForm.miniapp_name" maxlength="50" placeholder="如：宠小满·示例门店" />
                  </el-form-item>
                  <el-form-item label="小程序 AppID">
                    <el-input v-model="miniappForm.miniapp_appid" maxlength="64" placeholder="如 wx667ddd8e0d8dd8fb，暂未申请可留空" />
                  </el-form-item>
                  <el-form-item label="默认入口">
                    <el-switch v-model="miniappForm.miniapp_entry_enabled" active-text="启用" inactive-text="关闭" />
                  </el-form-item>
                </el-form>

                <div class="entry-summary">
                  <div>
                    <span>默认门店标识</span>
                    <code>{{ slug }}</code>
                  </div>
                  <div>
                    <span>发布配置</span>
                    <code>{{ publishCommand }}</code>
                  </div>
                  <el-button text type="primary" @click="copyText(publishCommand, '发布配置命令已复制')">
                    <el-icon><CopyDocument /></el-icon> 复制
                  </el-button>
                </div>
              </section>

              <section class="miniapp-code">
                <div class="qr-box">
                  <img v-if="qrDataUrl" :src="qrDataUrl" alt="门店小程序码参数二维码" />
                  <span v-else>生成中</span>
                </div>
                <div class="miniapp-code__title">{{ profileName }}</div>
                <div class="miniapp-code__meta">门店标识：{{ slug }}</div>
                <el-button class="miniapp-code__btn" type="primary" plain @click="copyText(qrPayload, '二维码内容已复制')">
                  <el-icon><CopyDocument /></el-icon> 复制二维码内容
                </el-button>
              </section>

              <section class="entry-panel">
                <div class="entry-item">
                  <div class="entry-label">微信官方码参数</div>
                  <code>{{ miniappPage }}</code>
                  <code>{{ miniappScene }}</code>
                  <el-button text type="primary" @click="copyText(officialMiniappPayload, '官方码参数已复制')">
                    <el-icon><CopyDocument /></el-icon> 复制
                  </el-button>
                </div>

                <div class="entry-item">
                  <div class="entry-label">开发者工具启动路径</div>
                  <code>{{ launchPath }}</code>
                  <el-button text type="primary" @click="copyText(launchPath, '启动路径已复制')">
                    <el-icon><Link /></el-icon> 复制
                  </el-button>
                </div>

                <div class="entry-item">
                  <div class="entry-label">C 端白标验收接口</div>
                  <code>{{ storeProfileApi }}</code>
                  <el-button text type="primary" @click="copyText(storeProfileApi, '接口地址已复制')">
                    <el-icon><CopyDocument /></el-icon> 复制
                  </el-button>
                </div>

                <div class="entry-item">
                  <div class="entry-label">业务请求门店头</div>
                  <code>X-Store-Slug: {{ slug }}</code>
                  <el-button text type="primary" @click="copyText(`X-Store-Slug: ${slug}`, '请求头已复制')">
                    <el-icon><CopyDocument /></el-icon> 复制
                  </el-button>
                </div>
              </section>

              <section class="entry-note">
                <el-icon><Tickets /></el-icon>
                <div>
                  <strong>两种入口共用同一套租户隔离。</strong>
                  <span>
                    独立 AppID 发布包会写入默认门店标识；二维码入口继续带 scene=slug。
                    C 端业务请求都会携带 X-Store-Slug，价格、商品、订单和宠物档案不会串店。
                  </span>
                </div>
              </section>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane label="门店账号" name="staff">
          <div class="panel">
            <div class="panel__head panel__head--row">
              <div>
                <h3 class="panel__title">登录账号</h3>
                <p class="panel__hint">
                  该店店长可自己再添加店员；这里是你代为开户 / 改密 / 停用的入口。
                  店长只能有一个是你开通的首位店长，后续加的都算店员。
                </p>
              </div>
              <el-button type="primary" @click="openCreate">
                <el-icon><Plus /></el-icon> 开账号
              </el-button>
            </div>

            <el-table :data="staffRows" v-loading="staffLoading">
              <el-table-column label="角色" width="92">
                <template #default="{ row }">
                  <el-tag v-if="row.role === 'manager'" type="warning" effect="plain">店长</el-tag>
                  <el-tag v-else type="info" effect="plain">店员</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="姓名" width="120" />
              <el-table-column prop="username" label="账号" width="150">
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
                  variant="user" text="该门店还没有账号"
                  hint="正常情况开户时会同时建好首位店长；若缺失，点右上角「开账号」补上"
                />
              </template>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </template>

    <px-form-drawer
      v-model="createVisible"
      title="开通门店账号"
      subtitle="账号直接归属本门店；首次登录后请让对方自行改密"
      :footer-hint="`初始密码：${form.password || '—'}`"
      :icon="UserFilled"
      :saving="saving"
      @cancel="createVisible = false"
      @submit="save"
    >
      <el-form label-width="84px">
        <el-form-item label="角色">
          <el-radio-group v-model="form.role">
            <el-radio-button value="manager">店长</el-radio-button>
            <el-radio-button value="employee">店员</el-radio-button>
          </el-radio-group>
          <span class="field-hint">
            店长可管理本店服务项目、纪念品、团队成员与角色权限；店员只能做订单与客户。
          </span>
        </el-form-item>
        <el-form-item label="姓名">
          <el-input v-model="form.name" maxlength="50" placeholder="如：小李" />
        </el-form-item>
        <el-form-item label="登录账号">
          <el-input v-model="form.username" maxlength="32" placeholder="全平台唯一" />
        </el-form-item>
        <el-form-item label="初始密码">
          <el-input v-model="form.password" maxlength="32" placeholder="至少 6 位" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" maxlength="20" placeholder="选填" />
        </el-form-item>
      </el-form>
    </px-form-drawer>
  </div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import QRCode from "qrcode";
import { Check, CopyDocument, Hide, Key, Link, Plus, Tickets, UserFilled } from "@element-plus/icons-vue";
import {
  createStoreStaff, disableStoreStaff, getStore, listStoreStaff, setStoreStatus,
  updateStoreBrand, updateStoreStaff,
} from "../../api/platform";
import PxActionButton from "../../components/PxActionButton.vue";
import PxBrandForm from "../../components/PxBrandForm.vue";
import PxEmpty from "../../components/PxEmpty.vue";
import PxErrorState from "../../components/PxErrorState.vue";
import PxFormDrawer from "../../components/PxFormDrawer.vue";
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
const miniappSaving = ref(false);

const miniappPage = "pages/index/index";
const profile = computed(() => store.value?.profile || null);
const slug = computed(() => profile.value?.slug || "");
const profileName = computed(() => profile.value?.name || store.value?.name || "门店");
const miniappName = computed(() => profile.value?.miniapp_name || profileName.value);
const miniappAppid = computed(() => profile.value?.miniapp_appid || "");
const miniappEntryEnabled = computed(() => profile.value?.miniapp_entry_enabled !== false);
const miniappScene = computed(() => slug.value ? `scene=slug=${slug.value}` : "scene=—");
const launchPath = computed(() => slug.value ? `${miniappPage}?slug=${slug.value}` : miniappPage);
const storeProfileApi = computed(() => slug.value ? `/api/c/store/profile?slug=${slug.value}` : "/api/c/store/profile");
const officialMiniappPayload = computed(() => `page=${miniappPage}\nscene=slug=${slug.value}`);
const publishCommand = computed(() => [
  `STORE_SLUG=${slug.value}`,
  `MINIAPP_APPID=${miniappAppid.value || "wx请替换为该店AppID"}`,
  `MINIAPP_NAME="${miniappName.value}"`,
  `PROJECT_NAME=pet_xiaoman_${slug.value}`,
  "node scripts/build-store-config.js",
].join(" "));
const qrPayload = computed(() => JSON.stringify({
  type: "pet_xiaoman_store_entry",
  page: miniappPage,
  scene: `slug=${slug.value}`,
  slug: slug.value,
  name: profileName.value,
}));
const miniappForm = reactive({
  miniapp_name: "",
  miniapp_appid: "",
  miniapp_entry_enabled: true,
});

const subtitle = computed(() => {
  if (!store.value) return "";
  const slug = store.value.profile?.slug;
  const counts = `${store.value.manager_count} 名店长 · ${store.value.staff_count} 个账号`;
  return slug ? `C 端入口标识 ${slug} ｜ ${counts}` : counts;
});

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

function syncMiniappForm() {
  miniappForm.miniapp_name = miniappName.value;
  miniappForm.miniapp_appid = miniappAppid.value;
  miniappForm.miniapp_entry_enabled = miniappEntryEnabled.value;
}

const createVisible = ref(false);
const saving = ref(false);
const blank = () => ({ role: "manager", name: "", username: "", password: "", phone: "" });
const form = reactive(blank());

function openCreate() {
  Object.assign(form, blank());
  createVisible.value = true;
}

async function save() {
  if (!form.name.trim() || !form.username.trim()) return ElMessage.warning("请填写姓名与账号");
  if ((form.password || "").length < 6) return ElMessage.warning("初始密码至少 6 位");
  saving.value = true;
  try {
    await createStoreStaff(storeId, {
      role: form.role,
      name: form.name.trim(),
      username: form.username.trim(),
      password: form.password,
      phone: form.phone.trim() || null,
    });
    createVisible.value = false;
    ElMessage.success("账号已开通，可立即登录");
    reloadStaff();
  } finally {
    saving.value = false;
  }
}

async function saveMiniappEntry() {
  if (miniappForm.miniapp_appid && !/^wx[A-Za-z0-9]{8,62}$/.test(miniappForm.miniapp_appid.trim())) {
    return ElMessage.warning("小程序 AppID 需以 wx 开头，仅包含字母数字");
  }
  miniappSaving.value = true;
  try {
    const next = await updateStoreBrand(storeId, {
      miniapp_name: miniappForm.miniapp_name.trim() || "",
      miniapp_appid: miniappForm.miniapp_appid.trim() || "",
      miniapp_entry_enabled: miniappForm.miniapp_entry_enabled,
    });
    store.value = { ...store.value, profile: next };
    syncMiniappForm();
    ElMessage.success("小程序入口已保存");
  } finally {
    miniappSaving.value = false;
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

watch(qrPayload, async (value) => {
  if (!slug.value) {
    qrDataUrl.value = "";
    return;
  }
  qrDataUrl.value = await QRCode.toDataURL(value, {
    width: 224,
    margin: 1,
    errorCorrectionLevel: "M",
    color: { dark: "#1D2129", light: "#FFFFFF" },
  });
}, { immediate: true });

watch(profile, syncMiniappForm, { immediate: true });

load();
</script>

<style scoped>
.tabs { margin-top: calc(-1 * var(--px-sp-2)); }

.panel {
  margin-top: var(--px-sp-3);
  padding: var(--px-sp-5);
  background: var(--px-bg-card);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-lg);
  box-shadow: var(--px-shadow-card);
}
.panel__head { margin-bottom: var(--px-sp-4); }
.panel__head--row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--px-sp-4);
}
.panel__title {
  margin: 0;
  color: var(--px-text-1);
  font-size: var(--px-fs-lg);
  font-weight: 600;
}
.panel__hint {
  margin: var(--px-sp-1) 0 0;
  max-width: 68ch;
  color: var(--px-text-2);
  font-size: var(--px-fs-sm);
  line-height: 1.6;
}
.slug {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}
.field-hint {
  display: block;
  width: 100%;
  margin-top: var(--px-sp-1);
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
  line-height: 1.5;
}
.miniapp-empty {
  padding: var(--px-sp-8) 0;
}
.miniapp-grid {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  gap: var(--px-sp-5);
  align-items: start;
}
.entry-config {
  grid-column: 1 / -1;
  display: grid;
  gap: var(--px-sp-4);
  padding: var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
  background: linear-gradient(180deg, var(--px-bg-card), var(--px-bg-warm));
}
.entry-config__head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--px-sp-4);
}
.entry-config__head h4 {
  margin: 0;
  color: var(--px-text-1);
  font-size: var(--px-fs-md);
}
.entry-config__head p {
  margin: var(--px-sp-1) 0 0;
  color: var(--px-text-2);
  font-size: var(--px-fs-sm);
  line-height: 1.6;
}
.entry-form {
  max-width: 760px;
}
.entry-summary {
  display: grid;
  grid-template-columns: 180px minmax(0, 1fr) auto;
  gap: var(--px-sp-3);
  align-items: center;
}
.entry-summary > div {
  min-width: 0;
}
.entry-summary span {
  display: block;
  margin-bottom: 4px;
  color: var(--px-text-3);
  font-size: var(--px-fs-xs);
}
.entry-summary code {
  display: block;
  min-width: 0;
  padding: 3px var(--px-sp-2);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-sm);
  background: var(--px-primary-softer);
  color: var(--px-text-2);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--px-fs-sm);
  overflow-wrap: anywhere;
}
.miniapp-code {
  padding: var(--px-sp-5);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-lg);
  background: var(--px-bg-warm);
  text-align: center;
}
.qr-box {
  display: grid;
  place-items: center;
  width: 224px;
  height: 224px;
  margin: 0 auto var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
  background: var(--px-bg-card);
  color: var(--px-text-3);
  overflow: hidden;
}
.qr-box img {
  display: block;
  width: 224px;
  height: 224px;
}
.miniapp-code__title {
  color: var(--px-text-1);
  font-size: var(--px-fs-md);
  font-weight: 600;
}
.miniapp-code__meta {
  margin-top: var(--px-sp-1);
  color: var(--px-text-2);
  font-size: var(--px-fs-sm);
}
.miniapp-code__btn {
  margin-top: var(--px-sp-4);
}
.entry-panel {
  display: grid;
  gap: var(--px-sp-3);
}
.entry-item {
  display: grid;
  grid-template-columns: 150px minmax(0, 1fr) minmax(0, 1fr) auto;
  gap: var(--px-sp-3);
  align-items: center;
  padding: var(--px-sp-3) var(--px-sp-4);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-md);
  background: var(--px-bg-card);
}
.entry-item code {
  min-width: 0;
  padding: 3px var(--px-sp-2);
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-sm);
  background: var(--px-primary-softer);
  color: var(--px-text-2);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: var(--px-fs-sm);
  overflow-wrap: anywhere;
}
.entry-item code:only-of-type {
  grid-column: span 2;
}
.entry-label {
  color: var(--px-text-1);
  font-weight: 600;
}
.entry-note {
  grid-column: 1 / -1;
  display: flex;
  gap: var(--px-sp-3);
  align-items: flex-start;
  padding: var(--px-sp-4);
  border: 1px solid rgba(227, 115, 24, 0.22);
  border-radius: var(--px-radius-md);
  background: var(--px-bg-warning);
  color: var(--px-text-2);
  line-height: 1.7;
}
.entry-note .el-icon {
  margin-top: 3px;
  color: var(--px-warning);
}
.entry-note strong {
  display: block;
  color: var(--px-text-1);
}
@media (max-width: 960px) {
  .miniapp-grid {
    grid-template-columns: 1fr;
  }
  .entry-config__head,
  .entry-summary {
    grid-template-columns: 1fr;
  }
  .entry-item {
    grid-template-columns: 1fr;
  }
  .entry-item code:only-of-type {
    grid-column: auto;
  }
}
</style>
