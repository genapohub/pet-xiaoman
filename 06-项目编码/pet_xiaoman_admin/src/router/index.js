import { createRouter, createWebHistory } from "vue-router";
import AdminLayout from "../layout/AdminLayout.vue";

// B 端页面路由（PRD §5.4：B001-B010，P2 看板后续补）
export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", component: () => import("../views/login.vue") },
    {
      path: "/",
      component: AdminLayout,
      children: [
        { path: "", redirect: "/dashboard" },
        { path: "dashboard", component: () => import("../views/dashboard.vue"), meta: { title: "今日工作台" } },
        { path: "orders", component: () => import("../views/order/OrderList.vue"), meta: { title: "订单列表" } },
        { path: "orders/:orderNo", component: () => import("../views/order/OrderDetail.vue"), meta: { title: "订单详情" } },
        { path: "service-items", component: () => import("../views/service/ServiceItems.vue"), meta: { title: "服务项目与价格" } },
        { path: "products", component: () => import("../views/product/Products.vue"), meta: { title: "纪念品管理" } },
        { path: "boarding", component: () => import("../views/boarding/Boarding.vue"), meta: { title: "骨灰寄存" } },
        { path: "customers", component: () => import("../views/customer/CustomerList.vue"), meta: { title: "客户档案" } },
        { path: "customers/:customerId", component: () => import("../views/customer/CustomerDetail.vue"), meta: { title: "客户详情" } },
        { path: "stats", component: () => import("../views/stats/Stats.vue"), meta: { title: "数据看板" } },
      ],
    },
  ],
});
