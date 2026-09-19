// C002/C003 价格表（全量单项价公开，PRD §5.2.1 差异化核心）
//
// 层级：服务 Tab 之下的二级页 → Header 带返回箭头、底部为「不加价」承诺条给 tabBar 让位。
// 三分类（套餐 / 单项 / 加购）共用同一套价格卡模板，由 current 驱动；顾问卡仅套餐页出现。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

const TABS = ["套餐", "单项", "加购"];

/**
 * 价格卡装饰：把「推荐位」与「说明行」在 JS 里算好。
 * WXML 绑定不支持函数调用与可选链（编译期 Bad attr），所有派生字段必须预先落数据。
 */
function decorate(list, active) {
  return (list || []).map((it, i) => ({
    id: it.id,
    name: it.name,
    // 画布价格不带小数（¥680 / ¥880）；后端是 float，统一取整展示避免 ¥680.00 的笨重感
    priceText: Number(it.price || 0).toFixed(0),
    desc: it.weight_tier || "",
    // 套餐第 2 档打「多数家庭的选择」（画布 2:199 的推荐徽章）；其它分类不打，避免误当促销
    recommend: active === "套餐" && i === 1,
  }));
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    tabs: TABS,
    active: "套餐",
    groups: {},
    current: [],
    loading: true,
  },

  onLoad() {
    get("/api/c/service-items").then((rows) => {
      const groups = {};
      for (const r of (rows || [])) {
        if (!groups[r.type]) groups[r.type] = [];
        groups[r.type].push(r);
      }
      this.setData({
        groups,
        current: decorate(groups[this.data.active], this.data.active),
        loading: false,
      });
    }).catch(() => this.setData({ loading: false }));
  },

  switchTab(e) {
    const active = e.currentTarget.dataset.tab;
    this.setData({ active, current: decorate(this.data.groups[active], active) });
  },

  goBack() { navbar.back(); },

  // 选套餐 → 直接进预约并预选；看单项 → 进服务详情（科普 + 预约入口）
  goCreate(e) {
    go(`/pages/order-create/index?pkg_id=${e.currentTarget.dataset.id}`);
  },
  goDetail(e) {
    go(`/pages/service-detail/detail?id=${e.currentTarget.dataset.id}`);
  },

  // 「找顾问聊聊」：不确定选哪档时给人工出口，不推销（画布顾问卡文案）
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
