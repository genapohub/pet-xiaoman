#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.v1.local.yml"
ENV_FILE="$ROOT_DIR/pet_xiaoman_api/.env.v1.local"
PREVIOUS_API="$ROOT_DIR/.v1-local.previous.api"
PREVIOUS_ADMIN="$ROOT_DIR/.v1-local.previous.admin"

if ! command -v docker >/dev/null 2>&1; then
  echo "错误：未找到 Docker。请先安装并启动 Docker Desktop。" >&2
  exit 1
fi

if [ ! -f "$ENV_FILE" ]; then
  echo "首次运行：创建本地 V1.0 环境文件。"
  cp "$ROOT_DIR/pet_xiaoman_api/.env.v1.local.example" "$ENV_FILE"
  echo "已生成：$ENV_FILE"
  echo "请检查并修改 MYSQL_ROOT_PASS、TOKEN_SECRET、STAFF_TOKEN_SECRET 后重新运行。" >&2
  exit 2
fi

dc=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")

save_previous_image() {
  local service="$1"
  local output="$2"
  if image_id=$("${dc[@]}" images -q "$service" 2>/dev/null) && [ -n "$image_id" ]; then
    printf '%s\n' "$image_id" > "$output"
  fi
}

echo "[1/6] 记录当前镜像，保留本地回滚点"
save_previous_image api "$PREVIOUS_API"
save_previous_image admin "$PREVIOUS_ADMIN"

echo "[2/6] 启动 MySQL"
"${dc[@]}" up -d mysql

echo "[3/6] 等待 MySQL 健康"
for i in $(seq 1 30); do
  if "${dc[@]}" exec -T mysql mysqladmin ping -h 127.0.0.1 -u root -p"$(grep '^MYSQL_ROOT_PASS=' "$ENV_FILE" | cut -d= -f2-)" --silent >/dev/null 2>&1; then
    break
  fi
  if [ "$i" -eq 30 ]; then
    echo "错误：MySQL 30 次检查仍未就绪。" >&2
    exit 1
  fi
  sleep 2
done

echo "[4/6] 执行多租户迁移与本地演示种子"
"${dc[@]}" run --rm --no-deps api python -m scripts.migrate_tenant
"${dc[@]}" run --rm --no-deps api python -m scripts.init_local_db

echo "[5/6] 构建并启动 API 与后台"
"${dc[@]}" up -d --build api admin

echo "[6/6] 检查服务"
"${dc[@]}" ps
echo
echo "V1.0 本地仿真已启动："
echo "- 后台：http://127.0.0.1:15173"
echo "- API：http://127.0.0.1:18010"
echo "- API 文档：http://127.0.0.1:18010/docs"
echo "- 停止服务：$ROOT_DIR/rollback_v1_local.sh stop"
