// 页面跳转统一入口
//
// 为什么需要这个文件：微信平台有一条硬约束——
//   wx.navigateTo  **不能**打开 tabBar 页面，调用后静默失败（只在控制台报
//   `navigateTo:fail can not navigateTo a tabbar page`），用户侧表现为「点了没反应」。
// 而 wx.switchTab 又**不支持带 query 参数**。
// 两边夹击，凡是「从 A 页跳到 tabBar 页 B 并带参数」的场景，手写必然踩坑。
//
// 所以统一走 go()：自动识别目标是不是 tabBar 页 → 选对 API → 参数经本地暂存传递。

// 与 app.json 的 tabBar.list 保持一致（改 app.json 时同步这里）
const TAB_PAGES = [
  "/pages/index/index",
  "/pages/order-create/index",
  "/pages/order-list/index",
  "/pages/products/products",
  "/pages/profile/index",
];

const PARAMS_KEY = "nav_params"; // switchTab 无法带参，参数经此中转

function isTabPage(url) {
  return TAB_PAGES.indexOf(String(url).split("?")[0]) !== -1;
}

function parseQuery(query) {
  const out = {};
  if (!query) return out;
  query.split("&").forEach((kv) => {
    const i = kv.indexOf("=");
    if (i === -1) return;
    const k = kv.slice(0, i);
    const v = kv.slice(i + 1);
    try { out[k] = decodeURIComponent(v); } catch (e) { out[k] = v; }
  });
  return out;
}

/**
 * 跳转到任意页面。tabBar 页自动走 switchTab，其余走 navigateTo。
 * @param {string} url 形如 "/pages/order-create/index?pkg_id=3"
 * @returns {Promise} wx API 返回的 Promise（失败时 reject，便于上层兜底）
 */
function go(url) {
  const [path, query] = String(url).split("?");

  if (isTabPage(path)) {
    const params = parseQuery(query);
    if (Object.keys(params).length) wx.setStorageSync(PARAMS_KEY, params);
    return wx.switchTab({ url: path });
  }
  return wx.navigateTo({ url });
}

/**
 * tabBar 页在 onShow 里调它取参数（onLoad 对已存在的 tabBar 页不会再触发）。
 * 取完即清，避免下次误读旧参数。
 */
function takeParams() {
  const params = wx.getStorageSync(PARAMS_KEY);
  if (params) wx.removeStorageSync(PARAMS_KEY);
  return params || {};
}

module.exports = { go, isTabPage, takeParams, TAB_PAGES, PARAMS_KEY };
