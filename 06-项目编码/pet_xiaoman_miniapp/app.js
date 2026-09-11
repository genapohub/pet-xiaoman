// 入口：微信登录（WX_LOGIN_ENABLED=true 走 code；关闭时轻量注册+dev login，接口语义不变）
const { post } = require("./utils/request");
const { repairDebugBaseURL, isDevelopEnv } = require("./config/env");

App({
  globalData: { theme: require("./config/theme") },
  onLaunch() {
    repairDebugBaseURL();
    this.ensureLogin();
  },
  ensureLogin() {
    const token = wx.getStorageSync("token");
    const customerId = wx.getStorageSync("customer_id");
    if (token && customerId) return Promise.resolve({ token, customer_id: customerId });

    if (isDevelopEnv()) return this._legacyLogin();

    return new Promise((resolve) => {
      wx.login({
        success: ({ code }) => {
          post("/api/c/auth/login", { code }, { retryAuth: false, silentError: true })
            .then((data) => this._save(data, resolve))
            .catch(() => this._legacyLogin().then(resolve));
        },
        fail: () => this._legacyLogin().then(resolve),
      });
    });
  },
  _save(data, resolve) {
    wx.setStorageSync("token", data.token);
    wx.setStorageSync("customer_id", data.customer_id);
    if (resolve) resolve(data);
    return data;
  },
  // 轻量模式：注册客户 → dev login 换 token（后端开关关闭时）
  _legacyLogin() {
    return post("/api/c/customers", { nickname: "微信用户" }, { retryAuth: false, silentError: true })
      .then((data) => post("/api/c/auth/login", { customer_id: data.customer_id }, { retryAuth: false, silentError: true }))
      .then((data) => this._save(data))
      .catch((err) => {
        console.warn("[宠小满登录] 开发模式登录失败，请检查 API 服务是否启动，以及 /api/c/customers 与 /api/c/auth/login 是否正常。", err);
        return {};
      });
  },
  getCustomerId() {
    return wx.getStorageSync("customer_id") || 0;
  },
});
