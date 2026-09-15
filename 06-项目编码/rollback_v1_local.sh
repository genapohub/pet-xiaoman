#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.v1.local.yml"
ENV_FILE="$ROOT_DIR/pet_xiaoman_api/.env.v1.local"
PREVIOUS_API="$ROOT_DIR/.v1-local.previous.api"
PREVIOUS_ADMIN="$ROOT_DIR/.v1-local.previous.admin"

if [ ! -f "$ENV_FILE" ]; then
  echo "未找到本地 V1.0 环境文件：$ENV_FILE" >&2
  exit 1
fi

dc=(docker compose --env-file "$ENV_FILE" -f "$COMPOSE_FILE")
action="${1:-stop}"

case "$action" in
  stop)
    echo "停止 V1.0 仿真服务，保留 MySQL 和 uploads 数据卷。"
    "${dc[@]}" down --remove-orphans
    ;;
  restore)
    if [ ! -s "$PREVIOUS_API" ] || [ ! -s "$PREVIOUS_ADMIN" ]; then
      echo "没有可用的历史镜像回滚点。至少成功部署两次后才可执行 restore。" >&2
      exit 2
    fi
    api_image="$(cat "$PREVIOUS_API")"
    admin_image="$(cat "$PREVIOUS_ADMIN")"
    echo "恢复 API 镜像：$api_image"
    echo "恢复后台镜像：$admin_image"
    docker tag "$api_image" pet_xiaoman-v1-api:local
    docker tag "$admin_image" pet_xiaoman-v1-admin:local
    "${dc[@]}" down --remove-orphans
    "${dc[@]}" up -d mysql
    "${dc[@]}" up -d api admin
    "${dc[@]}" ps
    ;;
  data-reset)
    echo "危险操作：删除本地 V1.0 的 MySQL 和上传数据卷。"
    read -r -p "确认输入 RESET-V1-LOCAL：" answer
    if [ "$answer" != "RESET-V1-LOCAL" ]; then
      echo "已取消。"
      exit 0
    fi
    "${dc[@]}" down --volumes --remove-orphans
    ;;
  *)
    echo "用法：$0 [stop|restore|data-reset]" >&2
    exit 1
    ;;
esac
