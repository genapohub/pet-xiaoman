// 入口：微信登录（WX_LOGIN_ENABLED=true 走 code；关闭时轻量注册+dev login，接口语义不变）
const { post } = require("./utils/request");

App({
  globalData: { theme: require("./config/theme") },
  onLaunch() { this.ensureLogin(); },
  ensureLogin() {
    const token = wx.getStorageSync("token");
    const customerId = wx.getStorageSync("customer_id");
    if (token && customerId) return Promise.resolve({ token, customer_id: customerId });

    return new Promise((resolve) => {
      wx.login({
        success: ({ code }) => {
          post("/api/c/auth/login", { code })
            .then((data) => this._save(data, resolve))
            .catch(() => this._legacyLogin(resolve));
        },
        fail: () => this._legacyLogin(resolve),
      });
    });
  },
  _save(data, resolve) {
    wx.setStorageSync("token", data.token);
    wx.setStorageSync("customer_id", data.customer_id);
    resolve(data);
  },
  // 轻量模式：注册客户 → dev login 换 token（后端开关关闭时）
  _legacyLogin(resolve) {
    post("/api/c/customers", { nickname: "微信用户" })
      .then((data) => post("/api/c/auth/login", { customer_id: data.customer_id }))
      .then((data) => this._save(data, resolve))
      .catch(() => resolve({}));
  },
  getCustomerId() {
    return wx.getStorageSync("customer_id") || 0;
  },
});
