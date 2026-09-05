# AGENTS.md · 企业级 AI 编程行为规范模板

> 适用于 Claude Code / Cursor / Aider / Continue 等所有支持 AGENTS.md 规范的 AI 编程工具。
> **本文件是宪法**：所有 AI 在本项目里做什么、不做什么、怎么做，必须遵守本文档。
> 项目级文件，复制到你的项目根目录，按需修改 `【项目名】` `【技术栈】` 等占位符。

---

## 第一部分：项目身份（必填区）

```yaml
# === 项目基本信息 ===
项目名：pet_xiaoman（宠物善终门店系统；品牌名：「宠小满」（终名已定 2026-09-05），终名/logo/商标由品牌设计师决策）
项目目标：宠物善终门店系统「宠小满」（单门店定位）——C 端小程序（宠物主预约/透明价格/服务过程可视化）+ B 端后台（门店订单/影像/价格配置）；未来迭代方向（多租户后台 + 小程序品牌装修）已记录于 PRD §12
目标用户：C 端=郑州本地失去宠物的宠物主（首次决策、情绪敏感、信任>价格）；B 端=门店员工（接单、排期、服务执行与记录）
技术栈：已选型（ADR-001~006）：FastAPI 单体 + MySQL 8.0（shop_id 行级多租户）+ Vue3 + Element Plus + 原生微信小程序 + 微信云托管全托管
代码仓库：本地仓库（远程待配）；代码子仓库规划于 04-前后端代码/ 下（pxm-api / pxm-miniapp / pxm-admin）
主要分支：main（受保护）/ develop（开发）
当前阶段：需求阶段（0→1，竞品分析已完成）
项目知识地图：                  # AI 取业务上下文的索引（v1.2）；没有的行删掉，禁止凭空猜业务规则
  业务背景：../宠物善终账号/宠物善终账号_竞品分析_v1.0.md（郑州善终赛道洞察、用户四大痛点、差异化定位）
  业务背景：01-产品文档/pet_xiaoman_PRD_v2.0.md（功能范围/多租户/状态机/字段/权限的唯一事实源）
  业务背景：../宠物善终账号/宠物善终账号_竞品内容详录_v1.0.md（竞品内容原始素材）
  技术选型：02-技术文档/pet_xiaoman_技术选型方案_v1.1.md（ADR-001~006：FastAPI 单体多租户/MySQL shop_id 行级隔离/Vue3+ElementPlus/原生小程序/微信云托管，含"不做"清单）
  接口协议：【PRD 评审后由 backend-dev-guide 产出 API 文档】
  数据模型：【PRD §7.1 字段定义为基线，建表后以 ER 文档为准】
  设计规范：【设计阶段产出】
  部署运维：【按 ADR-005 云托管部署清单，开发期产出】
```

> **AI 必须做的事**：进入项目第一件事是读这份 YAML，理解项目背景再动手；需要业务上下文时按「项目知识地图」取，不要猜。
> **禁止做的事**：不了解项目就盲改代码。

---

## 第二部分：AI 角色定位

```yaml
# === AI 在本项目的角色 ===
主导级别：对话协作（AI 建议，人类审核）    # 不要轻易升级到"AI 主导"
触发场景：所有改动
激活角色清单：                             # 分级规则见 /Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/06-工具链/工具治理白名单.md v1.1
  P0_常驻：tech-lead-guide / frontend-dev-guide / backend-dev-guide / qa-testing-guide / devops-guide / team-orchestrator
  P1_阶段激活：product-plan-guide（当前：需求阶段，出 PRD）/ ux-design-guide（小程序+后台设计阶段）
  # 未勾选的角色 = 本项目未激活，orchestrator 不得调度；激活 P2 挂起角色前须先 refresh 白名单
工具白名单：见 第六部分
工具黑名单：见 第六部分
```

> **激活角色清单的作用**：本项目宪法只约束被激活的角色，未激活角色的边界规则不用写进本文档——这是项目宪法保持精简（AI 遵守率更高）的关键机制。

**主导级别三档**（按风险递增）：

