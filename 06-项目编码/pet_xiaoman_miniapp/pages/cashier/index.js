const { fmtMoney } = require("../../utils/format");
const { brandPage } = require("../../utils/brand");

Page(brandPage({
  data: {
    orderNo: "",
    amountText: "0.00",
    selected: "offline",
    payEnabled: false,
    methods: [],
    submitting: false,
    actionText: "提交预约",
  },
  onLoad(options) {
    const amount = Number(options.amount || 0);
    const deposit = Math.max(Math.round(amount * 0.2 * 100) / 100, amount > 0 ? 100 : 0);
    const realDeposit = Math.min(deposit, amount);
    const remain = Math.max(amount - realDeposit, 0);
    const methods = [
      {
        key: "deposit",
        name: "付定金",
        desc: `定金 ¥${fmtMoney(realDeposit)} · 尾款 ¥${fmtMoney(remain)} 到店支付`,
        icon: "/assets/icons/shield-primary.png",
        disabled: true,
        disabledText: "线上支付暂未开启",
      },
      {
        key: "full",
        name: "付全款",
        desc: `¥${fmtMoney(amount)} · 服务完成无需再付款`,
        icon: "/assets/icons/check-primary.png",
        disabled: true,
        disabledText: "线上支付暂未开启",
      },
      {
        key: "offline",
        name: "到店付款",
        desc: "服务完成时到店支付，门店会电话确认",
        icon: "/assets/icons/location-primary.png",
        disabled: false,
        disabledText: "",
      },
    ];
    this.setData({
      orderNo: options.order_no || "",
      amountText: fmtMoney(amount),
      methods,
    });
    this.updateActionText("offline");
  },
  selectMethod(e) {
    const key = e.currentTarget.dataset.key;
    const method = this.data.methods.find((m) => m.key === key);
    if (!method) return;
    if (method.disabled) {
      wx.showToast({ title: method.disabledText || "暂不可选", icon: "none" });
      return;
    }
    this.setData({ selected: key });
    this.updateActionText(key);
  },
  updateActionText(key) {
    const textMap = {
      deposit: "确认支付定金",
      full: "确认支付全款",
      offline: "提交预约",
    };
    this.setData({ actionText: textMap[key] || "提交预约" });
  },
  submit() {
    if (!this.data.orderNo) {
      wx.showToast({ title: "订单信息缺失", icon: "none" });
      return;
    }
    if (this.data.selected !== "offline") {
      wx.showToast({ title: "支付失败，可重试或换到店付", icon: "none" });
      return;
    }
    this.setData({ submitting: true });
    wx.navigateTo({
      url: `/pages/order-success/index?order_no=${this.data.orderNo}&pay_text=${encodeURIComponent("到店付款")}`,
      complete: () => this.setData({ submitting: false }),
    });
  },
}));
