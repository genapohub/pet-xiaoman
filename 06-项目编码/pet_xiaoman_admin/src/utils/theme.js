// 门店白标：按门店主色在运行时重算品牌变量（多租户「按店换肤」）。
// 覆盖 index 层 CSS 变量即可让全部页面 + Element Plus 组件跟随换色，无需改组件。

export const DEFAULT_PRIMARY = "#5B8C85";

const BRAND_VARS = [
  "--px-primary",
  "--px-primary-hover",
  "--px-primary-pressed",
  "--px-primary-disabled",
  "--px-primary-weak",
  "--px-primary-softer",
  "--el-color-primary",
  "--el-color-primary-light-3",
  "--el-color-primary-light-5",
  "--el-color-primary-light-7",
  "--el-color-primary-light-8",
  "--el-color-primary-light-9",
  "--el-color-primary-dark-2",
];

function hexToRgb(hex) {
  const h = hex.replace("#", "");
  const full = h.length === 3 ? h.split("").map((c) => c + c).join("") : h;
  return [parseInt(full.slice(0, 2), 16), parseInt(full.slice(2, 4), 16), parseInt(full.slice(4, 6), 16)];
}

function toHex([r, g, b]) {
  const c = (n) => Math.max(0, Math.min(255, Math.round(n))).toString(16).padStart(2, "0");
  return `#${c(r)}${c(g)}${c(b)}`;
}

/** 把 hex 颜色向 target（#ffffff / #000000）按 ratio 混合。 */
export function mix(hex, target, ratio) {
  const a = hexToRgb(hex);
  const b = hexToRgb(target);
  return toHex(a.map((v, i) => v + (b[i] - v) * ratio));
}

export function isValidHex(hex) {
  return typeof hex === "string" && /^#([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$/.test(hex.trim());
}

/** 应用门店主色（非法值回退默认色）。 */
export function applyBrandColor(hex) {
  const color = isValidHex(hex) ? hex.trim() : DEFAULT_PRIMARY;
  const root = document.documentElement;
  const set = (k, v) => root.style.setProperty(k, v);
  set("--px-primary", color);
  set("--px-primary-hover", mix(color, "#ffffff", 0.15));
  set("--px-primary-pressed", mix(color, "#000000", 0.12));
  // 禁用态：对齐 tokens.css 默认值 #C2D6D1（≈ 主色向白 0.63）
  set("--px-primary-disabled", mix(color, "#ffffff", 0.63));
  set("--px-primary-weak", mix(color, "#ffffff", 0.88));
  set("--px-primary-softer", mix(color, "#ffffff", 0.94));
  set("--el-color-primary", color);
  set("--el-color-primary-light-3", mix(color, "#ffffff", 0.30));
  set("--el-color-primary-light-5", mix(color, "#ffffff", 0.50));
  set("--el-color-primary-light-7", mix(color, "#ffffff", 0.70));
  set("--el-color-primary-light-8", mix(color, "#ffffff", 0.80));
  set("--el-color-primary-light-9", mix(color, "#ffffff", 0.90));
  set("--el-color-primary-dark-2", mix(color, "#000000", 0.12));
}

/** 还原默认品牌色（退出登录时调用）。 */
export function resetBrandColor() {
  const root = document.documentElement;
  BRAND_VARS.forEach((k) => root.style.removeProperty(k));
}
