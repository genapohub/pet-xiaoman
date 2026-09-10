// 请求封装：自动带 X-Customer-Token；401 清缓存重新登录（沿用宠宝树 data 解包经验）
const { baseURL } = require("../config/env");

function buildHeader() {
  const token = wx.getStorageSync("token");
  return token ? { "X-Customer-Token": token } : {};
}

function handle401() {
  wx.removeStorageSync("token");
  wx.removeStorageSync("customer_id");
  getApp().ensureLogin();
}

function request(path, method = "GET", data = {}) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${baseURL()}${path}`,
      method,
      data,
      header: buildHeader(),
      success(res) {
        if (res.statusCode === 401) {
          handle401();
          return reject(res);
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data.data !== undefined ? res.data.data : res.data);
        } else {
          wx.showToast({ title: res.data?.detail || res.data?.message || "请求失败", icon: "none" });
          reject(res);
        }
      },
      fail(err) {
        wx.showToast({ title: "网络异常，请稍后重试", icon: "none" });
        reject(err);
      },
    });
  });
}

module.exports = { get: (p, d) => request(p, "GET", d), post: (p, d) => request(p, "POST", d) };
