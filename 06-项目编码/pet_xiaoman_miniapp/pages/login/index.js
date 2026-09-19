// C000 登录（对齐画布 2:60）
//
// 版式见 index.wxml 顶部说明（纸感底 / 顶对齐 / 品牌行 / Spacer 120px / 主 h56 + 次 h52）。
// 登录页也接白标：顾客扫哪家店的码，就在哪家的品牌下登录。
// 店名/logo/标语统一读 data.theme（brandPage 注入并随品牌加载刷新），
// 不在这里缓存成 shopName —— 否则首帧拿到的是平台默认值，之后再也不会更新。
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
  // 运营商授权手机号一键登录（真机 / 体验版）—— 对应画布主按钮「微信授权登录」
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
  // 本地联调兜底：直接传 dev 手机号。
  // 一期没有独立短信验证码通道，故画布上的次按钮「手机号登录」只在开发环境出现。
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