| 档位 | AI 做什么 | 人类做什么 | 适用场景 |
|---|---|---|---|
| 对话协作 | 写代码、改代码 | 全量 review | 默认档，企业项目都用这个 |
| AI 主导 | 提 PR、写测试、跑 CI | 抽查 + 兜底 | 重构、低风险模块 |
| 全自主 | 自己提 PR 自己 merge | 仅看结果 | **本项目禁用** |

---

## 第三部分：AI 能做什么（白名单）

```yaml
能做：
  - 读懂现有代码并解释
  - 按规范写新功能（含测试）
  - 重构指定模块（需人类指定范围）
  - 写单元测试 / 集成测试
  - 跑 lint / format / type check
  - 生成数据库迁移脚本（人类 review 后执行）
  - 生成 API 文档 / OpenAPI spec
  - 生成 commit message / PR description
  - 解释报错并给出修复建议
  - 翻译注释（中↔英）
```

---

## 第四部分：AI 不能做什么（黑名单 · 红线）

```yaml
红线（违反即拒绝）：
  - 直接 push 到 main / master 分支
  - 删除未被 git 跟踪的关键文件
  - 执行 rm -rf / mkfs / dd 等破坏性命令
  - 修改 .env / credentials / secrets 相关文件
  - 调用生产环境数据库（read-only 可以，写不行）
  - 跳过 review 直接 merge 自己的 PR
  - 把客户代码 / 合同 / 财务数据喂给公网模型（敏感代码用 Ollama 本地推理）
  - 在 commit message / PR 描述里泄露密钥
  - 替人类做架构决策（架构变更需人类拍板）
  - 修改 CI/CD 配置（需 DevOps 角色人工审核）
```

> **越权处理**：AI 若发现自己被要求做红线事项，必须**明确拒绝并说明理由**，不能"勉强执行"。

---

## 第五部分：AI 工作流（标准流程）

每个任务必须按以下流程执行：

```
1. 读上下文（AGENTS.md + 相关代码 + 最近 3 次 commit）
2. 明确需求（向人类复述确认，不懂的问而不是猜）
3. 写方案（小改动 1-3 句话说明思路，大改动写设计文档）
4. 写代码（按 第七部分 代码规范）
5. 写测试（覆盖率 ≥ 项目基线）
6. 跑检查（lint / format / type check / 单测必须全绿）
7. 自我 review（对照 第八部分 checklist）
8. 提 PR（标题清晰，描述含：变更原因 + 变更内容 + 验证方式）
9. 等人类 review
10. 反馈迭代（人类提意见 → AI 改 → 再 review）
```

**禁止跳步**：尤其是第 2 步（明确需求）和第 9 步（等 review），跳了就属于"AI 越权"。

---

## 第六部分：工具白名单 / 黑名单

```yaml
工具白名单（允许 AI 主动调用）：
  文件操作：Read / Write / Edit / Glob / Grep
  Git 操作：git status / git diff / git log / git add / git commit / git push（仅限 feature 分支）
  包管理：npm install / pip install -r requirements.txt（需锁版本）
  测试：npm test / pytest / go test（只读，不写生产数据）
  容器：docker build / docker run --rm（不挂载主机目录）

工具黑名单（AI 不可调用）：
  破坏性：rm -rf / mkfs / dd / chmod 777
  生产数据库：mysql -h prod-* / psql prod-*（写操作）
  密钥相关：cat .env / printenv | grep SECRET
  网络外发：curl POST 到非项目内网地址
  CI/CD 改写：修改 .github/workflows / .gitlab-ci.yml
  远程执行：ssh prod-* / kubectl --context=prod
```

> **最小特权原则**：白名单以外的工具，AI 调用前必须先问人类，得到明确许可才能用。

---

## 第七部分：代码规范

