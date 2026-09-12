/**
 * 小程序图标资产生成器
 *
 * 设计约束（对齐品牌手册 v1.0 + 图标风格决策「线性描边」）：
 * - 24×24 网格，fill:none，stroke 线性描边，round cap/join
 * - 线宽：tabBar 1.75（等价 81px 下约 5.9px 视觉）、页面内 1.75
 * - 颜色：暖灰 #86909C（默认）/ 暖松绿 #5B8C85（选中·强调）/ 纸感白 #FAF9F6（深底反白）
 *
 * 为什么是 PNG：小程序 tabBar 只接受本地 PNG；页面内用 image 组件加载 PNG
 * 体积和一致性都可控（iconfont 需要额外字体文件，且小程序不支持本地字体）。
 *
 * 用法：
 *   NODE_PATH=<brandkit>/assets/logo/node_modules node scripts/gen-icons.js
 */
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const OUT_DIR = path.join(__dirname, "..", "assets", "icons");

const COLORS = {
  gray: "#86909C",
  primary: "#5B8C85",
  white: "#FAF9F6",
  clay: "#D9A468",
};

// 线性图标路径（24×24，stroke 由外层控制）
const PATHS = {
  // ===== tabBar 5 个 =====
  home:
    '<path d="M3.4 10.6 12 3.8l8.6 6.8"/><path d="M5.6 9.2V19a1.6 1.6 0 0 0 1.6 1.6h9.6A1.6 1.6 0 0 0 18.4 19V9.2"/><path d="M9.8 20.6v-5.2h4.4v5.2"/>',
  booking:
    '<rect x="3.6" y="5.4" width="16.8" height="15" rx="2.6"/><path d="M8.2 3.6v3.4M15.8 3.6v3.4M3.6 10.2h16.8"/><path d="M12 13.4v4M10 15.4h4"/>',
  order:
    '<rect x="4.8" y="3.6" width="14.4" height="16.8" rx="2.4"/><path d="M8.8 8.6h6.4M8.8 12h6.4M8.8 15.4h4"/>',
  gift:
    '<rect x="3.8" y="8.8" width="16.4" height="4" rx="1.2"/><path d="M5.4 12.8v6.6a1.4 1.4 0 0 0 1.4 1.4h10.4a1.4 1.4 0 0 0 1.4-1.4v-6.6"/><path d="M12 8.8v12"/><path d="M12 8.8c-1.4-3-2.6-5-4.3-5a2.3 2.3 0 0 0 0 4.6h8.6a2.3 2.3 0 0 0 0-4.6c-1.7 0-2.9 2-4.3 5Z"/>',
  user:
    '<circle cx="12" cy="8.4" r="4"/><path d="M4.8 20.4c0-3.6 3.2-6.2 7.2-6.2s7.2 2.6 7.2 6.2"/>',

  // ===== 页面内通用 =====
  chevron:
    '<path d="M9.6 5.8 15.8 12l-6.2 6.2"/>',
  back:
    '<path d="M14.8 5.2 8 12l6.8 6.8"/>',
  phone:
    '<path d="M5.4 3.8h2.8l1.7 4.2-2.1 1.7a13.2 13.2 0 0 0 6.2 6.2l1.7-2.1 4.2 1.7v2.8a1.9 1.9 0 0 1-2.1 1.9C11.1 20.1 4.2 13.2 3.5 6.2a1.9 1.9 0 0 1 1.9-2.4Z"/>',
  clock:
    '<circle cx="12" cy="12" r="8.4"/><path d="M12 7.2V12l3.2 2"/>',
  location:
    '<path d="M12 21.2s6.6-5.7 6.6-10.5a6.6 6.6 0 1 0-13.2 0C5.4 15.5 12 21.2 12 21.2Z"/><circle cx="12" cy="10.5" r="2.5"/>',
  check:
    '<circle cx="12" cy="12" r="8.4"/><path d="M8.4 12.2l2.6 2.6 4.6-5"/>',
  camera:
    '<path d="M4.6 8.6h2.6L8.6 6.4h6.8l1.4 2.2h2.6a1.6 1.6 0 0 1 1.6 1.6v7.6a1.6 1.6 0 0 1-1.6 1.6H4.6A1.6 1.6 0 0 1 3 17.8v-7.6a1.6 1.6 0 0 1 1.6-1.6Z"/><circle cx="12" cy="14" r="3.1"/>',
  paw:
    '<ellipse cx="12" cy="15.6" rx="3.7" ry="3" transform="rotate(-4 12 15.6)"/><ellipse cx="7.4" cy="10.4" rx="1.8" ry="2.3" transform="rotate(-16 7.4 10.4)"/><ellipse cx="12" cy="9.2" rx="1.9" ry="2.4" transform="rotate(-3 12 9.2)"/><ellipse cx="16.6" cy="10.4" rx="1.8" ry="2.3" transform="rotate(16 16.6 10.4)"/>',
  plus:
    '<path d="M12 6.6v10.8M6.6 12h10.8"/>',
  shield:
    '<path d="M12 3.4 5.4 6v5.9c0 4.1 2.8 7.4 6.6 8.5 3.8-1.1 6.6-4.4 6.6-8.5V6Z"/><path d="M9.1 12.1l2.2 2.2 4-4.4"/>',
  heart:
    '<path d="M12 20.2S4.6 15.6 4.6 10.5a4.1 4.1 0 0 1 7.4-2.4 4.1 4.1 0 0 1 7.4 2.4c0 5.1-7.4 9.7-7.4 9.7Z"/>',
  refresh:
    '<path d="M19.4 12a7.4 7.4 0 1 1-2.2-5.2"/><path d="M19.6 4.6v4.2h-4.2"/>',
  edit:
    '<path d="M15.6 4.6l3.8 3.8-9.8 9.8-4.4.6.6-4.4 9.8-9.8Z"/><path d="M13.8 6.4l3.8 3.8"/>',
  price:
    '<path d="M11.4 3.6H19a1.4 1.4 0 0 1 1.4 1.4v7.6a1.4 1.4 0 0 1-.4 1l-7.4 7.4a1.4 1.4 0 0 1-2 0l-7.2-7.2a1.4 1.4 0 0 1 0-2l7.4-7.4a1.4 1.4 0 0 1 1-.4Z"/><circle cx="15.9" cy="8.1" r="1.4"/>',
  box:
    '<path d="M3.8 7.6 12 3.6l8.2 4v8.8L12 20.4l-8.2-4Z"/><path d="M3.8 7.6 12 11.6l8.2-4M12 11.6v8.8"/>',
  info:
    '<circle cx="12" cy="12" r="8.4"/><path d="M12 11.2v5M12 7.9v.2"/>',
};

