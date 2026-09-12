/**
 * 小程序白标运行时校验（Node 桩环境，不需要微信开发者工具）
 *
 * 为什么需要它：小程序没法在 CI 里跑，而换肤逻辑（色阶派生 / 切店不串品牌 / 12 页是否都接上）
 * 全靠肉眼在开发者工具里点，很容易漏。这里用 stub 的 wx/getApp/Page 把页面模块真加载一遍。
 *
 * 校验点：
 *  1) initialOf：未配 logo 时的占位字取店名首字，不回落固定门店名
 *  2) brandStyle：由门店主色派生整套 --c-primary* 色阶
 *  3) 扫码/链接参数解析 + 切店缓存失效：扫 B 店后不能继续展示 A 店
 *  4) brandPage：预置 shopInitial + brandStyle，onLoad/onShow 生命周期仍被调用
 *  5) 12 个页面模块全部可加载且已接入换肤
 *  6) 源码中不再有「宠小满 / 爱意小满 / logo-mark」硬编码
 *
 * 用法：
 *   NODE_PATH=<workbuddy node workspace>/node_modules node scripts/verify-brand.js
 */
const path = require("path");
const Module = require("module");

// 以本文件为基准定位小程序根目录，别写死绝对路径
const ROOT = path.resolve(__dirname, "..");

/* ---------- wx / App / Page 桩 ---------- */
const storage = {};
let navTitle = null;
let tabBarColor = null;

global.wx = {
  setStorageSync: (k, v) => { storage[k] = v; },
  getStorageSync: (k) => (k in storage ? storage[k] : ""),
  removeStorageSync: (k) => { delete storage[k]; },
  setTabBarStyle: (o) => { tabBarColor = o.selectedColor; },
  setNavigationBarTitle: (o) => { navTitle = o.title; },
  showToast: () => {},
  showLoading: () => {},
  hideLoading: () => {},
  getAccountInfoSync: () => ({ miniProgram: { envVersion: "develop" } }),
  getDeviceInfo: () => ({ platform: "devtools" }),
  getSystemInfoSync: () => ({ platform: "devtools" }),
};

const appStub = { globalData: {} };
global.getApp = () => appStub;
global.getCurrentPages = () => [];

let currentPagePath = null;
const loadedPages = {};
global.Page = (o) => { loadedPages[currentPagePath] = o; };
global.Component = () => {};

/* ---------- 注入假的 C 端门店资料接口 ---------- */
let profileResponse = null;
let lastProfileSlug = null;
function fakeModule(absPath, exports) {
  const m = new Module(absPath);
  m.filename = absPath;
  m.exports = exports;
  m.loaded = true;
  require.cache[absPath] = m;
}
fakeModule(path.join(ROOT, "utils/request.js"), {
  getStoreProfile: (slug) => {
    lastProfileSlug = slug || "";
    return Promise.resolve(profileResponse);
  },
  absUrl: (u) => u,
});
fakeModule(path.join(ROOT, "utils/url.js"), { absUrl: (u) => u });

/* ---------- 断言工具 ---------- */
let failures = 0;
function check(label, actual, expected) {
  const ok = JSON.stringify(actual) === JSON.stringify(expected);
  if (!ok) failures += 1;
  console.log(`${ok ? "OK  " : "FAIL"} ${label}` + (ok ? "" : `\n      实际=${JSON.stringify(actual)}\n      期望=${JSON.stringify(expected)}`));
}
function checkTrue(label, cond, detail) {
  if (!cond) failures += 1;
  console.log(`${cond ? "OK  " : "FAIL"} ${label}` + (cond ? "" : `\n      ${detail || ""}`));
}

const brand = require(path.join(ROOT, "utils/brand.js"));
const DEFAULT_THEME = require(path.join(ROOT, "config/theme.js"));

/* ---------- 1) 中性占位字 ---------- */
console.log("\n== 1) 未配 logo 的占位字 ==");
check("门店名首字", brand.initialOf({ shopName: "喵星人宠物善终" }), "喵");
check("英文店名单字", brand.initialOf({ shopName: "PET HOME" }), "P");
check("空门店名兜底为中性的「店」", brand.initialOf({}), "店");
check("undefined 也不炸", brand.initialOf(undefined), "店");
checkTrue("平台默认店名不是某家门店的名字", DEFAULT_THEME.shopName !== "宠小满", `实际=${DEFAULT_THEME.shopName}`);
check("平台默认标语为空（不硬编码）", DEFAULT_THEME.slogan, "");

