// C001 品牌首页（对齐画布 2:84）
//
// 结构：品牌头图轮播（3 屏）→ 三承诺 → 服务入口宫格 → 今日寄语 → 门店信息卡。
// 门店信息卡不在画布里，但《C 端信息架构 V2.0》§3 首页明确要求「门店信息卡（电话直呼）」，
// 且这是 C 端唯一的电话入口，故保留（样式与其它卡片同源）。
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

// 头图轮播：文案与画布 3 张 Slide 逐字一致
const HEROES = [
  { key: "brand",   brand: "宠小满", title: "温柔送别，不失温度", slogan: "爱意小满，不留遗憾" },
  { key: "price",   eyebrow: "透明价格", title: "明码标价，安心托付", slogan: "每一程，都看得见" },
  { key: "memory",  eyebrow: "温柔纪念", title: "纪念，是最好的告别", slogan: "为爱留一处温柔归处" },
];

// 三承诺：图标直接使用 Ardot 导出的节点资源，避免近似替代
const PROMISES = [
  { key: "price", icon: "/assets/ardot/icons/2_98-20260922_083300113.png", title: "明码标价", desc: "无隐藏费用" },
  { key: "single", icon: "/assets/ardot/icons/2_104-20260922_083300123.png", title: "单独火化", desc: "专属送别" },
  { key: "24h", icon: "/assets/ardot/icons/2_110-20260922_083300123.png", title: "24h 可约", desc: "随时响应" },
];

// 服务入口宫格（2 列）：与画布 Service Grid 4 张卡一致
const ENTRIES = [
  { key: "booking", title: "预约火化", desc: "安心送别", icon: "/assets/ardot/icons/2_117-20260922_083300123.png", url: "/pages/order-create/index" },
  { key: "price", title: "服务价格", desc: "明码标价", icon: "/assets/ardot/icons/2_123-20260922_083300124.png", url: "/pages/prices/prices" },
  { key: "gift", title: "纪念品", desc: "把爱留驻", icon: "/assets/ardot/icons/2_128-20260922_083300124.png", url: "/pages/products/products" },
  { key: "archive", title: "宠物档案", desc: "记忆永存", icon: "/assets/ardot/icons/2_134-20260922_083300124.png", url: "/pages/pets/pets" },
];

function heroesWithActive(activeIndex) {
  return HEROES.map((item, index) => {
    const active = index === activeIndex;
    return Object.assign({}, item, { active, dotClass: active ? "dot--on" : "" });
  });
}

function syncTabBar(page) {
  if (typeof page.getTabBar !== "function") return;
  const tabBar = page.getTabBar();
  if (tabBar && typeof tabBar.setSelected === "function") {
    tabBar.setSelected("/pages/index/index");
  }
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    heroes: heroesWithActive(0),
    heroIndex: 0,
    promises: PROMISES,
    entries: ENTRIES,
    storeIcons: {
      phone: "/assets/ardot/icons/82_3-20260922_083300125.png",
      address: "/assets/ardot/icons/82_7-20260922_083300126.png",
      clock: "/assets/ardot/icons/82_12-20260922_083300127.png",
      chevron: "/assets/ardot/icons/82_5-20260922_083300126.png",
    },
  },

  onShow() {
    syncTabBar(this);
  },

  onHeroChange(e) {
    const current = e.detail.current || 0;
    this.setData({ heroIndex: current, heroes: heroesWithActive(current) });
  },

  goEntry(e) {
    const item = ENTRIES[e.currentTarget.dataset.idx];
    if (item) go(item.url);
  },

  // 唯一电话入口：24h 可约是核心承诺，未配置电话时给出可执行的提示而不是静默失败
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },

  // 地址复制：门店详情页尚未提供经纬度，导航能力待后端补 lat/lng 后再接 wx.openLocation
  copyAddress() {
    const addr = this.data.theme && this.data.theme.contactAddress;
    if (!addr) return;
    wx.setClipboardData({ data: addr, success: () => wx.showToast({ title: "地址已复制", icon: "none" }) });
  },
}));
