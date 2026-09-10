// C010 个人中心（菜单聚合）
const { go: navGo } = require("../../utils/nav");

const app = getApp();

Page({
  data: {
    customerId: 0,
    shopName: "",
    menus: [
      { label: "我的订单", icon: "/assets/icons/tab-order.png", url: "/pages/order-list/index" },
      { label: "宠物档案", icon: "/assets/icons/paw.png", url: "/pages/pets/pets" },
      { label: "骨灰寄存查询", icon: "/assets/icons/box.png", url: "/pages/boarding-query/query" },
      { label: "服务价格表", icon: "/assets/icons/price.png", url: "/pages/prices/prices" },
      { label: "关于我们的承诺", icon: "/assets/icons/info.png", url: "" },
    ],
  },
  onShow() {
    this.setData({ customerId: app.getCustomerId(), shopName: app.globalData.theme.shopName });
  },
  go(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return wx.showToast({ title: "内容筹备中", icon: "none" });
    // 「我的订单」指向 tabBar 页，必须由 navGo 内部改用 switchTab
    navGo(url);
  },
});
