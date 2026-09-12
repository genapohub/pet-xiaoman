/**
 * 平台超管门店管理 · 浏览器 E2E（真实 Chrome，打本地 5173 后台）
 *
 * 覆盖：登录页中性化 → 超管只看到「门店管理」 → 开店（含取色器）→ 品牌配置与预览
 *      → 改色保存后 C 端同步 → 门店账号 → 租户视角隔离（看不到也进不去 /stores）
 *
 * 前置：
 *   1. API 跑在 8010，且已建超管：`scripts/create_super_admin.py`（superadmin / super123456）
 *   2. 后台 dev server 跑在 5173（`npm run dev`）
 *   3. 依赖托管 workspace 的 playwright + 本机 Chrome（免下载 chromium）
 *
 * 用法：
 *   NODE_PATH=<workbuddy node workspace>/node_modules node scripts/e2e_superadmin.cjs
 *
 * 副作用：会建一家 slug=`demo-meow` 的演示门店；截图写到 /tmp/sa_shots。
 *        清理演示店：`pet_xiaoman_api` 里跑 `scripts/purge_demo_stores.py --apply`。
 */
const path = require("path");
const fs = require("fs");
const { chromium } = require("playwright");

const ADMIN = "http://localhost:5173";
const API = "http://127.0.0.1:8010";
const SHOTS = "/tmp/sa_shots";
const DEMO_SLUG = "demo-meow";

let fails = 0;
const notes = [];
function check(label, cond, detail) {
  if (!cond) fails += 1;
  const line = `${cond ? "OK  " : "FAIL"} ${label}`;
  console.log(line + (cond || detail === undefined ? "" : `\n      ${detail}`));
}
async function shot(page, name) {
  await page.screenshot({ path: path.join(SHOTS, `${name}.png`), fullPage: true });
  notes.push(name);
}

/**
 * 在 Element Plus 取色面板里填 hex 并确认。
 * 选择器按实测 DOM 写死：hex 输入在 .el-color-picker-panel__footer 里，
 * 确认按钮是 .el-color-footer__btn（不是 .el-color-dropdown__btns）。
 */
async function pickColor(page, hex) {
  await page.waitForSelector(".el-color-picker-panel", { state: "visible" });
  await page.waitForTimeout(300);
  const input = page.locator(".el-color-picker-panel__footer input").first();
  await input.click();
  await input.fill(hex);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(200);
  const confirm = page.locator(".el-color-footer__btn").first();
  if (await confirm.isVisible().catch(() => false)) await confirm.click();
  await page.waitForTimeout(300);
}

