// C000 登录（Ardot 2:60 一比一复刻）。
const { phoneLogin } = require("../../utils/request");
const { isDevelopEnv } = require("../../config/env");
const { brandPage } = require("../../utils/brand");
const navbar = require("../../utils/navbar");

Page(brandPage({
  data: {
    nav: navbar.measure(),
    dev: false,
    loading: false,
  },
  onLoad() {
    this.setData({ dev: isDevelopEnv() });
  },
  onGetPhone(e) {
    const { code: phoneCode, errMsg } = e.detail;
    if (errMsg !== "getPhoneNumber:ok" || !phoneCode) {
      wx.showToast({ title: "已取消授权", icon: "none" });
      return;
    }
    wx.login({
      success: (res) => {
        this._doLogin({ phone_code: phoneCode, code: res.code || "" }, "授权登录失败，请重试");
      },
      fail: () => this._doLogin({ phone_code: phoneCode }, "授权登录失败，请重试"),
    });
  },
  onPhoneLogin() {
    if (this.data.loading) return;
    if (this.data.dev) {
      this.onDevLogin();
      return;
    }
    wx.showToast({ title: "手机号登录即将开放", icon: "none" });
  },
  onDevLogin() {
    this._doLogin({ dev_phone: "13800000000" }, "开发登录失败，请重试");
  },
  _doLogin(payload, failTip) {
    if (this.data.loading) return;
    this.setData({ loading: true });
    phoneLogin(payload)
      .then((data) => getApp().finishLogin(data))
      .catch(() => {
        wx.showToast({ title: failTip, icon: "none" });
        this.setData({ loading: false });
      });
  },
}));
