"""小程序静态校验：
  1. 图片路径是否真实存在（404 图片不会报错，只会静默空白）
  2. WXSS 变量是否都有定义（未定义变量同样静默失效）
  3. WXML 绑定表达式是否用了编译器不支持的写法（函数调用 / 括号表达式取成员）

第 3 项是 WXML 最容易踩的坑：WXML 的绑定表达式**不是 JS**，
`{{item.time.slice(0,16)}}`、`{{(a||[]).length}}` 都会在微信开发者工具
编译期直接报 `Bad attr wx:if ... unexpected token`，导致整个包编译失败。
本地静态脚本提前拦截，比等 CLI 编译报错快得多。

用法：python3 scripts/check-assets.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
missing, bad_expr = [], []

# 1. WXML 里 src="/assets/..." 的引用
for f in ROOT.rglob("*.wxml"):
    for m in re.finditer(r'src="(/assets/[^"]+)"', f.read_text(encoding="utf-8")):
        ref = m.group(1)
        if "{{" in ref:  # 动态路径（如 {{item.icon}}-primary.png）不在静态校验范围
            continue
        if not (ROOT / ref.lstrip("/")).exists():
            missing.append(f"{f.relative_to(ROOT)} -> {ref}")

# 2. app.json tabBar 图标
app = json.loads((ROOT / "app.json").read_text(encoding="utf-8"))
for item in app.get("tabBar", {}).get("list", []):
    for key in ("iconPath", "selectedIconPath"):
        if key in item and not (ROOT / item[key]).exists():
            missing.append(f"app.json -> {item[key]}")

# 3. WXSS 变量：使用但未定义
defined = set(re.findall(r"(--[\w-]+)\s*:", (ROOT / "app.wxss").read_text(encoding="utf-8")))
used = set()
for f in ROOT.rglob("*.wxss"):
    used |= set(re.findall(r"var\((--[\w-]+)", f.read_text(encoding="utf-8")))
undef = sorted(used - defined)

# 4. WXML 绑定表达式：编译器不支持的写法
#    a) 函数调用，如 {{x.slice(0,16)}} / {{x.toFixed(2)}}
#    b) 括号表达式后取成员，如 {{(a || []).length}}
#    c) 可选链 ?. / 模板字符串 / 箭头函数
EXPR = re.compile(r"\{\{(.*?)\}\}", re.S)
BANNED = [
    (re.compile(r"\)\s*\."), "括号表达式后取成员，如 {{(a||[]).length}} → 改在 JS 里算好"),
    (re.compile(r"\.\w+\s*\("), "函数调用，如 {{t.slice(0,16)}} → 用 utils/format.js 预格式化"),
    (re.compile(r"\?\."), "可选链 ?. WXML 不支持"),
    (re.compile(r"`"), "模板字符串 WXML 不支持"),
    (re.compile(r"=>"), "箭头函数 WXML 不支持"),
]
for f in ROOT.rglob("*.wxml"):
    text = f.read_text(encoding="utf-8")
    for m in EXPR.finditer(text):
        expr = m.group(1)
        line = text[: m.start()].count("\n") + 1
        for pat, why in BANNED:
            if pat.search(expr):
                bad_expr.append(f"{f.relative_to(ROOT)}:{line}  {{{{{expr.strip()}}}}}  ← {why}")

if missing:
    print(f"资源缺失 {len(missing)} 处：")
    for m in missing:
        print("  MISSING:", m)
else:
    print("资源引用全部存在 OK")

if undef:
    print(f"未定义变量 {len(undef)} 个：")
    for u in undef:
        print("  UNDEF:", u)
else:
    print("Token 变量全部有定义 OK")

if bad_expr:
    print(f"WXML 表达式含不支持的写法 {len(bad_expr)} 处（会导致编译失败）：")
    for b in bad_expr:
        print("  BADEXPR:", b)
else:
    print("WXML 绑定表达式全部合法 OK")

# 5. 跳转检查：wx.navigateTo 不能打开 tabBar 页面（静默失败 → 用户侧「点了没反应」）
tab_pages = {i["pagePath"] for i in app.get("tabBar", {}).get("list", [])}
tab_paths = {"/" + p for p in tab_pages}
bad_nav = []
for f in ROOT.rglob("pages/**/*.js"):
    text = f.read_text(encoding="utf-8")
    for m in re.finditer(r"wx\.navigateTo\s*\(\s*\{\s*url:\s*[`\"']([^`\"'$]+)", text):
        url = m.group(1).split("?")[0]
        if url in tab_paths:
            line = text[: m.start()].count("\n") + 1
            bad_nav.append(f"{f.relative_to(ROOT)}:{line}  wx.navigateTo → {url}（tabBar 页，必须用 utils/nav.go）")
    for m in re.finditer(r"wx\.switchTab\s*\(\s*\{\s*url:\s*[`\"']([^`\"']+)", text):
        if "?" in m.group(1):
            line = text[: m.start()].count("\n") + 1
            bad_nav.append(f"{f.relative_to(ROOT)}:{line}  switchTab 不支持 query 参数：{m.group(1)}")

if bad_nav:
    print(f"跳转调用有误 {len(bad_nav)} 处（会静默失败，用户侧表现为点击无反应）：")
    for b in bad_nav:
        print("  BADNAV:", b)
else:
    print("页面跳转调用全部合法 OK")

sys.exit(1 if (missing or undef or bad_expr or bad_nav) else 0)

