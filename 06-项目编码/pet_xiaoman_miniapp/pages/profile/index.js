// C010 个人中心（对齐画布 2:545，我的一级 tab 页）
//
// 层级：一级 tab 页 → 自绘衬线页头（无返回箭头）、底部原生 tabBar。
// 结构修复（原自检报告「底部 39% 空白」）：补「更多」分组，把「关于与承诺」等
// 已建页面接成真实入口——空白是表象，真问题是「我的」缺下半区。
const { get } = require("../../utils/request");
const { go: navGo } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

const app = getApp();

Page(brandPage({
  data: {
    nav: navbar.measure(),
    customerId: 0,
    me: null,
    // 分三组：先「我的事」（订单/档案），再「我的资料」，最后「关于我们」——信息层级由高到低
    groups: [
      {
        key: "service",
        items: [
          { label: "我的订单", icon: "/assets/icons/tab-order.png", url: "/pages/order-list/index" },
          { label: "纪念品订单", icon: "/assets/icons/box.png", url: "/pages/product-orders/index" },
          { label: "宠物档案", icon: "/assets/icons/paw.png", url: "/pages/pets/pets" },
          { label: "骨灰寄存查询", icon: "/assets/icons/box.png", url: "/pages/boarding-query/query" },
        ],
      },
      {
        key: "profile",
        items: [
          { label: "个人资料", icon: "/assets/icons/tab-user.png", url: "/pages/profile-detail/detail" },
        ],
      },
      {
        key: "about",
        items: [
          { label: "服务价格表", icon: "/assets/icons/price.png", url: "/pages/prices/prices" },
          { label: "关于与承诺", icon: "/assets/icons/shield.png", url: "/pages/about-promise/detail" },
        ],
      },
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
    // 菜单统一走 navGo：tabBar 页（如「服务价格表」已降为二级页）自动判定跳转方式
    navGo(url);
  },

  // 在线客服：一期用门店电话兜底（不虚构在线客服能力）
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
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
