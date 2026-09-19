// C011 预约/支付成功（对齐画布 47:342，服务 · 二级页）
//
// 说明：本页同时承担「预约已提交（到店付）」与「线上支付成功」两种结果，
// 文案按 pay_text 分流；订单信息不靠 query 传递，而是回查订单接口，
// 保证刷新/二次进入时信息一致（query 只带 order_no 与结果文案）。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    orderNo: "",
    payText: "",
    title: "预约成功",
    statusText: "已预约",
    order: null,
  },

  onLoad(options) {
    const orderNo = options.order_no || "";
    const payText = options.pay_text || "到店付款";
    const isOffline = payText.indexOf("到店") >= 0;
    this.setData({
      orderNo,
      payText,
      title: isOffline ? "预约成功" : "支付成功",
      statusText: isOffline ? "待服务" : "已支付",
    });
    this.load(orderNo);
  },

  goBack() { navbar.back(); },

  load(orderNo) {
    if (!orderNo) return;
    get(`/api/c/orders/${orderNo}`, {}, { silentError: true })
      .then((order) => this.setData({ order }))
      .catch(() => {});
  },

  viewOrder() {
    if (!this.data.orderNo) return;
    go(`/pages/order-detail/index?order_no=${this.data.orderNo}`);
  },
}));
