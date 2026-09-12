import { createRouter, createWebHistory } from "vue-router";
import AdminLayout from "../layout/AdminLayout.vue";
import { useUserStore } from "../stores/user";

// B 端页面路由（PRD §5.4：B001-B010，P2 看板后续补）
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../views/login.vue") },
    {
      path: "/",
      component: AdminLayout,
      children: [
        { path: "", redirect: "/dashboard" },
        // 平台超管专属（menuKey=stores）：开店 / 开账号 / 统一配品牌，租户角色菜单里没有这一项
        { path: "stores", component: () => import("../views/platform/StoreList.vue"), meta: { title: "门店管理", menuKey: "stores" } },
        { path: "stores/:storeId", component: () => import("../views/platform/StoreDetail.vue"), meta: { title: "门店详情", menuKey: "stores" } },
        { path: "dashboard", component: () => import("../views/dashboard.vue"), meta: { title: "今日工作台", menuKey: "dashboard" } },
        { path: "orders", component: () => import("../views/order/OrderList.vue"), meta: { title: "订单列表", menuKey: "orders" } },
        { path: "orders/:orderNo", component: () => import("../views/order/OrderDetail.vue"), meta: { title: "订单详情", menuKey: "orders" } },
        { path: "service-items", component: () => import("../views/service/ServiceItems.vue"), meta: { title: "服务项目与价格", menuKey: "service-items" } },
        { path: "products", component: () => import("../views/product/Products.vue"), meta: { title: "纪念品管理", menuKey: "products" } },
        { path: "boarding", component: () => import("../views/boarding/Boarding.vue"), meta: { title: "骨灰寄存", menuKey: "boarding" } },
        { path: "customers", component: () => import("../views/customer/CustomerList.vue"), meta: { title: "客户档案", menuKey: "customers" } },
        { path: "customers/:customerId", component: () => import("../views/customer/CustomerDetail.vue"), meta: { title: "客户详情", menuKey: "customers" } },
        { path: "stats", component: () => import("../views/stats/Stats.vue"), meta: { title: "数据看板", menuKey: "stats" } },
        { path: "staff", component: () => import("../views/staff/StaffList.vue"), meta: { title: "团队成员", menuKey: "staff" } },
        { path: "rbac", component: () => import("../views/rbac/Rbac.vue"), meta: { title: "角色权限", menuKey: "rbac" } },
      ],
    },
  ],
});

router.beforeEach(async (to) => {
  const user = useUserStore();
  if (to.path === "/login") return true;
  if (!user.token) return { path: "/login", query: { redirect: to.fullPath } };
  if (!user.loaded) {
    try {
      await user.fetchMe();
    } catch {
      user.logout();
      return { path: "/login", query: { redirect: to.fullPath } };
    }
  }
  const key = to.meta.menuKey;
  if (key && !user.canMenu(key)) {
    const first = user.menus[0] ? `/${user.menus[0]}` : "/login";
    return first === to.path ? true : first;
  }
  return true;
});

export default router;
