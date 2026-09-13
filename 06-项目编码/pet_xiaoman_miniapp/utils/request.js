// 请求封装：自动带 X-Customer-Token；401 清缓存重新登录（沿用宠宝树 data 解包经验）
const { baseURL } = require("../config/env");
const { DEFAULT_STORE_SLUG } = require("../config/store");

function buildHeader() {
  const token = wx.getStorageSync("token");
  const header = {};
  if (token) header["X-Customer-Token"] = token;
  // 多租户门店上下文：扫码/链接进入后 utils/brand.js 会保存 store_slug。
  // 独立 AppID 搜索进入时没有参数，兜底使用本发布包默认门店 slug。
  // 所有 C 端业务接口都带上它，才能读取对应门店的价格、商品、订单与档案。
  const slug = wx.getStorageSync("store_slug") || DEFAULT_STORE_SLUG;
  if (slug) header["X-Store-Slug"] = slug;
  return header;
}

function clearLogin() {
  wx.removeStorageSync("token");
  wx.removeStorageSync("customer_id");
}

function messageFromResponse(res) {
  return res.data?.detail || res.data?.message || "请求失败";
}

function request(path, method = "GET", data = {}, options = {}) {
  return new Promise((resolve, reject) => {
    const apiBase = baseURL();
    if (apiBase.includes(":8000")) {
      console.warn(`[门店接口请求] 当前仍在访问旧端口 8000：${apiBase}。请在微信开发者工具控制台执行 wx.removeStorageSync('debug_base_url') 后重新编译。`);
    }
    wx.request({
      url: `${apiBase}${path}`,
      method,
      data,
      header: buildHeader(),
      success(res) {
        if (res.statusCode === 401) {
          clearLogin();
          if (options.retryAuth === false) return reject(res);
          console.warn(`[门店登录] ${path} 返回 401，正在重新登录并重试一次。`);
          return getApp().ensureLogin()
            .then((loginData) => {
              if (!loginData?.token) throw res;
              return request(path, method, data, { ...options, retryAuth: false });
            })
            .then(resolve)
            .catch((err) => {
              if (!options.silentError) {
                wx.showToast({ title: "登录已过期，请重试", icon: "none" });
              }
              reject(err);
            });
        }
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data.data !== undefined ? res.data.data : res.data);
        } else {
          if (!options.silentError) wx.showToast({ title: messageFromResponse(res), icon: "none" });
          reject(res);
        }
      },
      fail(err) {
        if (!options.silentError) wx.showToast({ title: "网络异常，请稍后重试", icon: "none" });
        reject(err);
      },
    });
  });
}

module.exports = {
  get: (p, d, options) => request(p, "GET", d, options),
  post: (p, d, options) => request(p, "POST", d, options),
  // 手机号一键登录：dev 走 dev_phone，真机走 phone_code（getPhoneNumber 返回）
  phoneLogin: (payload) => request("/api/c/auth/phone-login", "POST", payload),
  // 门店白标（多租户换肤）：按门店标识拉 logo/主色/店名；缺失不弹错（回退默认品牌）
  getStoreProfile: (slug) =>
    request("/api/c/store/profile", "GET", slug ? { slug } : {}, { silentError: true }),
};
