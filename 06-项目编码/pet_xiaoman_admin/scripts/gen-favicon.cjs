/**
 * 后台 favicon 生成器（中性平台标，不含任何门店品牌）
 *
 * 为什么需要一个中性 favicon：
 *   后台是多门店共用的，标签页上挂某一家门店（或平台产品）的标，
 *   另外一家店的店长看到会以为登错了系统。所以这里用「主色底 + 反白爪印」的通用标。
 *   要换成你们自己的平台标，改下面的 SVG 重跑即可。
 *
 * 用法：
 *   NODE_PATH=<brandkit>/assets/logo/node_modules node scripts/gen-favicon.cjs
 *   或在本目录下 npm i -D @resvg/resvg-js 后直接 node scripts/gen-favicon.cjs
 */
const fs = require("fs");
const path = require("path");
const { Resvg } = require("@resvg/resvg-js");

const OUT = path.join(__dirname, "..", "public", "favicon.png");

// 24 网格的爪印，缩放到 64 画布上居中
const SVG = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="16" fill="#5B8C85"/>
  <g fill="#FFFFFF" transform="translate(13.2 13.2) scale(1.5667)">
    <ellipse cx="12" cy="16.8" rx="4.7" ry="3.7"/>
    <ellipse cx="5.9" cy="11.4" rx="2.1" ry="2.6" transform="rotate(-16 5.9 11.4)"/>
    <ellipse cx="9.9" cy="8.6" rx="2.1" ry="2.7"/>
    <ellipse cx="14.1" cy="8.6" rx="2.1" ry="2.7"/>
    <ellipse cx="18.1" cy="11.4" rx="2.1" ry="2.6" transform="rotate(16 18.1 11.4)"/>
  </g>
</svg>`;

fs.mkdirSync(path.dirname(OUT), { recursive: true });
const png = new Resvg(SVG, { fitTo: { mode: "width", value: 64 } }).render().asPng();
fs.writeFileSync(OUT, png);
console.log(`已生成中性 favicon：${OUT}（${png.length} 字节）`);
