// C010 个人中心（菜单聚合）
const { go: navGo } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

const app = getApp();

Page(brandPage({
  data: {
    customerId: 0,
    menus: [
      { label: "我的订单", icon: "/assets/icons/tab-order.png", url: "/pages/order-list/index" },
      { label: "宠物档案", icon: "/assets/icons/paw.png", url: "/pages/pets/pets" },
      { label: "骨灰寄存查询", icon: "/assets/icons/box.png", url: "/pages/boarding-query/query" },
      { label: "服务价格表", icon: "/assets/icons/price.png", url: "/pages/prices/prices" },
      { label: "关于我们的承诺", icon: "/assets/icons/info.png", url: "" },
    ],
  },
  onShow() {
    // 店名/logo/标语直接读 data.theme —— 由 brandPage 在品牌加载完成后 setData 刷新。
    // （不要在这里读 app.globalData.theme 存成 shopName：首帧它还是平台默认值，
    //   等品牌到位时已经过了 onShow，页面会一直停在默认店名上。）
    this.setData({ customerId: app.getCustomerId() });
  },
  go(e) {
    const url = e.currentTarget.dataset.url;
    if (!url) return wx.showToast({ title: "内容筹备中", icon: "none" });
    // 「我的订单」指向 tabBar 页，必须由 navGo 内部改用 switchTab
    navGo(url);
  },
}));
