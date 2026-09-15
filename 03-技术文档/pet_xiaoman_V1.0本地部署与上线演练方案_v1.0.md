# 宠小满 V1.0 本地部署与上线演练方案 v1.0

> 目的：在购买云资源和提交小程序正式版前，用本地环境模拟一次生产启动、数据迁移、核心接口验证和回滚。
> 适用阶段：V1.0 RC / 试运营前；不替代 PyCharm 日常开发启动方式。

## 1. 两套本地运行模式

| 模式 | API | 后台 | 数据库 | 用途 |
|---|---|---|---|---|
| 开发模式 | PyCharm `8010` | Vite `5173` | SQLite 或当前联调库 | 日常开发、调试、页面修改 |
| V1.0 仿真 | Docker `18010` | Nginx `15173` | MySQL 8.0 容器 | 上线前发布、迁移、回滚演练 |

两套模式可以并存。V1.0 仿真模式不占用 `8010/5173`，不会影响哥拿坡原有的 PyCharm 配置。

## 2. 文件清单

- `06-项目编码/docker-compose.v1.local.yml`：MySQL、FastAPI、后台 Nginx 编排。
- `06-项目编码/pet_xiaoman_api/.env.v1.local.example`：本地发布环境变量模板。
- `06-项目编码/deploy_v1_local.sh`：首次配置、迁移、种子、构建、启动和健康检查。
- `06-项目编码/rollback_v1_local.sh`：停止、镜像恢复和数据重置。
- `06-项目编码/pet_xiaoman_api/Dockerfile`：非 root API 容器，uploads 使用独立数据卷。
- `06-项目编码/pet_xiaoman_admin/Dockerfile`：Vue 构建 + Nginx 静态托管。
- `06-项目编码/pet_xiaoman_admin/nginx.conf`：SPA 回退和 `/api`、`/uploads` 同源代理。

## 3. 首次运行

前置条件：安装并启动 Docker Desktop。

```bash
cd 06-项目编码
./deploy_v1_local.sh
```

首次运行会复制环境模板到 `pet_xiaoman_api/.env.v1.local` 并停止，先检查本地数据库密码和两个 token 密钥，再重新执行。

启动后访问：

- 后台：`http://127.0.0.1:15173`
- API 健康：`http://127.0.0.1:18010/healthz`
- API 文档：`http://127.0.0.1:18010/docs`

本地演示账号沿用种子脚本：平台超管 `superadmin / super123456`，门店店长 `petxiaoman / petxiaoman123`。上线前必须更换。

## 4. V1.0 验收顺序

1. API `/healthz` 返回 `ok=true`。
2. 后台登录页可访问，平台超管能看到门店管理。
3. 平台超管查看示例门店品牌与门店账号。
4. 后台商品、服务价格和订单接口返回 200。
5. C 端开发工具将 API 指向 `http://127.0.0.1:18010` 或局域网地址，验证门店品牌和价格。
6. 完成预约、确认、服务节点、影像上传、交付、完成的主流程。
7. 执行 `./rollback_v1_local.sh stop`，再启动，确认 MySQL 数据和上传文件仍存在。
8. 第二次部署后执行 `./rollback_v1_local.sh restore`，确认旧镜像可恢复。

## 5. 与云上线的差异

本地仿真用 MySQL 容器和 uploads 数据卷；云上需要替换为托管 MySQL、COS、正式域名、HTTPS、微信合法域名和支付回调地址。支付、地图、订阅消息仍按配置位开启，不因本地仿真提前打开。

## 6. 禁止事项

- 不要把 `.env.v1.local` 提交到 Git。
- 不要把生产数据库密码写入 Compose 文件。
- 不要在生产环境开启 SQLite fallback。
- 不要把 MySQL 端口暴露到公网。
- `data-reset` 会删除本地 V1.0 数据卷，仅用于重新演练。
