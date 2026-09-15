// C003 服务详情 + 科普：基于公开价格接口展示，底部可直接预约该服务。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
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
        this.setData({ item: item || null, loading: false });
      })
      .catch(() => this.setData({ loading: false }));
  },
  goCreate() {
    if (!this.data.item) return;
    go(`/pages/order-create/index?pkg_id=${this.data.item.id}`);
  },
  goPrices() {
    go("/pages/prices/prices");
  },
}));