/* ---------- 2) 色阶派生 ---------- */
console.log("\n== 2) 主色 → 整套色阶 ==");
const style = brand.brandStyle({ colorPrimary: "#5B8C85" });
const want = {
  "--c-primary": "#5b8c85",
  "--c-primary-press": "#4b746e",
  "--c-primary-deep": "#3c5c58",
  "--c-primary-light": "#eff4f3",
  "--c-primary-pale": "#f5f8f8",
};
Object.entries(want).forEach(([k, v]) => {
  const m = style.match(new RegExp(`${k}:([^;]+);`));
  const got = (m ? m[1] : "").toLowerCase();
  checkTrue(`${k} 派生正确`, got === v, `实际=${got} 期望=${v}`);
});
const dirty = brand.brandStyle({ colorPrimary: "红色" }).toLowerCase();
checkTrue("脏色值回退平台默认主色",
  dirty.includes(`--c-primary:${DEFAULT_THEME.colorPrimary.toLowerCase()};`), dirty);

/* ---------- 3) 扫码/链接参数 + 切店不串品牌 ---------- */
console.log("\n== 3) 扫码/链接参数与切换门店 ==");
async function run() {
  check("query.slug 解析", brand.slugFromOptions({ query: { slug: " store-a " } }), "store-a");
  check("scene=slug%3Dstore-b 解析", brand.slugFromOptions({ scene: "slug%3Dstore-b" }), "store-b");
  check("scene 直接传 slug 解析", brand.slugFromOptions({ scene: "store-c" }), "store-c");

  brand.saveSlug("store-a");
  profileResponse = { name: "门店A", slogan: "A 的标语", primary_color: "#5B8C85", logo_url: "" };
  let theme = await brand.ensureBrand();
  check("门店A 请求带 slug", lastProfileSlug, "store-a");
  check("门店A 店名", theme.shopName, "门店A");
  check("门店A 标语", theme.slogan, "A 的标语");
  checkTrue("tabBar 选中色跟随门店主色", tabBarColor === "#5B8C85", String(tabBarColor));
  check("导航栏标题跟随门店名", navTitle, "门店A");

  // 切到门店 B：saveSlug 会让品牌缓存失效；B 没有 slogan、也没有 name → 不能沿用 A
  brand.saveSlug("store-b");
  profileResponse = { name: null, slogan: null, primary_color: "#C97B63", logo_url: "" };
  theme = await brand.ensureBrand();
  check("门店B 请求带 slug", lastProfileSlug, "store-b");
  check("门店B 无店名 → 回落平台中性店名", theme.shopName, DEFAULT_THEME.shopName);
  check("门店B 无标语 → 清空，不留 A 的标语", theme.slogan, "");
  checkTrue("门店B 主色已切换", theme.colorPrimary === "#C97B63", theme.colorPrimary);
  check("导航栏标题跟着换", navTitle, DEFAULT_THEME.shopName);
  checkTrue("门店B 的占位字来自中性店名", brand.initialOf(theme) === DEFAULT_THEME.shopName.slice(0, 1), brand.initialOf(theme));

  // 门店 B 配了自有 logo → 用图，不用占位
  brand.resetBrand();
  profileResponse = { name: "喵星人", slogan: "给ta最后的体面", primary_color: "#C97B63", logo_url: "/uploads/meow.png" };
  theme = await brand.ensureBrand();
  checkTrue("有 logo 时用绝对地址", theme.logoUrl === "/uploads/meow.png", theme.logoUrl);
  check("有标语时展示门店标语", theme.slogan, "给ta最后的体面");

  /* ---------- 4) brandPage 包装 ---------- */
  console.log("\n== 4) brandPage 注入与生命周期 ==");
  let loadCalled = 0;
  let showCalled = 0;
  const opts = brand.brandPage({
    data: { own: 1 },
    onLoad() { loadCalled += 1; },
    onShow() { showCalled += 1; },
  });
  check("预置 brandStyle 存在", typeof opts.data.brandStyle === "string" && opts.data.brandStyle.length > 0, true);
  check("预置 shopInitial", opts.data.shopInitial, "喵");
  checkTrue("页面自有 data 保留", opts.data.own === 1, opts.data.own);

  const ctx = { data: opts.data, setData(patch) { Object.assign(this.data, patch); } };
  opts.onLoad.call(ctx);
  opts.onShow.call(ctx);
  check("原 onLoad 被调用", loadCalled, 1);
  check("原 onShow 被调用", showCalled, 1);
  check("theme 已注入页面 data", ctx.data.theme.shopName, "喵星人");
  check("shopInitial 随品牌刷新", ctx.data.shopInitial, "喵");
  checkTrue("brandStyle 已随品牌刷新", ctx.data.brandStyle.toLowerCase().includes("#c97b63"),
    ctx.data.brandStyle.slice(0, 60));

  // 无 onLoad/onShow 的页面也要能拿到品牌
  let fallbackShow = 0;
  const bare = brand.brandPage({ data: {}, onShow() { fallbackShow += 1; } });
  const ctx2 = { data: bare.data, setData(p) { Object.assign(this.data, p); } };
  bare.onShow.call(ctx2);
  check("仅有 onShow 的页面也接上换肤", ctx2.data.theme.shopName, "喵星人");
  check("onShow 仍被调用", fallbackShow, 1);

  /* ---------- 5) 12 个页面全部接入 ---------- */
  console.log("\n== 5) 页面模块加载与换肤接入 ==");
  const PAGES = [
    "pages/index/index", "pages/login/index", "pages/order-create/index",
    "pages/order-list/index", "pages/products/products", "pages/profile/index",
    "pages/prices/prices", "pages/cashier/index", "pages/order-success/index",
    "pages/order-detail/index", "pages/boarding-query/query", "pages/pets/pets",
  ];
  const notWrapped = [];
  PAGES.forEach((p) => {
    currentPagePath = p;
    try {
      require(path.join(ROOT, `${p}.js`));
    } catch (e) {
      failures += 1;
      console.log(`FAIL 加载失败 ${p}: ${e.message}`);
      return;
    }
    const page = loadedPages[p];
    if (!page) { failures += 1; console.log(`FAIL ${p} 未调用 Page()`); return; }
    if (typeof page._applyBrand !== "function") notWrapped.push(p);
  });
  check("接入换肤的页面数", PAGES.length - notWrapped.length, PAGES.length);
  checkTrue("没有漏接的页面", notWrapped.length === 0, notWrapped.join(", "));

  /* ---------- 6) 源码里不该再出现别家门店的品牌硬编码 ---------- */
  console.log("\n== 6) 硬编码品牌残留扫描 ==");
  const fs = require("fs");
  const hits = [];
  // 只扫"会呈现给用户"的代码。scripts/ 是构建与自检工具（本文件自己就写着这些字样），
  // 不参与 UI 渲染，排除掉才不会自我误报。
  const SKIP_DIRS = new Set(["node_modules", "miniprogram_npm", "scripts"]);
  const walk = (dir) => {
    for (const name of fs.readdirSync(dir)) {
      if (SKIP_DIRS.has(name) || name.startsWith(".")) continue;
      const full = path.join(dir, name);
      const st = fs.statSync(full);
      if (st.isDirectory()) { walk(full); continue; }
      if (!/\.(js|json|wxml|wxss)$/.test(name)) continue;
      const text = fs.readFileSync(full, "utf8");
      if (/宠小满|爱意小满|logo-mark|logo-lockup/.test(text)) hits.push(path.relative(ROOT, full));
    }
  };
  walk(ROOT);
  checkTrue("用户可见代码中无「宠小满 / 爱意小满 / logo-mark」硬编码", hits.length === 0, hits.join(", "));

  console.log(`\n${failures === 0 ? "全部通过" : `${failures} 项失败`}`);
  process.exit(failures === 0 ? 0 : 1);
}

run().catch((e) => { console.error("harness error:", e); process.exit(2); });
