// C012 收银台（对齐画布 47:281，服务 · 二级页）
//
// 口径（重要）：一期 `PAY_ENABLED=false`，线上支付未开通 → 定金/全款两项默认 disabled，
// 默认选中「到店付款」并直接进成功页。开支付开关后本页无需改动即自动可用（方法项由
// `/api/c/integrations/config` 的 payment.ready 决定），这是「可空转」设计的落点。
const { fmtMoney } = require("../../utils/format");
const { get, post } = require("../../utils/request");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    orderNo: "",
    amountText: "0.00",
    selected: "offline",
    payEnabled: false,
    methods: [],
    feeRows: [],
    submitting: false,
    actionText: "提交预约",
  },

  onLoad(options) {
    const amount = Number(options.amount || 0);
    // 定金按 20% 计、下限 100；不足全额时不得超过订单金额（小额单直接全款逻辑）
    const deposit = Math.max(Math.round(amount * 0.2 * 100) / 100, amount > 0 ? 100 : 0);
    const realDeposit = Math.min(deposit, amount);
    const remain = Math.max(amount - realDeposit, 0);
    this._amounts = { amount, deposit: realDeposit, remain };
    const methods = [
      {
        key: "deposit",
        name: "付定金",
        desc: `定金 ¥${fmtMoney(realDeposit)} · 尾款 ¥${fmtMoney(remain)} 到店支付`,
        disabled: true,
        disabledText: "线上支付暂未开启，可选择到店付款",
      },
      {
        key: "full",
        name: "付全款",
        desc: `¥${fmtMoney(amount)} · 服务完成无需再付款`,
        disabled: true,
        disabledText: "线上支付暂未开启，可选择到店付款",
      },
      {
        key: "offline",
        name: "到店付款",
        desc: "服务完成时到店支付，门店会电话确认",
        disabled: false,
        disabledText: "",
      },
    ];
    this.setData({
      orderNo: options.order_no || "",
      amountText: fmtMoney(amount),
      methods,
    });
    this.updateSelection("offline");
    this.loadPayConfig();
  },

  goBack() { navbar.back(); },

  loadPayConfig() {
    get("/api/c/integrations/config", {}, { silentError: true })
      .then((cfg) => {
        const payReady = Boolean(cfg && cfg.payment && cfg.payment.ready);
        const disabledText = (cfg && cfg.payment && cfg.payment.enabled)
          ? "支付配置未完成，请选择到店付款"
          : "线上支付暂未开启，可选择到店付款";
        this.applyPayReady(payReady, disabledText);
      })
      .catch(() => this.applyPayReady(false, "支付配置读取失败，请选择到店付款"));
  },

  applyPayReady(payReady, disabledText) {
    const methods = this.data.methods.map((m) => (
      m.key === "offline" ? m : Object.assign({}, m, {
        disabled: !payReady,
        disabledText: payReady ? "" : disabledText,
      })
    ));
    this.setData({ payEnabled: payReady, methods });
  },

  selectMethod(e) {
    const key = e.currentTarget.dataset.key;
    const method = this.data.methods.find((m) => m.key === key);
    if (!method) return;
    if (method.disabled) {
      wx.showToast({ title: method.disabledText || "暂不可选", icon: "none" });
      return;
    }
    this.updateSelection(key);
  },

  updateSelection(key) {
    const textMap = {
      deposit: "支付定金",
      full: "支付全款",
      offline: "提交预约",
    };
    this.setData({ selected: key, actionText: textMap[key] || "提交预约" });
    this.recalcFees(key);
  },

  // 费用明细：用真实金额推导，不写死文案
  recalcFees(key) {
    const a = this._amounts || { amount: 0, deposit: 0, remain: 0 };
    const payNow = key === "deposit" ? a.deposit : (key === "full" ? a.amount : 0);
    const payLater = Math.max(a.amount - payNow, 0);
    this.setData({
      feeRows: [
        { l: "服务金额", v: `¥${fmtMoney(a.amount)}` },
        { l: key === "offline" ? "线上支付" : "本次支付", v: `¥${fmtMoney(payNow)}` },
        { l: "到店支付", v: `¥${fmtMoney(payLater)}` },
      ],
    });
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
        wx.showToast({
          title: (err && err.detail) || "线上支付暂未开启，可选择到店付款",
          icon: "none",
        });
      })
      .finally(() => this.setData({ submitting: false }));
  },
}));
