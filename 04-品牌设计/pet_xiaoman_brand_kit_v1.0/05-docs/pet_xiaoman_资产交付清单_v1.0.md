# pet_xiaoman · 品牌资产交付清单

> 版本 v1.0 · 2026-09-05 · graphic-design-guide（第二轮 4/4 · 收尾）
> 命名规范：`chongxiaoman_{物料类型}_{尺寸}_{版本}.{格式}`

## 一、资产目录结构（目标态）

```
pet_xiaoman_brand_kit_v1.0/
├── 01-logo/
│   ├── source/                          # 精稿源文件（SVG/Figma，设计师产出）
│   │   ├── chongxiaoman_logo_图形标_master.svg
│   │   ├── chongxiaoman_logo_组合横版_master.svg
│   │   └── chongxiaoman_logo_组合竖版_master.svg
│   └── export/
│       ├── png/（透明底：256/128/64/32/16px 五档）
│       └── mono/（反白版 + 深松单色版）
├── 02-color/
│   └── chongxiaoman_色值表_v1.0（HEX/RGB/CMYK/PANTONE）
├── 03-font/
│   ├── LXGWWenKai-Medium.ttf            # 霞鹜文楷（OFL，✅ 已随包；最新版无 Bold，用 Medium+合成加粗）
│   ├── FONT_SOURCES.md                  # 其余字体精确下载地址与授权（思源黑体/阿里普惠）
│   └── （思源黑体 Bold / 阿里普惠 3.0）   # 按 FONT_SOURCES.md 获取（体积大不进 git）
├── 04-online/
│   ├── miniapp/（头像 400×400 + 分享卡 500×400）
│   ├── xhs/（头像 400×400 + 竖版封面 1242×1656 三套 + 内页）
│   └── favicon/（16/32/48）
└── 05-docs/（本批次 5+4 份方案文档）
```

## 二、当前状态盘点（2026-09-05 更新：kit 已落地）

| 资产 | 状态 | 下一步 |
|---|---|---|
| 品牌策略/调研/色彩/字体/线上规格 | ✅ 05-docs 已归档 | — |
| logo 精稿（图形标/反白/组合横版 SVG） | ✅ 01-logo/source 已交付（锚点偏移+线宽节奏已做） | 设计师可在此基础上做渲染级微调 |
| 图形标 PNG 七尺寸 + 反白 PNG | ✅ 01-logo/export/png 已交付（16-512px） | — |
| 线上成图（小程序头像/小红书头像/App icon 1024/favicon） | ✅ 04-online 已交付 | — |
| 字体 | ✅ 霞鹜文楷 Medium 已随包；思源黑体/阿里普惠见 03-font/FONT_SOURCES.md | — |
| 小红书封面成图 | ⬜ 内容资产，随笔记产出时制作（模板骨架在 04-online 规格内） | — |

## 三、方向 A「将满的圆」结构示意 SVG（初稿）

> ⚠️ **性质声明**：这是给设计师的结构参数示意（缺口 137°、爪印比例、线宽关系已按方案 A 定义），
> **不是精稿**——精稿必须按反AI八条第 1 条手工调整锚点（破坏完美几何），并做小尺寸（16/32px）渲染测试。

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="200" height="200">
  <!-- 将满的圆：缺口 137°，起点角度刻意偏移 -7°（禁整数角度）；线宽 3:2 有机变化需精稿手工调 -->
  <circle cx="100" cy="100" r="72" fill="none"
          stroke="#3D5C57" stroke-width="9"
          stroke-linecap="round"
          stroke-dasharray="286 167"
          transform="rotate(-97 100 100)"/>
  <!-- 抽象三趾爪印（缺口处，占圆内 ~25%，偏心放置） -->
  <g fill="#3D5C57">
    <ellipse cx="103" cy="88" rx="10" ry="12" transform="rotate(-8 103 88)"/>
    <ellipse cx="86"  cy="98" rx="7.5" ry="9"  transform="rotate(-14 86 98)"/>
    <ellipse cx="118" cy="97" rx="7"   ry="8.5" transform="rotate(9 118 97)"/>
    <path d="M88 112 Q103 104 118 111 Q116 128 103 129 Q90 128 88 112 Z"/>
  </g>
</svg>
```

**精稿 checklist（设计师执行）**：
1. 锚点偏移：三趾椭圆中心 ±2-5px 非对称化；圆弧转贝塞尔曲线，半径微扰
2. 线宽节奏：圆弧 8-10px 渐变（非等宽），爪印与圆弧粗细关系校准
3. 16/32/48px 三档缩放渲染测试（favicon 可读性）
4. 反白版（白线）与单色版输出
5. 文字标定制：思源黑体 Bold 圆头化改造 +「满」字三点水替换三枚渐小爪印点

## 四、验收口径

| 项 | 通过标准 |
|---|---|
| 品牌侵略性测试 | 遮住「宠小满」文字，仅凭图形标（缺口圆+爪印）仍能被认出是宠小满 |
| 小尺寸测试 | 16px 下缺口与爪印关系仍可辨 |
| 色彩一致性 | 全资产色值与色彩体系 v1.0 精确一致（无近似色） |
| 排版一致性 | 全物料行高/字距/留白在字体体系 v1.0 参数区间内 |
