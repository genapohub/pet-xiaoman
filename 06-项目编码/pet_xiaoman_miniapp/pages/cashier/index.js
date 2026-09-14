const { fmtMoney } = require("../../utils/format");
const { get, post } = require("../../utils/request");
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
        disabledText: "线上支付暂未开启，可选择到店付款",
      },
      {
        key: "full",
        name: "付全款",
        desc: `¥${fmtMoney(amount)} · 服务完成无需再付款`,
        icon: "/assets/icons/check-primary.png",
        disabled: true,
        disabledText: "线上支付暂未开启，可选择到店付款",
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
    this.loadPayConfig();
  },
  loadPayConfig() {
    get("/api/c/integrations/config", {}, { silentError: true })
      .then((cfg) => {
        const payReady = Boolean(cfg && cfg.payment && cfg.payment.ready);
        const disabledText = cfg?.payment?.enabled
          ? "支付配置未完成，请选择到店付款"
          : "线上支付暂未开启，可选择到店付款";
        const methods = this.data.methods.map((m) => (
          m.key === "offline" ? m : { ...m, disabled: !payReady, disabledText: payReady ? "" : disabledText }
        ));
        this.setData({ payEnabled: payReady, methods });
      })
      .catch(() => {
        const methods = this.data.methods.map((m) => (
          m.key === "offline" ? m : { ...m, disabled: true, disabledText: "支付配置读取失败，请选择到店付款" }
        ));
        this.setData({ payEnabled: false, methods });
      });
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
    if (this.data.selected !== "offline") return this.startWxPay();
    this.setData({ submitting: true });
    wx.navigateTo({
      url: `/pages/order-success/index?order_no=${this.data.orderNo}&pay_text=${encodeURIComponent("到店付款")}`,
      complete: () => this.setData({ submitting: false }),
    });
  },
  startWxPay() {
    this.setData({ submitting: true });
    post("/api/pay/jsapi", { order_no: this.data.orderNo, pay_type: this.data.selected }, { silentError: true })
      .then((params) => new Promise((resolve, reject) => {
        wx.requestPayment({
          timeStamp: params.timeStamp,
          nonceStr: params.nonceStr,
          package: params.package,
          signType: params.signType,
          paySign: params.paySign,
          success: resolve,
          fail: reject,
        });
      }))
      .then(() => wx.navigateTo({
        url: `/pages/order-success/index?order_no=${this.data.orderNo}&pay_text=${encodeURIComponent(this.data.selected === "deposit" ? "定金已支付" : "全款已支付")}`,
      }))
      .catch((err) => {
        const msg = err?.detail || "线上支付暂未开启，可选择到店付款";
        wx.showToast({ title: msg, icon: "none" });
      })
      .finally(() => this.setData({ submitting: false }));
  },
}));
