# pet_xiaoman_B端后台UI精致化优化记录_v1.1

> 日期：2026-09-11  
> 范围：B 端后台管理系统 `pet_xiaoman_admin`  
> 输入依据：`pet_xiaoman_PRD_v1.2.md`、品牌策略/色彩体系、C 端最终 UI 精致化方向

## 结论

本轮把后台从“Element Plus 默认管理模板”升级为“宠小满门店履约工作台”。方向不是做营销化视觉，而是在不牺牲 B 端效率的前提下，统一品牌质感、菜单图标、操作图标和 CRUD 状态。

优化后的后台基调：纸感暖底、暖松绿主操作、陶土色仅作轻提示、表格高密但不压迫、关键操作全部“图标 + 文字”双标识。

## 背景/目标

### 使用场景

后台主要给门店店员/店长处理订单、价格、纪念品、寄存和客户回访。PRD 明确要求 B 端“一切页面以少输入、多选择、大按钮为原则”，所以本轮重点不是增加装饰，而是提升高频操作的清晰度和可信感。

### 设计目标

1. 与 C 端最终风格保持同源：暖松绿、纸感白、克制陶土色。
2. 保持 B 端效率：列表、筛选、操作区信息密度不下降。
3. CRUD 操作可识别：编辑、版本、上下架、续存、取回、查看都配图标和文字。
4. 降低误操作：下架、上架、取回等动作增加二次确认。

## 方案

| 模块 | 优化点 | 业务价值 |
|---|---|---|
| 全局 Token | 新增纸感背景、柔和绿底、焦点光晕、卡片悬浮阴影、抽屉底部毛玻璃 | 后台与 C 端品牌同源，不再像通用模板 |
| 主框架 | 侧栏升级为品牌工作台样式，菜单图标重新语义化，顶部增加“单店版”标识 | 员工能明确当前系统定位和版本边界 |
| 页面头 | 增加统一后台眉标与品牌点缀，标题区层次更稳定 | 页面识别更精致，避免散乱标题 |
| 筛选区 | 从散落控件改为独立筛选面板 | 提升查询页工具感，减少视觉漂移 |
| 表格 | 表头浅绿、圆角边界、行 hover 同源品牌色 | 增强可扫读性和品牌一致性 |
| 操作按钮 | 新增 `PxActionButton`，统一图标、tooltip、语义色、防冒泡 | 表格行点击和按钮点击不互相干扰 |
| 抽屉表单 | 增加图标标题、说明、底部影响提示 | 新建/编辑时明确“保存会影响哪里” |
| 危险动作 | 服务下架、纪念品上下架、寄存取回增加确认弹窗 | 降低误操作和履约风险 |

## 执行

### 已修改文件

- `06-项目编码/pet_xiaoman_admin/src/styles/tokens.css`
- `06-项目编码/pet_xiaoman_admin/src/layout/AdminLayout.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxActionButton.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxFormDrawer.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxTablePage.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxPageHeader.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxEmpty.vue`
- `06-项目编码/pet_xiaoman_admin/src/components/PxStatCard.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/service/ServiceItems.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/product/Products.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/boarding/Boarding.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/order/OrderList.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/order/OrderDetail.vue`
- `06-项目编码/pet_xiaoman_admin/src/views/customer/CustomerList.vue`
- `06-项目编码/pet_xiaoman_admin/vite.config.mjs`

## 验收

### 已执行检查

1. 后台构建：通过。
2. FastAPI 健康检查：`http://127.0.0.1:8010/healthz` 返回 `{"ok":true}`。
3. 浏览器截图走查：1366 桌面与 390 移动宽度无横向溢出。
4. 真实接口页面检查：服务项目、纪念品表格均成功加载数据，操作按钮正常显示。

### 设计自检

| 项 | 结果 |
|---|---|
| C/B 端品牌同源 | 通过，后台继承暖松绿与纸感白 |
| B 端效率密度 | 通过，表格行高与按钮高度仍遵循 PRD |
| 操作图标一致性 | 通过，表格操作统一为图标 + 文字 |
| 危险操作防误触 | 通过，下架/上架/取回均有确认 |
| 响应式 | 通过，1366px 与 390px 无横向溢出 |
| 去 AI 味 | 通过，无紫蓝渐变、无夸张毛玻璃、无 emoji 图标 |

## 后续建议

1. 下一轮可补 B003 订单详情的完整服务时间线视觉，把节点影像、状态呼吸和内部备注保存态做成代表作页面。
2. 真实门店使用前，建议用 3 条真实订单走一次“接单-上传影像-收款-完成”的全链路演练。
3. 若后续做多租户，侧栏顶部“单店版”可升级为门店切换器。
