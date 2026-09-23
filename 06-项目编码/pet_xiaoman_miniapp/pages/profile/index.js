// C010 个人中心（对齐画布 2:545，我的一级 tab 页）
//
// 层级：一级 tab 页 → 自绘衬线页头（无返回箭头）、底部自定义胶囊 tabBar。
// 结构按画布 2:545：用户卡 + 6 行菜单。
const { get } = require("../../utils/request");
const { go: navGo } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

const app = getApp();

function maskPhone(phone) {
  const raw = String(phone || "").trim();
  if (/^1\d{10}$/.test(raw)) return raw.slice(0, 3) + "****" + raw.slice(7);
  return raw || "138****0000";
}

function profileNameOf(me) {
  return (me && (me.name || me.nickname)) || "张先生";
}

function syncTabBar(page) {
  if (typeof page.getTabBar !== "function") return;
  const tabBar = page.getTabBar();
  if (tabBar && typeof tabBar.setSelected === "function") {
    tabBar.setSelected("/pages/profile/index");
  }
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    customerId: 0,
    me: null,
    profileName: "张先生",
    profileInitial: "张",
    profilePhone: "138****0000",
    memberLabel: "银牌会员",
    menus: [
      { label: "我的订单", icon: "/assets/ardot/icons/2_567-20260922_083300134.png", chevron: "/assets/ardot/icons/2_573-20260922_083300134.png", url: "/pages/order-list/index" },
      { label: "宠物档案", icon: "/assets/ardot/icons/2_576-20260922_083300135.png", chevron: "/assets/ardot/icons/2_579-20260922_083300135.png", url: "/pages/pets/pets" },
      { label: "纪念品订单", icon: "/assets/ardot/icons/2_582-20260922_083300135.png", chevron: "/assets/ardot/icons/2_587-20260922_083300135.png", url: "/pages/product-orders/index" },
      { label: "骨灰寄存", icon: "/assets/ardot/icons/2_590-20260922_083300136.png", chevron: "/assets/ardot/icons/2_594-20260922_083300136.png", url: "/pages/boarding-query/query" },
      { label: "联系我们", icon: "/assets/ardot/icons/2_597-20260922_083300136.png", chevron: "/assets/ardot/icons/2_600-20260922_083300137.png", action: "call" },
      { label: "设置", icon: "/assets/ardot/icons/2_603-20260922_083300138.png", chevron: "/assets/ardot/icons/2_607-20260922_083300138.png", url: "/pages/settings/index" },
    ],
  },

  onShow() {
    syncTabBar(this);
    // 店名/logo/标语直接读 data.theme —— 由 brandPage 在品牌加载完成后 setData 刷新。
    // （不要在这里读 app.globalData.theme 存成 shopName：首帧它还是平台默认值，
    //   等品牌到位时已经过了 onShow，页面会一直停在默认店名上。）
    this.setData({ customerId: app.getCustomerId() });
    this.loadMe();
  },

  loadMe() {
    if (!app.getCustomerId()) return;
    get("/api/c/auth/me", {}, { silentError: true })
      .then((me) => {
        const name = profileNameOf(me);
        this.setData({
          me,
          profileName: name,
          profileInitial: name.slice(0, 1),
          profilePhone: maskPhone(me && me.phone),
          memberLabel: (me && me.member_level) || "银牌会员",
        });
      })
      .catch(() => {});
  },

  onMenuTap(e) {
    if (e.currentTarget.dataset.action === "call") {
      this.callShop();
      return;
    }
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

}));