```yaml
命名：
  变量：camelCase（前端）/ snake_case（后端 Python）
  类：PascalCase
  常量：UPPER_SNAKE_CASE
  文件：kebab-case（小写中划线）
  布尔变量：is_/has_/should_ 前缀

注释：
  函数必须有 docstring（解释做什么，不是怎么做的）
  复杂逻辑必须有行内注释（解释为什么这么做）
  TODO 必须带负责人 + 预计完成时间
  不要写"这是一个函数"这种废话注释

目录结构：
  src/        # 源代码
  tests/      # 测试
  docs/       # 文档
  scripts/    # 一次性脚本
  config/     # 配置

测试覆盖：
  核心业务逻辑：≥ 80%
  工具函数：≥ 90%
  UI 组件：≥ 60%
  新功能 PR 必须带测试，无测试 = 不通过 review
```

---

## 第八部分：Review Checklist（AI 产出物自检）

每次提 PR 前，AI 必须逐条对照：

```markdown
- [ ] 代码已通过 lint（无 warning）
- [ ] 代码已通过 format（与项目风格一致）
- [ ] type check 全绿（TS / Python type hints）
- [ ] 单测全绿，新增功能有对应测试
- [ ] 没动红线（见 第四部分）
- [ ] 没在白名单外调用工具（见 第六部分）
- [ ] 命名规范（见 第七部分）
- [ ] 注释清楚（docstring + 复杂逻辑行内注释）
- [ ] 没有遗留 console.log / print / debugger
- [ ] 没有写死的密钥 / 假数据 / TODO 占位
- [ ] commit message 清晰（feat: / fix: / refactor: / docs: 前缀）
- [ ] PR 描述含：变更原因 + 变更内容 + 验证方式
```

**没勾完的不能提 PR**。

---

## 第九部分：回滚机制

```yaml
回滚触发条件：
  - CI 红了且 10 分钟内修不好
  - 线上监控告警（错误率 > 阈值）
  - AI 产出代码被发现含安全漏洞
  - 人类 review 发现架构性问题

回滚动作：
  1. git revert <commit-hash>（首选，保留历史）
  2. git revert 失败 → git reset --hard <上一个稳定 tag>
  3. 立即通知人类 owner
  4. 在事故频道写时间线

版本标记：
  - 每个稳定版本打 git tag（v1.0.0 格式）
  - Harness 配置变更也走 tag（harness-v1.0）
  - 至少保留 5 个 tag 可回滚
```

---

## 第十部分：沟通约定

```yaml
与人类沟通：
  遇到歧义：问，不要猜
  遇到风险：先说风险再做，不要闷头做
  遇到完成：明确说"完成" + 列出产出物
  遇到失败：说"失败" + 失败原因 + 下一步建议，不要掩饰

PR 沟通：
  标题：<type>(<scope>): <subject>，type ∈ feat/fix/refactor/docs/test/chore
  描述模板：
    ## 变更原因
    ## 变更内容
    ## 验证方式
    ## 风险点
    ## 关联 issue

Code Review 沟通：
  AI 提的修改：人类不批就不 merge
  人类提的修改：AI 必须执行，不要争论风格
  分歧大时：升级到架构师 / Tech Lead 决策
```

---

## 附录 A：模板使用指南

1. **复制本文件**到项目根目录，改名为 `AGENTS.md`
2. **第一部分（项目身份）必须填**，否则 AI 没法工作
3. **第二部分（角色定位）按项目风险等级选**，默认"对话协作"
4. **第三~六部分按需微调**，但红线不要轻易删
5. **第七部分（代码规范）和项目已有 ESLint / Pylint 配置对齐**，冲突时以工具配置为准
6. **第八部分 checklist 跑通才能提 PR**
7. **`/Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/04-Evals/regression-cases.json` 套件**配合本文件使用，作为回归测试基线

---

## 附录 B：与 Harness 其他组件的关系

```
本文件（AGENTS.md）= 行为规范 / 宪法
├── project-tracker.md = 任务状态持久化（本目录）
├── /Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/04-Evals/regression-cases.json = AI 产出物回归测试
├── /Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/05-实战/项目记录.md = 落地过程复盘
├── /Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/06-工具链/工具治理白名单.md = 工具级最小特权清单（v1.1 起按 P0/P1/P2 分级维护）
├── /Users/macos/Downloads/WorkBuddy/日常办公/05-Harness/06-工具链/MCP-工具分级.md = L1~L5 通用风险分级
└── SECURITY.md = 密钥 / 脱敏 / 合规三件套
```

