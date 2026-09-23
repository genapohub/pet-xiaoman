<!-- B-角色权限 Rbac（对齐画布 2:1424）
     版式：页头（标题 / 副标题 / 新建角色）+ 双栏（左角色列表 · 右权限配置）。
     数据全部来自后端 RBAC：角色 listRoles、菜单 listMenus、员工 listStaff（算各角色人数）。
     开关 = 菜单级权限（RoleMenu.menu_key），保存批量写回 PUT /api/b/roles/{key}。

     不虚构说明：
     - 画布 v2 列了 4 个角色（店长/前台/服务师/财务），但 v1 模型只有 2 个租户角色
       （manager/employee，见 app/models/rbac.py Role）。此处渲染后端真实返回的角色，
       不补画布超前于模型的角色；画布超前项归口文档待对齐。
     - 画布列了 7 个权限开关（含不存在的「门店配置」），此处渲染后端真实菜单
       listMenus（含 dashboard/orders/service-items/products/boarding/customers/stats/staff/rbac），
       不写死画布示例标签。
     - 「新建角色」按画布保留按钮，但 v1 无建角色接口，点击给诚实提示，不留死按钮。 -->
<template>
  <div class="rbac">
    <px-page-header title="角色权限" subtitle="门店角色与功能授权">
      <template #actions>
        <el-button class="rbac__add" @click="onNewRole">
          <el-icon><Plus /></el-icon> 新建角色
        </el-button>
      </template>
    </px-page-header>

    <div v-loading="loading" class="rbac__body">
      <!-- 左：角色列表 -->
      <aside class="rbac__roles">
        <p class="rbac__roles-title">角色</p>
        <button
          v-for="r in roles"
          :key="r.key"
          type="button"
          class="rbac__role"
          :class="{ 'is-active': r.key === selectedKey }"
          @click="selectRole(r.key)"
        >
          <span class="rbac__role-name">{{ r.name }}</span>
          <span class="rbac__role-count">{{ roleCount(r.key) }}</span>
        </button>
        <p v-if="!roles.length" class="rbac__empty">暂无可选角色</p>
      </aside>

      <!-- 右：权限配置 -->
      <section class="rbac__perm">
        <header class="rbac__perm-head">
          <h2 class="rbac__perm-title">{{ selectedRole?.name }} · 权限配置</h2>
          <el-button
            type="primary"
            size="small"
            class="rbac__save"
            :loading="saving"
            :disabled="!selectedRole"
            @click="save"
          >
            保存
          </el-button>
        </header>

        <ul v-if="selectedRole" class="rbac__toggles">
          <li v-for="m in menus" :key="m.key" class="rbac__toggle">
            <span class="rbac__toggle-name">{{ m.title }}</span>
            <el-switch
              class="rbac-switch"
              :model-value="menuOn(m.key)"
              @change="(v) => toggleMenu(m.key, v)"
            />
          </li>
          <li v-if="!menus.length" class="rbac__toggle rbac__toggle--empty">
            暂无菜单权限可配置
          </li>
        </ul>
        <p v-else class="rbac__empty rbac__empty--perm">请选择左侧角色以配置权限</p>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { ElMessage } from "element-plus";
import { Plus } from "@element-plus/icons-vue";
import { listRoles, listMenus, updateRole } from "../../api/rbac";
import { listStaff } from "../../api/staff";
import PxPageHeader from "../../components/PxPageHeader.vue";

const roles = ref([]);
const menus = ref([]);
const staffCountByRole = ref({});
const selectedKey = ref("");
const drafts = reactive({}); // roleKey -> string[]（该角色勾选的 menu_key 草稿）
const saving = ref(false);
const loading = ref(false);

const selectedRole = computed(
  () => roles.value.find((r) => r.key === selectedKey.value) || null,
);

function roleCount(key) {
  return staffCountByRole.value[key] || 0;
}
function menuOn(key) {
  const arr = drafts[selectedKey.value];
  return Array.isArray(arr) && arr.includes(key);
}
function toggleMenu(key, val) {
  const arr = drafts[selectedKey.value];
  if (!arr) return;
  const i = arr.indexOf(key);
  if (val && i === -1) arr.push(key);
  else if (!val && i > -1) arr.splice(i, 1);
}

function selectRole(key) {
  selectedKey.value = key;
  const r = roles.value.find((x) => x.key === key);
  if (r && !drafts[key]) drafts[key] = [...(r.menus || [])];
}

async function loadAll() {
  loading.value = true;
  try {
    const [rs, ms, staff] = await Promise.all([
      listRoles(),
      listMenus(),
      listStaff(),
    ]);
    roles.value = rs;
    menus.value = ms;
    const cnt = {};
    staff.forEach((s) => {
      cnt[s.role] = (cnt[s.role] || 0) + 1;
    });
    staffCountByRole.value = cnt;
    rs.forEach((r) => {
      if (!drafts[r.key]) drafts[r.key] = [...(r.menus || [])];
    });
    if (rs.length) selectRole(rs[0].key);
  } finally {
    loading.value = false;
  }
}