(async () => {
  fs.mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch({ channel: "chrome" });
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  const consoleErrors = [];
  page.on("console", (m) => { if (m.type() === "error") consoleErrors.push(m.text()); });
  const httpErrors = [];
  page.on("response", (r) => { if (r.status() >= 400) httpErrors.push(`${r.status()} ${r.url()}`); });

  /* ---------- 1) 登录页：不能出现别家门店的品牌 ---------- */
  await page.goto(`${ADMIN}/login`, { waitUntil: "networkidle" });
  const loginHtml = await page.content();
  check("登录页不再出现「宠小满」", !loginHtml.includes("宠小满"));
  check("浏览器标签页标题中性", (await page.title()).trim() === "门店管理后台", await page.title());
  check("登录页不再加载别家 logo 资源", !loginHtml.includes("logo-lockup"));
  check("登录页标题中性", await page.locator(".brand__title").innerText() === "门店管理后台");
  check("登录页有中性爪印占位标", await page.locator(".brand__mark svg").count() === 1);
  check("登录页标语不再硬编码", !loginHtml.includes("爱意小满"));
  await shot(page, "01-login");

  /* ---------- 2) 超管登录 → 只应看到「门店管理」 ---------- */
  await page.fill('input[placeholder="账号"]', "superadmin");
  await page.fill('input[placeholder="密码"]', "super123456");
  await page.click("button.login-btn");
  await page.waitForURL(/\/stores/, { timeout: 15000 });
  await page.waitForTimeout(800);
  check("超管登录后落到 /stores", page.url().includes("/stores"), page.url());

  const menuTexts = await page.locator(".el-menu-item").allInnerTexts();
  check("侧栏只有「门店管理」一项", menuTexts.length === 1 && menuTexts[0].trim() === "门店管理",
    JSON.stringify(menuTexts));
  check("侧栏店名 = 平台管理台",
    (await page.locator(".brand__name").innerText()).trim() === "平台管理台");
  check("侧栏副标题 = 多门店统一管理",
    (await page.locator(".brand__sub").innerText()).trim() === "多门店统一管理");
  check("页头小标签为平台语境",
    (await page.locator(".px-header__eyebrow").innerText()).trim() === "PLATFORM ADMIN");
  check("顶栏不再有「门店品牌」按钮", (await page.locator('button:has-text("门店品牌")').count()) === 0);
  const rowsBefore = await page.locator(".el-table__body tbody tr").count();
  check("门店列表有数据", rowsBefore >= 1, `行数=${rowsBefore}`);
  await shot(page, "02-superadmin-store-list");

  /* ---------- 3) 开通门店（走 UI 真建一家） ---------- */
  // 用平台接口探测（不要用 C 端 profile 探测：门店不存在时那个 404 会被浏览器记为控制台报错）
  const exists = await page.evaluate(async (slug) => {
    const token = localStorage.getItem("token") || "";
    const r = await fetch("/api/b/platform/stores", { headers: { Authorization: `Bearer ${token}` } });
    if (r.status !== 200) return null;
    const rows = await r.json();
    const hit = rows.find((x) => x.profile && x.profile.slug === slug);
    return hit ? hit.store_id : null;
  }, DEMO_SLUG);

  if (exists) {
    console.log(`（演示店 ${DEMO_SLUG} 已存在 id=${exists}，跳过创建，直接进详情）`);
    await page.goto(`${ADMIN}/stores/${exists}`, { waitUntil: "networkidle" });
    await page.waitForTimeout(900);
  } else {
    await page.click('button:has-text("开通门店")');
    await page.waitForSelector(".el-drawer", { state: "visible" });
    await page.waitForTimeout(400);
    await page.fill('input[placeholder^="内部使用"]', "喵星人善终（演示）");
    await page.fill('input[placeholder^="英文/数字"]', DEMO_SLUG);
    await page.fill('input[placeholder^="C 端显示"]', "喵星人宠物善终");
    await page.fill('input[placeholder^="如：给 ta"]', "给 ta 最后的体面");
    await page.fill('input[placeholder^="如：王店长"]', "喵店长");
    await page.fill('input[placeholder^="全平台唯一"]', "demo_meow_boss");
    await page.fill('input[placeholder^="至少 6 位"]', "meow123456");

    // 主色：点开取色面板 → 填 hex → 确认
    await page.click(".el-drawer .el-color-picker");
    await pickColor(page, "#C97B63");
    const picked = await page.locator(".el-drawer .swatch-text").innerText();
    check("取色器写入门店主色", picked.trim().toLowerCase() === "#c97b63", picked);
    await shot(page, "03-create-store-drawer");

    await page.click('.el-drawer button:has-text("开通并去配置")');
    await page.waitForURL(/\/stores\/\d+/, { timeout: 15000 });
    await page.waitForTimeout(900);
    check("开店后跳到该店详情页", /\/stores\/\d+/.test(page.url()), page.url());
  }

  /* ---------- 4) 详情页：品牌表单 + 预览 ---------- */
  const storeUrl = page.url();
  check("详情页标题是该店门店名",
    (await page.locator(".px-header__title").innerText()).includes("喵星人"),
    await page.locator(".px-header__title").innerText());
  check("页头小标签仍为平台语境",
    (await page.locator(".px-header__eyebrow").innerText()).trim() === "PLATFORM ADMIN");

  const brandName = await page.locator('input[placeholder^="门店名称（50 字内）"]').inputValue();
  check("品牌表单已回填店名", brandName.includes("喵星人"), brandName);
  const slogan = await page.locator('input[placeholder^="如：给ta"]').inputValue();
  check("品牌表单已回填标语", slogan.length > 0, slogan);
  const chip = await page.locator(".preview__chip").getAttribute("style");
  // 浏览器会把 #C97B63 归一成 rgb(201, 123, 99)，两种形式都认
  const chipLower = (chip || "").toLowerCase();
  check("预览色块用的是「这家店」的色，不是后台主色",
    chipLower.includes("c97b63") || chipLower.includes("rgb(201, 123, 99)"), chip);
  check("预览显示店名首字占位（未配 logo）",
    (await page.locator(".preview__mark").innerText()).trim() === "喵");
  await shot(page, "04-store-detail-brand");

  /* ---------- 5) 改主色 → 保存 → 立刻生效 ---------- */
  await page.click(".brand-form .el-color-picker");
  await pickColor(page, "#4F7BD9");
  await page.click('button:has-text("保存品牌")');
  await page.waitForTimeout(1200);
  const savedTip = await page.locator(".saved").innerText().catch(() => "");
  check("保存后有回执", savedTip.includes("已保存"), savedTip);

  const cEnd = await page.evaluate(async (slug) => {
    const r = await fetch(`/api/c/store/profile?slug=${slug}`);
    return r.status === 200 ? r.json() : null;
  }, DEMO_SLUG);
  check("C 端已同步为新主色", cEnd && (cEnd.primary_color || "").toUpperCase() === "#4F7BD9",
    JSON.stringify(cEnd && cEnd.primary_color));
  check("C 端标语来自门店配置（非硬编码）",
    cEnd && cEnd.slogan === "给 ta 最后的体面", JSON.stringify(cEnd && cEnd.slogan));
  await shot(page, "05-brand-saved");

  /* ---------- 6) 门店账号 tab ---------- */
  await page.click('.el-tabs__item:has-text("门店账号")');
  await page.waitForTimeout(700);
  const staffRows = await page.locator(".el-table__body tbody tr").count();
  check("门店账号列表有首位店长", staffRows >= 1, `行数=${staffRows}`);
  const roleTags = await page.locator(".el-table__body .el-tag").allInnerTexts();
  check("账号列表标出了角色", roleTags.join(",").includes("店长"), JSON.stringify(roleTags));
  check("提供「改密」入口", (await page.locator('button:has-text("改密")').count()) >= 1);
  await shot(page, "06-store-staff");

  /* ---------- 7) 租户视角：看不到门店管理，品牌按钮消失 ---------- */
  await ctx.clearCookies();
  await page.evaluate(() => localStorage.clear());
  await page.goto(`${ADMIN}/login`, { waitUntil: "networkidle" });
  await page.fill('input[placeholder="账号"]', "admin");
  await page.fill('input[placeholder="密码"]', "admin123");
  await page.click("button.login-btn");
  await page.waitForURL(/dashboard/, { timeout: 15000 });
  await page.waitForTimeout(900);

  const tenantMenus = await page.locator(".el-menu-item").allInnerTexts();
  check("租户侧栏没有「门店管理」", !tenantMenus.some((t) => t.includes("门店管理")),
    JSON.stringify(tenantMenus));
  check("租户侧栏店名 = 自己门店", (await page.locator(".brand__name").innerText()).trim().length > 0,
    await page.locator(".brand__name").innerText());
  check("租户侧栏不显示平台副标题",
    (await page.locator(".brand__sub").innerText()).trim() !== "多门店统一管理");
  check("租户页头小标签为门店语境",
    (await page.locator(".px-header__eyebrow").innerText()).trim() === "STORE ADMIN");
  check("租户顶栏没有「门店品牌」按钮",
    (await page.locator('button:has-text("门店品牌")').count()) === 0);
  await shot(page, "07-tenant-dashboard");

  // 直闯 /stores 应被守卫弹回
  await page.goto(`${ADMIN}/stores`, { waitUntil: "networkidle" });
  await page.waitForTimeout(900);
  check("店长直闯 /stores 被弹回自己的菜单", !page.url().includes("/stores"), page.url());
  await shot(page, "08-tenant-blocked-from-stores");

  /* ---------- 8) 控制台 / 网络错误 ---------- */
  const realErrors = consoleErrors.filter((t) => !/favicon|ResizeObserver/i.test(t));
  check("无控制台报错", realErrors.length === 0, realErrors.slice(0, 3).join(" | "));
  // 只有「故意的失败」才算预期：停用门店/品牌写入被拒这类探针请求
  const unexpected = httpErrors.filter(
    (t) => !/(401|403|404).*(platform\/stores\/\d+\/status|\/api\/c\/store\/profile)/.test(t));
  check("无非预期 4xx/5xx 资源请求", unexpected.length === 0, unexpected.slice(0, 5).join(" | "));

  await browser.close();
  console.log(`\n截图目录：${SHOTS}\n${fails === 0 ? "全部通过 ✓" : `${fails} 项失败`}`);
  process.exit(fails === 0 ? 0 : 1);
})().catch((e) => { console.error("E2E crashed:", e); process.exit(2); });
