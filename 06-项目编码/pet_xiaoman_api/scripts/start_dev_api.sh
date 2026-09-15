#!/bin/zsh
set -e

cd "$(dirname "$0")/.."

PORT="${PORT:-8010}"
API_HOST="${API_HOST:-127.0.0.1}"
PYTHON_BIN="${PYTHON_BIN:-.venv/bin/python}"

echo "========== 宠小满 API 启动检查 =========="
echo "目录：$(pwd)"
echo "地址：http://${API_HOST}:${PORT}"
echo "说明：同一个 FastAPI 服务同时提供 C 端 /api/c 和后台 /api/b"
echo

if [ ! -x "$PYTHON_BIN" ]; then
  echo "启动失败：找不到 API 项目的 Python 解释器。"
  echo "期望位置：$(pwd)/${PYTHON_BIN}"
  echo "处理方式：在 pet_xiaoman_api 目录重新创建虚拟环境，或在 PyCharm 配置里选择正确解释器。"
  exit 1
fi

if ! "$PYTHON_BIN" --version >/dev/null 2>&1; then
  echo "启动失败：当前 Python 解释器链接已失效，无法执行。"
  echo "当前配置：$(pwd)/${PYTHON_BIN}"
  echo "处理方式：在 pet_xiaoman_api 目录执行：uv venv --python 3.14 --clear .venv"
  echo "然后执行：uv pip install --python .venv/bin/python -r requirements.txt"
  exit 1
fi

if ! "$PYTHON_BIN" -c "import uvicorn, app.main" >/dev/null 2>&1; then
  echo "启动失败：当前解释器缺少依赖，或 app.main 无法导入。"
  echo "处理方式：确认解释器选择的是 pet_xiaoman_api/.venv，并安装 requirements.txt。"
  echo "可执行：.venv/bin/python -m pip install -r requirements.txt"
  exit 1
fi

if lsof -nP -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "启动失败：端口 ${PORT} 已被占用。"
  echo "处理方式："
  echo "1. 如果是旧的 API 进程，先停止它。"
  echo "2. 如果要换端口，启动时设置 PORT=8011，并同步修改后台前端的 VITE_API_TARGET。"
  echo
  lsof -nP -iTCP:"$PORT" -sTCP:LISTEN
  exit 1
fi

echo "检查通过，正在启动 API..."
echo "健康检查：http://${API_HOST}:${PORT}/healthz"
echo "C 端示例：http://${API_HOST}:${PORT}/api/c/products"
echo "后台示例：http://${API_HOST}:${PORT}/api/b/orders"
echo "========================================"

if [ "$1" = "--check" ]; then
  echo "仅检查模式：未启动服务。"
  exit 0
fi

SQLITE_FALLBACK=true "$PYTHON_BIN" -m uvicorn app.main:app --host "$API_HOST" --port "$PORT" --reload
