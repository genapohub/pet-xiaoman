// C010 个人中心（菜单聚合）
const { get } = require("../../utils/request");
const { go: navGo } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

const app = getApp();

Page(brandPage({
  data: {
    customerId: 0,
    me: null,
    menus: [
      { label: "个人资料", icon: "/assets/icons/tab-user.png", url: "/pages/profile-detail/detail" },
      { label: "我的订单", icon: "/assets/icons/tab-order.png", url: "/pages/order-list/index" },
      { label: "宠物档案", icon: "/assets/icons/paw.png", url: "/pages/pets/pets" },
      { label: "骨灰寄存查询", icon: "/assets/icons/box.png", url: "/pages/boarding-query/query" },
      { label: "服务价格表", icon: "/assets/icons/price.png", url: "/pages/prices/prices" },
      { label: "关于我们的承诺", icon: "/assets/icons/shield.png", url: "/pages/about-promise/detail" },
    ],
  },
  onShow() {
    // 店名/logo/标语直接读 data.theme —— 由 brandPage 在品牌加载完成后 setData 刷新。
    // （不要在这里读 app.globalData.theme 存成 shopName：首帧它还是平台默认值，
    //   等品牌到位时已经过了 onShow，页面会一直停在默认店名上。）
    this.setData({ customerId: app.getCustomerId() });
    this.loadMe();
  },
  loadMe() {
    if (!app.getCustomerId()) return;
    get("/api/c/auth/me", {}, { silentError: true })
      .then((me) => this.setData({ me }))
      .catch(() => {});
  },
  go(e) {
    const url = e.currentTarget.dataset.url;
    // 「我的订单」指向 tabBar 页，必须由 navGo 内部改用 switchTab
    navGo(url);
  },
  logout() {
    wx.showModal({
      title: "退出登录",
      content: "退出后，本机将清除登录态。再次查看订单或预约时需要重新授权登录。",
      confirmText: "退出",
      confirmColor: "#D54941",
      success: (res) => {
        if (res.confirm) app.logout();
      },
    });
  },
}));