async function save() {
  const role = selectedRole.value;
  if (!role) return;
  const nextMenus = drafts[role.key] || [];
  if (!nextMenus.length) {
    return ElMessage.warning("至少保留一个可访问菜单，否则该角色登录后无可用页面");
  }
  saving.value = true;
  try {
    await updateRole(role.key, {
      menu_keys: nextMenus,
      permissions: role.permissions || [],
    });
    // 回写本地角色对象，保证后续只读展示与草稿一致
    role.menus = [...nextMenus];
    ElMessage.success(`「${role.name}」权限已保存`);
  } finally {
    saving.value = false;
  }
}

function onNewRole() {
  ElMessage.info("当前版本仅内置「店长 / 店员」两个角色，暂不支持新建自定义角色（后端未提供建角色接口）");
}

onMounted(loadAll);
</script>

<style scoped>
.rbac__body {
  display: flex;
  align-items: flex-start;
  gap: var(--px-sp-4);
}

/* 左：角色列表 */
.rbac__roles {
  width: 300px;
  flex-shrink: 0;
  box-sizing: border-box;
  background: var(--px-bg-card);
  border: 1px solid #ECE9E3;
  border-radius: var(--px-radius-xl);
  box-shadow: var(--px-shadow-card-soft);
  padding: var(--px-sp-4);
  display: flex;
  flex-direction: column;
  gap: var(--px-sp-2);
}
.rbac__roles-title {
  margin: 0 0 4px;
  font-size: var(--px-fs-sm);
  font-weight: 600;
  color: var(--px-text-1);
}
.rbac__role {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  box-sizing: border-box;
  padding: 10px 12px;
  border: none;
  background: transparent;
  border-radius: 10px;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  transition: background-color var(--px-motion-fast) linear;
}
.rbac__role:hover {
  background: var(--px-bg-hover);
}
.rbac__role.is-active {
  background: var(--px-primary-light);
}
.rbac__role-name {
  font-size: var(--px-fs-base);
  color: var(--px-text-1);
}
.rbac__role.is-active .rbac__role-name {
  color: #3D5C57;
  font-weight: 600;
}
.rbac__role-count {
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  box-sizing: border-box;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  background: #fff;
  border: 1px solid var(--px-border);
  color: var(--px-text-3);
  font-size: 12px;
  font-weight: 600;
  line-height: 1;
}
.rbac__role.is-active .rbac__role-count {
  background: var(--px-primary);
  border-color: var(--px-primary);
  color: #fff;
}

/* 右：权限配置 */
.rbac__perm {
  flex: 1;
  min-width: 0;
  background: var(--px-bg-card);
  border: 1px solid #ECE9E3;
  border-radius: var(--px-radius-xl);
  box-shadow: var(--px-shadow-card-soft);
}
.rbac__perm-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--px-sp-3);
  padding: 16px 20px;
  border-bottom: 1px solid var(--px-border);
}
.rbac__perm-title {
  margin: 0;
  font-family: var(--px-font-serif);
  font-size: var(--px-fs-md);
  font-weight: 600;
  color: var(--px-text-1);
}
.rbac__toggles {
  list-style: none;
  margin: 0;
  padding: 0;
}
.rbac__toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--px-border);
}
.rbac__toggle:last-child {
  border-bottom: none;
}
.rbac__toggle-name {
  font-size: var(--px-fs-base);
  color: var(--px-text-1);
}
.rbac__toggle--empty {
  justify-content: center;
  color: var(--px-text-3);
}

.rbac__empty {
  margin: 8px 2px;
  font-size: var(--px-fs-sm);
  color: var(--px-text-3);
}
.rbac__empty--perm {
  padding: 32px 20px;
  text-align: center;
}

/* 按钮：对齐画布圆角与尺寸 */
.rbac__add {
  border-radius: 10px;
  height: 34px;
  padding: 0 16px;
  font-size: 13px;
  font-weight: 500;
}
.rbac__save {
  border-radius: 8px;
}

/* 开关：画布 44×24，白底旋钮 18×18，松绿=开 / 灰=#C9CDD4=关 */
.rbac-switch {
  --el-switch-on-color: #5B8C85;
  --el-switch-off-color: #C9CDD4;
  --el-switch-button-size: 18px;
}
.rbac-switch :deep(.el-switch__core) {
  width: 44px !important;
  height: 24px !important;
  border-radius: 999px;
}
.rbac-switch :deep(.el-switch__action) {
  width: 18px !important;
  height: 18px !important;
}
</style>
