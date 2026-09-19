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

// 三承诺：宽度 140:117:117（非对称节奏，避免机械三等分）
const PROMISES = [
  { key: "price",  main: true, icon: "shield-primary.png", title: "明码标价", desc: "无隐藏费用" },
  { key: "single", icon: "heart-primary.png",  title: "单独火化", desc: "专属送别" },
  { key: "24h",    icon: "clock-primary.png",  title: "24h 可约", desc: "随时响应" },
];

// 服务入口宫格（2 列）：与画布 Service Grid 4 张卡一致
const ENTRIES = [
  { key: "booking", title: "预约火化", desc: "安心送别", icon: "check-primary.png", url: "/pages/order-create/index" },
  { key: "price",   title: "服务价格", desc: "明码标价", icon: "price-primary.png", url: "/pages/prices/prices" },
  { key: "gift",    title: "纪念品",   desc: "把爱留驻", icon: "box-primary.png",   url: "/pages/products/products" },
  { key: "archive", title: "宠物档案", desc: "记忆永存", icon: "paw-primary.png",   url: "/pages/pets/pets" },
];

Page(brandPage({
  data: {
    nav: navbar.measure(),
    heroes: HEROES,
    heroIndex: 0,
    promises: PROMISES,
    entries: ENTRIES,
  },

  onHeroChange(e) {
    this.setData({ heroIndex: e.detail.current });
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