本文件定**原则**，其他文件定**执行**。

---

## 附录 C：Harness 版本管理（配置变更追溯）

> Harness 配置（AGENTS.md / SECURITY.md / MCP-工具分级 / regression-cases）属于生产级资产，变更必须可追溯。

### C.1 版本号约定

```
格式：vX.Y（X=大版本，Y=小版本）
大版本变更（X）：架构调整 / 红线增删 / 角色分级调整
小版本变更（Y）：条款细化 / 案例补充 / 工具分级调整
补丁版本：内部迭代不打 tag，仅 commit
```

### C.2 git tag 约定

```bash
# Harness 配置变更必须打 tag
git tag -a harness-v1.0 -m "AGENTS.md v1.0 + SECURITY.md v1.0 + MCP-工具分级 v1.0"
git push origin harness-v1.0

# 后续每次配置变更
git tag -a harness-v1.1 -m "..."
git push origin harness-v1.1
```

**tag 命名规则**：`harness-vX.Y`（X.Y 与 AGENTS.md 底部版本号一致）

### C.3 变更触发条件（必须打新 tag）

- AGENTS.md 任一段内容修改
- SECURITY.md 红线 / 事故响应 / 模型分级调整
- MCP-工具分级新增/降级/废弃工具
- regression-cases.json 新增/修改/删除 case
- 工具治理白名单（按角色分类）调整

### C.4 变更清单（CHANGELOG）

每次打 tag 必须同步更新本节：

```markdown
## harness-v1.2（2026-09-05）
- 本文件第一部分新增「项目知识地图」段：AI 按索引取业务上下文，不猜业务规则（吸收自五层架构对照，见 01-调研/03）
- install.sh 手工待办与 HARNESS_VERSION 同步更新

## harness-v1.1（2026-09-05）
- 工具治理白名单 v1.1：13+1 角色分级为 P0 常驻 6 个 / P1 阶段激活 3 个 / P2 挂起 6 个（角色边界内容未改动）
- 本文件第二部分新增「激活角色清单」机制：项目宪法只约束激活角色，未激活角色 orchestrator 不得调度
- 清理附录 C 后重复的目录树段落（编辑残留）

## harness-v1.0（2026-09-05）
- AGENTS.md v1.0 落地：10 部分 + 2 附录
- SECURITY.md v1.0 落地：密钥/脱敏/合规三件套
- MCP-工具分级 v1.0 落地：132 个工具 L1~L5 分级
- regression-cases.json v1.0 落地：13 case / 5 类
- 工具治理白名单 v1.0 落地：13+1 角色全覆盖
```

### C.5 回滚 Harness 配置

如果新版本 Harness 配置导致 AI 行为异常：

```bash
# 查看 tag 历史
git tag -l "harness-v*"

# 回滚到上一个稳定版本
git checkout harness-v1.0 -- 05-Harness/

# 提交回滚
git commit -m "revert: harness-v1.1 → harness-v1.0（AI 行为异常）"

# 打回滚 tag
git tag -a harness-v1.0.1-revert -m "回滚到 v1.0"
git push origin harness-v1.0.1-revert
```

### C.6 跨工具同步

Harness 配置变更后，必须同步到四个副本：

```bash
# WorkBuddy / Codex / Cursor / ZCode 四端
for d in ~/.workbuddy/skills ~/.codex/skills ~/.cursor/skills-cursor ~/.zcode/skills; do
  [ -d "$d" ] && echo "$d: 需手动同步（暂未自动化）"
done
```

> _本附录与 `01-调研/02-13+1体系行动启示.md` 中的 Recovery（回滚）能力对应_

---

> _维护原则：先骨架再追加细节。本模板先用默认值跑 2 周，再按实际踩坑迭代。_
> _版本：v1.2（2026-09-05）· 由 05-Harness/02-规范/AGENTS.md 同步_