function svgOf(paths, color, strokeWidth = 1.75) {
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="${color}" stroke-width="${strokeWidth}" stroke-linecap="round" stroke-linejoin="round">${paths}</svg>`;
}

function render(svg, size, filename) {
  const resvg = new Resvg(svg, {
    fitTo: { mode: "width", value: size },
    background: "rgba(0,0,0,0)",
  });
  fs.writeFileSync(path.join(OUT_DIR, filename), resvg.render().asPng());
}

function main() {
  fs.mkdirSync(OUT_DIR, { recursive: true });
  let n = 0;

  // tabBar：5 个 tab × 2 态（未选暖灰 / 选中暖松绿），81×81（微信推荐）
  const TAB_ICONS = ["home", "booking", "order", "gift", "user"];
  for (const name of TAB_ICONS) {
    render(svgOf(PATHS[name], COLORS.gray), 81, `tab-${name}.png`);
    render(svgOf(PATHS[name], COLORS.primary), 81, `tab-${name}-active.png`);
    n += 2;
  }

  // 页面内图标：暖灰（默认）/ 暖松绿（强调）/ 纸感白（深底反白），48×48（@2x）
  for (const [name, paths] of Object.entries(PATHS)) {
    if (TAB_ICONS.includes(name)) continue;
    render(svgOf(paths, COLORS.gray), 48, `${name}.png`);
    render(svgOf(paths, COLORS.primary), 48, `${name}-primary.png`);
    render(svgOf(paths, COLORS.white), 48, `${name}-white.png`);
    n += 3;
  }

  console.log(`已生成 ${n} 个图标 → ${OUT_DIR}`);
}

main();
