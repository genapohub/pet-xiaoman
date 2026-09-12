/**
 * 校验 Markdown 里的 mermaid 代码块能否被 mermaid 解析
 * （语法错的图在 GitHub / IDE 里会整块不渲染，评审时才发现就晚了）
 *
 * 用法：
 *   cd <workbuddy node workspace> && env -u NODE_OPTIONS NODE_PATH="$PWD/node_modules" <node> \
 *     <api>/scripts/check-mermaid.cjs <file.md> [more.md ...]
 *
 * 依赖托管 workspace 里的 mermaid + jsdom（无需安装）。
 * 注意：必须先覆盖 Node 22 的只读 navigator getter，否则 mermaid 初始化即抛错。
 */
const fs = require("fs");
const { JSDOM } = require("jsdom");

// Node 22 的 navigator 是只读 getter，mermaid/jsdom 需要一个可写的
Object.defineProperty(globalThis, "navigator", {
  value: { userAgent: "node" },
  configurable: true,
  writable: true,
});

const dom = new JSDOM("<!DOCTYPE html><body></body>", { pretendToBeVisual: true });
global.window = dom.window;
global.document = dom.window.document;
global.DOMParser = dom.window.DOMParser;
global.SVGElement = dom.window.SVGElement;
global.Element = dom.window.Element;

const mermaid = require("mermaid").default;

mermaid.initialize({ startOnLoad: false, securityLevel: "loose" });

const files = process.argv.slice(2);
let fails = 0;
let total = 0;

(async () => {
  for (const file of files) {
    const text = fs.readFileSync(file, "utf8");
    const blocks = [...text.matchAll(/```mermaid\n([\s\S]*?)```/g)].map((m) => m[1]);
    console.log(`\n== ${file}（${blocks.length} 张图）==`);
    for (let i = 0; i < blocks.length; i += 1) {
      total += 1;
      const head = blocks[i].trim().split("\n")[0];
      try {
        await mermaid.parse(blocks[i]);
        console.log(`  OK   #${i + 1} ${head}`);
      } catch (e) {
        fails += 1;
        console.log(`  FAIL #${i + 1} ${head}\n       ${String(e.message).split("\n").slice(0, 4).join("\n       ")}`);
      }
    }
  }
  console.log(`\n共 ${total} 张，${fails} 张失败`);
  process.exit(fails === 0 ? 0 : 1);
})();
