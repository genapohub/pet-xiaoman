// 门店白标（多租户「单小程序运行时换肤」+「每店独立 AppID 默认入口」）。
//
// 进入时按门店标识（slug）拉取该店白标，运行时替换 logo / 主色 / 店名。
// 门店标识来源优先级：
//   启动 query.slug → 扫码 query.scene → 包内 DEFAULT_STORE_SLUG → 本地记忆 → 空（后端默认门店）
//
// 换肤落点：globalData.theme（页面读它渲染）+ tabBar 选中色（wx.setTabBarStyle）。
const { getStoreProfile } = require("./request");
const { absUrl } = require("./url");
const DEFAULT_THEME = require("../config/theme");
const STORE_CONFIG = require("../config/store");

const SLUG_KEY = "store_slug";
let _cached = null;
let _promise = null;

function normalizeSlug(slug) {
  return typeof slug === "string" ? slug.trim() : "";
}

function defaultStoreSlug() {
  return normalizeSlug(STORE_CONFIG.DEFAULT_STORE_SLUG);
}

function cachedSlug() {
  try { return wx.getStorageSync(SLUG_KEY) || ""; } catch (e) { return ""; }
}

function saveSlug(slug) {
  const next = normalizeSlug(slug);
  if (!next) return "";
  const prev = currentSlug();
  try { wx.setStorageSync(SLUG_KEY, next); } catch (e) { /* 忽略 */ }
  if (prev !== next) {
    resetBrand();
  }
  return next;
}

function currentSlug() {
  return cachedSlug() || defaultStoreSlug();
}

// 从 onLaunch/onShow 的 options 里解析门店标识
function slugFromOptions(options) {
  if (!options) return "";
  if (options.query && options.query.slug) return normalizeSlug(options.query.slug);
  if (options.query && options.query.scene) {
    let scene = options.query.scene;
    try { scene = decodeURIComponent(scene); } catch (e) { /* 原样 */ }
    if (scene.indexOf("=") >= 0) {
      const pair = scene.split("&").find((p) => p.indexOf("slug=") === 0);
      if (pair) return normalizeSlug(pair.slice("slug=".length));
    }
    return normalizeSlug(scene); // 扫码直接传 slug 的情况
  }
  // 注意：微信 launch options.scene 是入口场景值（如 1001），不是业务二维码参数。
  // 把它当 slug 会请求 /store/profile?slug=1001，导致普通搜索/开发者工具启动时品牌 404。
  return "";
}

function mergeTheme(base, profile) {
  const theme = Object.assign({}, base);
  if (profile) {
    // 这四项必须"显式覆盖"而不是"有值才覆盖"：
    // 切换门店时 base 可能是上一家的品牌，沿用会把上一家的名字/标语留在页面上。
    theme.colorPrimary = profile.primary_color || DEFAULT_THEME.colorPrimary;
    theme.shopName = profile.name || DEFAULT_THEME.shopName;
    theme.slogan = profile.slogan || "";
    theme.logoUrl = profile.logo_url ? absUrl(profile.logo_url) : "";
    theme.contactPhone = profile.contact_phone || "";
    theme.contactAddress = profile.contact_address || "";
    theme.businessHours = profile.business_hours || "";
    theme.themeVars = profile.theme || {};
  }
  return theme;
}

/** 未配 logo 时的中性占位字：门店名首字（不回落到平台或别家门店的图形标）。 */
function initialOf(theme) {
  const name = theme && theme.shopName ? String(theme.shopName).trim() : "";
  return name ? name.slice(0, 1) : "店";
}

function applyTabBar(theme) {
  if (!theme || !theme.colorPrimary) return;
  try {
    wx.setTabBarStyle({ color: "#86909C", selectedColor: theme.colorPrimary });
  } catch (e) { /* 非 tabBar 页或低版本忽略 */ }
}

/** 导航栏标题跟随门店名：否则顾客在店里扫码打开的页头顶着平台名，像进了别人的小程序。 */
function applyNavTitle(theme) {
  if (!theme || !theme.shopName) return;
  try { wx.setNavigationBarTitle({ title: theme.shopName }); } catch (e) { /* 忽略 */ }
}

/* ---------- 色阶派生：由门店主色算出整套 Token ---------- */

function hexToRgb(hex) {
  let h = String(hex || "").trim().replace(/^#/, "");
  if (h.length === 3) h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
  if (!/^[0-9a-fA-F]{6}$/.test(h)) return null;
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)];
}

function rgbToHex(rgb) {
  return "#" + rgb.map((v) => Math.max(0, Math.min(255, Math.round(v))).toString(16).padStart(2, "0")).join("");
}

