# pet_xiaoman_api · pet_xiaoman API

宠物善终门店系统后端（单店版）。技术栈与决策见根目录 `02-技术文档/pet_xiaoman_技术选型方案_v1.1.md`（ADR-001~006）。

## 本地开发

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload        # 接口文档: /docs（即接口协议来源）
pytest                                # 状态机/健康检查测试
```

- 开发库默认 SQLite（免配置）；生产/联调走 MySQL（ADR-002），环境变量见 `app/config.py`
- 支付模块功能开关：`PAY_ENABLED=true` 且商户号配置后启用（PRD §10.1）
- 接口规范：`/api/c/*` 客户端 · `/api/b/*` 后台

## 结构
- `app/services/order_state.py` — 订单状态机（PRD §6.4 唯一实现，非法流转拒绝）
- `app/services/payment.py` — 微信支付框架（验签 fail-check / 幂等落账 / 退款）
