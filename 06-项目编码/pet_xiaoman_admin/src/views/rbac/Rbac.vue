<!-- B-角色权限 Rbac（对齐画布 2:1424）
     版式：页头 + 提示条 + 角色权限卡片网格；按角色控制菜单与关键操作权限。
     保存为批量更新，避免多卡片状态互相覆盖。 -->
<template>
  <div class="rbac">
    <px-page-header title="角色权限" subtitle="按角色分配可访问菜单与操作权限，店长 / 店员据此区分功能范围">
      <template #actions>
        <el-button :loading="loading" @click="loadAll">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
      </template>
    </px-page-header>

    <el-alert
      class="rbac__tip"
      type="info"
      :closable="false"
      show-icon
      title="修改立即生效：菜单决定侧边栏与路由可见性，操作权限决定关键按钮（如撤回影像、退款）是否可用。"
    />

    <div v-loading="loading" class="rbac__grid">
      <el-card v-for="role in roles" :key="role.key" class="rbac__card" shadow="never">
        <div class="rbac__card-head">
          <div class="rbac__card-title">
            <h3 class="rbac__role-name">{{ role.name }}</h3>
            <p class="rbac__role-desc">{{ role.description || "—" }}</p>
          </div>
          <el-button type="primary" size="small" :loading="saving[role.key]" @click="save(role)">
            保存
          </el-button>
        </div>

        <div class="rbac__section">
          <div class="rbac__section-title">
            菜单权限
            <span class="rbac__section-hint">已选 {{ menusModel[role.key]?.length || 0 }} 项；勾选后该角色可见对应菜单</span>
          </div>
          <el-checkbox-group v-model="menusModel[role.key]" class="rbac__checks">
            <el-checkbox v-for="m in menus" :key="m.key" :label="m.key" border>{{ m.title }}</el-checkbox>
          </el-checkbox-group>
        </div>

        <div class="rbac__section">
          <div class="rbac__section-title">
            操作权限
            <span class="rbac__section-hint">已选 {{ permsModel[role.key]?.length || 0 }} 项；勾选后该角色可使用对应敏感操作</span>
          </div>
          <el-checkbox-group v-model="permsModel[role.key]" class="rbac__checks">
            <el-checkbox v-for="p in permissions" :key="p.code" :label="p.code" border>{{ p.label }}</el-checkbox>
          </el-checkbox-group>
        </div>
      </el-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { ElMessage, ElMessageBox } from "element-plus";
import { Refresh } from "@element-plus/icons-vue";
import { listRoles, listMenus, listPermissions, updateRole } from "../../api/rbac";
import PxPageHeader from "../../components/PxPageHeader.vue";

const roles = ref([]);
const menus = ref([]);
const permissions = ref([]);
const menusModel = reactive({}); // roleKey -> [menuKey]
const permsModel = reactive({}); // roleKey -> [code]
const saving = reactive({});
const loading = ref(false);

async function loadAll() {
  loading.value = true;
  try {
    const [rs, ms, ps] = await Promise.all([listRoles(), listMenus(), listPermissions()]);
    roles.value = rs;
    menus.value = ms;
    permissions.value = ps;
    rs.forEach((r) => {
      menusModel[r.key] = [...r.menus];
      permsModel[r.key] = [...r.permissions];
    });
  } finally {
    loading.value = false;
  }
}

async function save(role) {
  const nextMenus = menusModel[role.key] || [];
  const nextPerms = permsModel[role.key] || [];
  if (!nextMenus.length) return ElMessage.warning("至少保留一个可访问菜单，否则该角色登录后无可用页面");
  if (role.key === "manager" && (!nextMenus.includes("rbac") || !nextPerms.includes("role.manage"))) {
    try {
      await ElMessageBox.confirm(
        "店长角色缺少「角色权限」菜单或权限后，将无法继续调整团队权限。确认这样保存？",
        "权限风险确认",
        { type: "warning", confirmButtonText: "确认保存", cancelButtonText: "再检查一下" },
      );
    } catch {
      return;
    }
  } else {
    try {
      await ElMessageBox.confirm(`确认保存「${role.name}」的菜单与操作权限？`, "保存权限", {
        type: "info",
        confirmButtonText: "保存",
        cancelButtonText: "取消",
      });
    } catch {
      return;
    }
  }
  saving[role.key] = true;
  try {
    await updateRole(role.key, {
      menu_keys: nextMenus,
      permissions: nextPerms,
    });
    ElMessage.success(`「${role.name}」权限已保存`);
  } finally {
    saving[role.key] = false;
  }
}

onMounted(loadAll);
</script>

<style scoped>
.rbac__tip { margin-bottom: var(--px-sp-4); }
.rbac__grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
  gap: var(--px-sp-4);
  align-items: start;
}
.rbac__card { border: 1px solid var(--px-border); }
.rbac__card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--px-sp-3);
  margin-bottom: var(--px-sp-4);
}
.rbac__role-name { margin: 0; font-size: var(--px-fs-lg); font-weight: 600; color: var(--px-text-1); }
.rbac__role-desc { margin: var(--px-sp-1) 0 0; font-size: var(--px-fs-sm); color: var(--px-text-2); }
.rbac__section { margin-bottom: var(--px-sp-4); }
.rbac__section:last-child { margin-bottom: 0; }
.rbac__section-title {
  margin-bottom: var(--px-sp-2);
  font-size: var(--px-fs-sm);
  font-weight: 600;
  color: var(--px-text-1);
}
.rbac__section-hint { margin-left: var(--px-sp-2); font-weight: 400; color: var(--px-text-3); font-size: var(--px-fs-xs); }
.rbac__checks { display: flex; flex-wrap: wrap; gap: var(--px-sp-2); }
</style>
