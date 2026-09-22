// C003 服务详情（服务 · 二级页；对齐画布 81:1）
//
// 定位：价格表上一张卡片的「展开」。家属在这一屏要解决的是「这档到底包含什么、
// 为什么是这个价、我担心的事有没有保障」，故内容顺序 = 主套餐 → 服务流程
// → 服务包含 → 适用情况 → 安心承诺 → 主 CTA。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    item: null,
    loading: true,
    tags: ["明码标价", "到店或接送", "进度可查"],
    flowRows: [
      "01 预约确认：提交预约后，门店 30 分钟内电话确认。",
      "02 到店或接宠：按约定时间到店，或由门店上门接宠。",
      "03 告别服务：整理仪容、陪伴告别，并同步关键进度。",
      "04 交付回访：完成后交付纪念品与影像，支持回访问候。",
    ],
    includeRows: ["预约确认", "上门接宠", "告别整理", "火化留痕"],
    sceneText: "适合需要基础告别、价格清晰、流程陪同的家庭。若需要单独仪式、骨灰盒、纪念品或影像服务，可在预约页加选。",
    promiseText: "费用透明，提交后门店确认报价；服务节点可查，不临时加价；所有纪念品与影像按订单留档。",
    fallbackItem: {
      name: "基础告别套餐",
      weight_tier: "适合家庭小型告别仪式，含接送、整理、基础告别与火化安排。",
      priceText: "800 起",
      id: 0,
    },
  },

  onLoad(options) {
    this.itemId = Number(options.id || 0);
    get("/api/c/service-items")
      .then((rows) => {
        const item = (rows || []).find((r) => Number(r.id) === this.itemId);
        this.setData({
          item: item ? Object.assign({}, item, {
            priceText: Number(item.price || 0).toFixed(0),
          }) : this.data.fallbackItem,
          loading: false,
        });
      })
      .catch(() => this.setData({ item: this.data.fallbackItem, loading: false }));
  },

  goBack() { navbar.back(); },
  goCreate() {
    if (!this.data.item) return;
    go("/pages/order-create/index?pkg_id=" + this.data.item.id);
  },
  goPrices() { go("/pages/prices/prices"); },
  callShop() {
    const phone = this.data.theme && this.data.theme.contactPhone;
    if (!phone) return wx.showToast({ title: "门店电话暂未配置", icon: "none" });
    wx.makePhoneCall({ phoneNumber: phone });
  },
}));
