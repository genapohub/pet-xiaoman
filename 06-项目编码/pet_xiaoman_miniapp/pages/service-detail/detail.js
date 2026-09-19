// C003 服务详情 + 科普（服务 · 二级页；画布未单列，按《设计风格规范 v2.0》推导）
//
// 定位：价格表上一张卡片的「展开」。家属在这一屏要解决的是「这档到底包含什么、
// 为什么是这个价、我担心的事有没有保障」，故内容顺序 = 价格 → 服务内容 → 节点流程
// → 常见问题 → 主 CTA（预约这一档）。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    item: null,
    loading: true,
    steps: ["电话确认", "上门接宠", "告别仪式", "单独火化", "骨灰交付"],
    faq: [
      { q: "为什么要先看公开价格？", a: "下单时会按当前价格锁价，门店确认后不会临时加价。" },
      { q: "单独火化怎么确认？", a: "服务过程中的关键节点会由门店上传影像，订单时间线可查看。" },
      { q: "可以先不在线支付吗？", a: "可以。当前一期支持到店付款，门店会电话确认预约。" },
    ],
  },

  onLoad(options) {
    this.itemId = Number(options.id || 0);
    get("/api/c/service-items")
      .then((rows) => {
        const item = (rows || []).find((r) => Number(r.id) === this.itemId);
        this.setData({
          item: item ? Object.assign({}, item, {
            priceText: Number(item.price || 0).toFixed(0),
          }) : null,
          loading: false,
        });
      })
      .catch(() => this.setData({ loading: false }));
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
