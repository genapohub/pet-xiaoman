# pet_xiaoman_C端UI精致化优化记录_v1.2

> 日期：2026-09-10  
> 范围：C 端微信小程序 `pet_xiaoman_miniapp`  
> 输入依据：`pet_xiaoman_PRD_v1.2.md`、品牌手册/色彩/字体体系、`pet_xiaoman_C端设计规范_v1.0.md`

## 结论

本轮从“可用的小程序页面”升级为“有品牌温度的服务界面”，重点解决原实现的三个问题：

1. 页面视觉偏通用卡片堆叠，缺少宠小满的自然有机气质。
2. 价格、预约、进度等关键转化/信任页面，信息层级不够强。
3. 空态、加载、底部操作区和状态头不够统一，精致感不足。

优化后的方向是：纸感暖底、暖松绿同源渐变、暖白卡片、陶土色只用于纪念/当前节点等情绪触点，整体保持“温暖、安宁、坦诚、恰到好处”。

## 背景/目标

### 用户情绪

C 端用户多处在首次决策、悲伤和不确定状态，设计目标不是刺激下单，而是降低认知负担、建立透明信任。

### 业务目标

- 首页 3 秒内传达本地可信、价格公开、过程可见。
- 价格表让用户可以直接比价，减少“还有没有隐藏收费”的疑虑。
- 预约页降低填写压力，同时始终保留费用确认。
- 订单详情强化进度与影像记录，承接“敢给你看”的信任承诺。

## 方案

| 模块 | 优化点 | 业务价值 |
|---|---|---|
| 全局 Token | 新增纸感层次、暖白卡片、同源渐变按钮、轻边框与操作阴影 | 统一页面质感，减少通用模板感 |
| 首页 C001 | 加定位眉标、品牌 logo、三承诺上浮卡、底部承诺条 | 强化第一屏可信度 |
| 价格表 C002/C003 | 增加页面说明头、克制 Tab 指示、价格右侧强视觉、描边选择按钮 | 透明定价更直观，弱化推销感 |
| 预约 C004 | 增加解释性头部、无边框表单、底部固定费用汇总与提交 | 悲伤期操作更轻，避免价格遗忘 |
| 订单 C005/C006 | 订单列表品牌头；详情页状态头、时间线竖线、当前节点呼吸与影像边界 | 提升过程可见的信任感 |
| 纪念品 C007 | 增加温和头部、陶土价格、描边按钮、品牌图形兜底 | 避免电商促销感 |
| 寄存/档案/我的 C008-C010 | 统一品牌状态头、温度空态、客户编号胶囊、菜单细分隔 | 工具页也保持品牌一致性 |

## 执行

### 已修改文件

- `06-项目编码/pet_xiaoman_miniapp/app.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/index/index.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/index/index.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/prices/prices.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/prices/prices.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-create/index.js`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-create/index.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-create/index.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-list/index.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-list/index.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-detail/index.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/order-detail/index.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/products/products.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/products/products.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/boarding-query/query.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/boarding-query/query.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/pets/pets.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/pets/pets.wxss`
- `06-项目编码/pet_xiaoman_miniapp/pages/profile/index.wxml`
- `06-项目编码/pet_xiaoman_miniapp/pages/profile/index.wxss`

## 验收

### 已执行检查

1. JS 语法检查：通过。
2. JSON 解析检查：`app.json`、`project.config.json`、`sitemap.json` 均通过。
3. 品牌禁忌扫描：未发现纯黑、冷蓝、促销红、紫色系、外链占位素材；白色仅用于深色品牌头部与按钮文字。

### 设计自检

| 项 | 结果 |
|---|---|
| 60-30-10 色彩纪律 | 通过，陶土色仅用于纪念/状态刺点 |
| 触控区 ≥44px | 通过，主按钮/输入/行入口均按 88rpx 基线 |
| 空态/加载态 | 通过，核心列表与商品/档案页已覆盖 |
| C004 无悲情元素 | 通过，仅保留操作和确认信息 |
| C006 影像安静呈现 | 通过，无弹窗营销、无促销色 |
| 去 AI 味 | 通过，避免紫蓝渐变、泛卡片、emoji 图标与夸张阴影 |

## 后续建议

1. 用微信开发者工具真机预览 375px/414px 两档，重点看底部固定操作区和 tabBar 是否有遮挡。
2. 若后续有真实门店图片，优先补 C006 影像预览样式和 C007 商品实拍图规范。
3. 下一轮可做 C011 预约成功页与 C012 收银台，把“提交后安心”和“三种支付方式”补成完整闭环。