// 向目标色（255=白 / 0=黑）混合，t 为混合强度
function mix(hex, target, t) {
  const rgb = hexToRgb(hex);
  if (!rgb) return hex;
  return rgbToHex(rgb.map((v) => v + (target - v) * t));
}

// 与 04-品牌设计/色值表 的既有色阶对齐：#5B8C85 → press#4A756E / deep#3D5C57 / light#EEF4F3 / pale#F5F9F8
const SHADES = [
  ["--c-primary", (c) => c],
  ["--c-primary-press", (c) => mix(c, 0, 0.175)],
  ["--c-primary-deep", (c) => mix(c, 0, 0.34)],
  ["--c-primary-light", (c) => mix(c, 255, 0.9)],
  ["--c-primary-pale", (c) => mix(c, 255, 0.94)],
];

/**
 * 生成页面根节点用的内联 style 字符串。
 * 页面 WXML 写 <view class="page" style="{{brandStyle}}">，整套主色系随之切换。
 */
function brandStyle(theme) {
  const candidate = theme && theme.colorPrimary;
  // 非法色值（脏数据 / 手改本地缓存）回退默认主色，避免整站样式失效
  const base = hexToRgb(candidate) ? candidate : DEFAULT_THEME.colorPrimary;
  return SHADES.map(([name, fn]) => name + ":" + fn(base)).join(";") + ";";
}

/* ---------- 页面接入：一行包装，onLoad/onShow 自动注入 ---------- */

/**
 * 页面包装器：Page(brandPage({ ...原配置 })) 即接入运行时换肤。
 * - 注入 data.brandStyle / data.shopInitial（先用已知品牌渲染，避免首帧闪色）
 * - onLoad / onShow 时 ensureBrand() 后刷新 brandStyle / theme / shopInitial
 */
function brandPage(options) {
  const opts = options || {};
  const known = currentTheme();
  // 预置首帧色：优先用已缓存的品牌（app 启动时已拉过），避免异色门店首帧闪默认绿
  opts.data = Object.assign(
    { brandStyle: brandStyle(known), shopInitial: initialOf(known) },
    opts.data || {},
  );

  const bootstrap = function () {
    const cached = currentTheme();
    this.setData({ brandStyle: brandStyle(cached), theme: cached, shopInitial: initialOf(cached) });
    applyNavTitle(cached);
    ensureBrand()
      .then((theme) => this.setData({
        brandStyle: brandStyle(theme), theme, shopInitial: initialOf(theme),
      }))
      .catch(() => {});
  };
  opts._applyBrand = bootstrap;

  const origOnLoad = opts.onLoad;
  const origOnShow = opts.onShow;
  if (typeof origOnLoad === "function") {
    opts.onLoad = function () {
      bootstrap.call(this);
      return origOnLoad.apply(this, arguments);
    };
  }
  if (typeof origOnShow === "function") {
    opts.onShow = function () {
      bootstrap.call(this);
      return origOnShow.apply(this, arguments);
    };
  }
  if (!opts.onLoad && !opts.onShow) {
    opts.onShow = function () { bootstrap.call(this); };
  }
  return opts;
}

function getApp_() {
  try { return typeof getApp === "function" ? getApp() : null; } catch (e) { return null; }
}

/** 当前已知品牌（无需发请求）：内存缓存 → globalData → 默认品牌。 */
function currentTheme() {
  if (_cached) return _cached;
  const app = getApp_();
  return (app && app.globalData && app.globalData.theme) || DEFAULT_THEME;
}

/** 确保品牌已加载（带缓存与并发去重）；页面 onLoad 调用后 setData 渲染。 */
function ensureBrand() {
  if (_cached) return Promise.resolve(_cached);
  if (_promise) return _promise;
  const app = getApp_();
  const base = (app && app.globalData && app.globalData.theme) || DEFAULT_THEME;
  _promise = getStoreProfile(currentSlug())
    .then((profile) => {
      const theme = mergeTheme(base, profile);
      _cached = theme;
      if (app && app.globalData) app.globalData.theme = theme;
      applyTabBar(theme);
      applyNavTitle(theme);
      return theme;
    })
    .catch(() => {
      _cached = Object.assign({}, base);
      return _cached;
    });
  return _promise;
}

/** 退出/切换门店时清除缓存，下次重新拉取。 */
function resetBrand() {
  _cached = null;
  _promise = null;
}

module.exports = {
  ensureBrand,
  saveSlug,
  currentSlug,
  defaultStoreSlug,
  slugFromOptions,
  resetBrand,
  brandStyle,
  brandPage,
  initialOf,
};
