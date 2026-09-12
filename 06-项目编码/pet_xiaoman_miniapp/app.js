// 入口：多租户白标换肤 + 手机号一键登录。未登录统一进入登录页，登录成功回退续跑原流程。
const { repairDebugBaseURL } = require("./config/env");
const { ensureBrand, saveSlug, slugFromOptions } = require("./utils/brand");

App({
  globalData: { theme: require("./config/theme") }, // 默认品牌；启动后按门店覆盖
  _loginWaiters: [],
  onLaunch(options) {
    repairDebugBaseURL();
    // 门店标识：来自二维码/启动参数，记下后本机后续进入沿用
    const slug = slugFromOptions(options);
    if (slug) saveSlug(slug);
    // 运行时换肤（异步，不阻塞登录判断；页面 onLoad 里 ensureBrand 会复用同一 Promise）
    ensureBrand().catch(() => {});

    const token = wx.getStorageSync("token");
    const customerId = wx.getStorageSync("customer_id");
    if (!(token && customerId)) {
      // 未登录：进入手机号一键登录页（登录成功由 finishLogin 回首页）
      wx.reLaunch({ url: "/pages/login/index" });
    }
  },
  // 当前客户 id（未登录返回 0）；订单/宠物/个人中心等页面取用
  getCustomerId() {
    return Number(wx.getStorageSync("customer_id")) || 0;
  },
  // 供需要登录的接口/页面调用：已登录立即 resolve；未登录跳登录页，登录完成后 resolve
  ensureLogin() {
    const token = wx.getStorageSync("token");
    const customerId = wx.getStorageSync("customer_id");
    if (token && customerId) return Promise.resolve({ token, customer_id: customerId });
    return new Promise((resolve) => {
      this._loginWaiters.push(resolve);
      wx.navigateTo({ url: "/pages/login/index" });
    });
  },
  // 登录页调用：落库 token，唤醒所有等待者，再回到原页面/首页
  finishLogin(data) {
    wx.setStorageSync("token", data.token);
    wx.setStorageSync("customer_id", data.customer_id);
    const waiters = this._loginWaiters;
    this._loginWaiters = [];
    waiters.forEach((r) => r({ token: data.token, customer_id: data.customer_id }));
    if (getCurrentPages().length > 1) wx.navigateBack();
    else wx.reLaunch({ url: "/pages/index/index" });
  },
});
