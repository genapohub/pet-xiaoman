<template>
  <el-container class="layout">
    <el-aside class="sider" :class="{ 'is-collapsed': collapsed }">
      <div class="brand">
        <span class="brand__mark"><img class="brand__logo" src="/brand/logo-mark-white.png" alt="宠小满" /></span>
        <span v-show="!collapsed" class="brand__copy">
          <span class="brand__name">宠小满</span>
          <span class="brand__sub">门店履约后台</span>
        </span>
      </div>

      <el-menu router :default-active="activeMenu" :collapse="collapsed" :collapse-transition="false">
        <el-menu-item v-for="m in menus" :key="m.path" :index="m.path">
          <el-icon><component :is="m.icon" /></el-icon>
          <template #title>{{ m.title }}</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="navbar">
        <button class="navbar__icon" type="button" :aria-label="collapsed ? '展开侧栏' : '收起侧栏'" @click="toggle">
          <el-icon><component :is="collapsed ? Expand : Fold" /></el-icon>
        </button>

        <el-breadcrumb separator="/" class="navbar__crumb">
          <el-breadcrumb-item v-for="c in crumbs" :key="c.text" :to="c.path ? { path: c.path } : undefined">
            {{ c.text }}
          </el-breadcrumb-item>
        </el-breadcrumb>

        <div class="navbar__right">
          <span class="navbar__badge">单店版</span>
          <span class="navbar__user">{{ user.name || "未登录" }}</span>
          <el-button text @click="onLogout">退出</el-button>
        </div>
      </el-header>

      <el-main class="content"><router-view /></el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessageBox } from "element-plus";
import {
  Box, DataLine, Expand, Fold, HomeFilled, Present, PriceTag, Tickets, User,
} from "@element-plus/icons-vue";
import { useUserStore } from "../stores/user";

const route = useRoute();
const router = useRouter();
const user = useUserStore();

const menus = [
  { path: "/dashboard", title: "今日工作台", icon: HomeFilled },
  { path: "/orders", title: "订单管理", icon: Tickets },
  { path: "/service-items", title: "服务项目与价格", icon: PriceTag },
  { path: "/products", title: "纪念品管理", icon: Present },
  { path: "/boarding", title: "骨灰寄存", icon: Box },
  { path: "/customers", title: "客户档案", icon: User },
  { path: "/stats", title: "数据看板", icon: DataLine },
];

const collapsed = ref(false);

// 详情页要回溯到所属菜单：/orders/GD20260910001 应高亮「订单管理」
const currentMenu = computed(() =>
  menus.find((m) => route.path === m.path || route.path.startsWith(`${m.path}/`)));

const activeMenu = computed(() => currentMenu.value?.path ?? route.path);

const crumbs = computed(() => {
  if (!currentMenu.value) return [{ text: route.meta.title || "首页" }];
  const list = [{ text: currentMenu.value.title, path: currentMenu.value.path }];
  if (route.path !== currentMenu.value.path) {
    // 详情页用单号/名字做屑名，比「订单详情」这三个字有用
    list.push({ text: route.params.orderNo || route.params.customerId || route.meta.title || "详情" });
  }
  return list;
});

function toggle() {
  collapsed.value = !collapsed.value;
}

// <1366px 侧栏收窄（PRD §5.6.3）。只在跨越断点时施加，否则会覆盖员工手动选择
let wasNarrow = null;
function syncViewport() {
  const narrow = window.innerWidth < 1366;
  if (narrow !== wasNarrow) {
    collapsed.value = narrow;
    wasNarrow = narrow;
  }
}

async function onLogout() {
  try {
    await ElMessageBox.confirm("确定退出当前账号？", "退出登录", {
      type: "warning",
      confirmButtonText: "退出",
      cancelButtonText: "再想想",
    });
  } catch {
    return;
  }
  user.logout();
  router.push("/login");
}

onMounted(() => {
  syncViewport();
  window.addEventListener("resize", syncViewport);
});
onUnmounted(() => window.removeEventListener("resize", syncViewport));
</script>

<style scoped>
.layout { height: 100vh; }

.sider {
  width: var(--px-w-sider);
  background:
    linear-gradient(180deg, rgba(234, 241, 239, 0.92), rgba(255, 251, 245, 0.96)),
    var(--px-bg-card);
  border-right: 1px solid var(--px-border);
  transition: width var(--px-motion-normal) var(--px-ease-out);
  overflow-x: hidden;
}
.sider.is-collapsed { width: var(--px-w-sider-collapsed); }

.brand {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
  height: var(--px-h-navbar);
  padding: 0 var(--px-sp-4);
  white-space: nowrap;
  border-bottom: 1px solid rgba(201, 205, 212, 0.55);
}
.brand__mark {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  flex-shrink: 0;
  border-radius: var(--px-radius-sm);
  background: linear-gradient(180deg, var(--px-primary), var(--px-primary-pressed));
  color: var(--px-text-inverse);
  font-size: var(--px-fs-base);
  font-weight: 600;
  box-shadow: 0 8px 18px rgba(91, 140, 133, 0.18);
}
.brand__logo {
  width: 18px;
  height: 18px;
  object-fit: contain;
}
.brand__copy {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}
.brand__name {
  font-size: var(--px-fs-md);
  font-weight: 600;
  color: var(--px-text-1);
}
.brand__sub {
  margin-top: 2px;
  font-size: var(--px-fs-xs);
  color: var(--px-text-3);
}

.navbar {
  display: flex;
  align-items: center;
  gap: var(--px-sp-3);
  height: var(--px-h-navbar);
  padding: 0 var(--px-sp-6);
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--px-border);
}
.navbar__icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: 1px solid var(--px-border);
  border-radius: var(--px-radius-sm);
  background: transparent;
  color: var(--px-text-2);
  cursor: pointer;
  transition: all var(--px-motion-fast) linear;
}
.navbar__icon:hover {
  color: var(--px-primary);
  border-color: var(--px-primary);
}
.navbar__icon:focus-visible {
  outline: 2px solid var(--px-primary);
  outline-offset: 2px;
}
.navbar__crumb { flex: 1; min-width: 0; }
.navbar__right {
  display: flex;
  align-items: center;
  gap: var(--px-sp-2);
}
.navbar__badge {
  display: inline-flex;
  align-items: center;
  height: 24px;
  padding: 0 var(--px-sp-2);
  border: 1px solid var(--px-border);
  border-radius: 999px;
  background: var(--px-bg-warm);
  color: var(--px-primary-pressed);
  font-size: var(--px-fs-xs);
  font-weight: 600;
}
.navbar__user {
  font-size: var(--px-fs-sm);
  color: var(--px-text-2);
}

.content {
  background: var(--px-bg-page);
  padding: var(--px-sp-6);
  overflow-y: auto;
}

/* EP 菜单自带右分割线，与 sider 边框重影，去掉 */
.sider :deep(.el-menu) { border-right: none; }
.sider :deep(.el-menu--collapse) { width: var(--px-w-sider-collapsed); }

@media (max-width: 1366px) {
  .content { padding: var(--px-sp-4); }
}
</style>
