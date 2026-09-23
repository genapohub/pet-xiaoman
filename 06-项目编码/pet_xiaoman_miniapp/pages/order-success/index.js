// C011 预约/支付成功（对齐画布 47:342，服务 · 二级页）
//
// 说明：本页同时承担「预约已提交（到店付）」与「线上支付成功」两种结果，
// 文案按 pay_text 分流；订单信息不靠 query 传递，而是回查订单接口，
// 保证刷新/二次进入时信息一致（query 只带 order_no 与结果文案）。
const { get } = require("../../utils/request");
const { go } = require("../../utils/nav");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");
const { fmtMoney } = require("../../utils/format");

function fmtAmount(v) {
  return Number(v || 0).toFixed(0);
}

function fmtExpect(v, offline) {
  if (!v) return offline ? "09-15 上午" : "09-18 10:00";
  const s = String(v);
  const md = s.slice(5, 10);
  const hm = s.slice(11, 16);
  if (!offline) return `${md} ${hm || "10:00"}`;
  const h = Number((hm || "10:00").slice(0, 2));
  return `${md} ${h < 12 ? "上午" : "下午"}`;
}

Page(brandPage({
  data: {
    nav: navbar.measure(),
    orderNo: "",
    payText: "",
    title: "预约成功",
    isOffline: true,
    statusText: "已预约",
    resultAmountText: "0",
    orderInfoRows: [],
    serviceRows: [],
    noteTitle: "服务承诺",
    noteRows: [],
    order: null,
  },

  onLoad(options) {
    const orderNo = options.order_no || "";
    let payText = options.pay_text || "到店付款";
    try { payText = decodeURIComponent(payText); } catch (e) { /* 原样 */ }
    const isOffline = payText.indexOf("到店") >= 0;
    const isDeposit = payText.indexOf("定金") >= 0;
    this.setData({
      orderNo,
      payText,
      title: isOffline ? "预约成功" : "支付成功",
      isOffline,
      statusText: isOffline ? "已预约" : (isDeposit ? "定金已付" : "已支付"),
      noteTitle: isOffline ? "服务承诺" : "后续安排",
    });
    this.load(orderNo);
  },

  goBack() { navbar.back(); },

  load(orderNo) {
    if (!orderNo) return;
    get(`/api/c/orders/${orderNo}`, {}, { silentError: true })
      .then((order) => this.applyOrder(order))
      .catch(() => {});
  },

  applyOrder(order) {
    const isOffline = this.data.isOffline;
    const isDeposit = this.data.payText.indexOf("定金") >= 0;
    const total = Number(order && order.total_amount || 0);
    const deposit = Math.min(Math.max(Math.round(total * 0.2), total > 0 ? 100 : 0), total);
    const paid = isOffline ? total : (isDeposit ? deposit : total);
    const remain = Math.max(total - paid, 0);
    const serviceName = (order && order.pkg_name) || (isOffline ? "单独火化 · 中型" : "基础告别套餐");
    const expectText = fmtExpect(order && order.expect_time, isOffline);

    const orderInfoRows = isOffline ? [
      { l: "服务项目", v: serviceName },
      { l: "期望时间", v: expectText },
      { l: "支付方式", v: "到店付款" },
    ] : [
      { l: "支付方式", v: "微信支付" },
      { l: "支付内容", v: isDeposit ? "服务定金" : "服务全款" },
      { l: "到店尾款", v: `¥${fmtMoney(remain)}` },
    ];

    const serviceRows = isOffline ? [
      `${serviceName}`,
      "上门接运 · 专车",
      "影像档案 · 全程可回看",
    ] : [
      `服务项目 · ${serviceName}`,
      `预约时间 · ${expectText}`,
      order && order.address ? "接送方式 · 上门接宠" : "接送方式 · 上门接宠",
    ];

    const noteRows = isOffline ? [
      "服务关键节点将上传影像，可在进度实时查看",
      "门店将在 30 分钟内电话确认时间与细节",
      "全程温柔、专业、克制",
    ] : [
      "门店会电话确认接宠时间与地址",
      "服务进度可在订单详情实时查看",
      "尾款将在到店或服务完成时结清",
    ];

    this.setData({
      order,
      resultAmountText: fmtAmount(paid),
      orderInfoRows,
      serviceRows,
      noteRows,
    });
  },

  viewOrder() {
    if (!this.data.orderNo) return;
    go(`/pages/order-detail/index?order_no=${this.data.orderNo}`);
  },
}));
