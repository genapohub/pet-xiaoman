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
import { computed, reactive, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage, ElMessageBox } from "element-plus";
import { Check, Hide, Key, Plus, UserFilled } from "@element-plus/icons-vue";
import {
  createStoreStaff, disableStoreStaff, getStore, listStoreStaff, setStoreStatus, updateStoreStaff,
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
</style>
