#!/usr/bin/env bash
# 一条命令完成部署：交互式填密钥 -> 建虚拟环境 -> 装依赖 -> 起服务
set -e
cd "$(dirname "$0")"

echo "================================================"
echo " 三模型对话服务部署（豆包 / 通义千问 / DeepSeek）"
echo "================================================"

# 1) 密钥
if [ -f .env ]; then
  echo "[配置] 检测到已有 .env，直接使用"
  set -a; source .env; set +a
fi

if [ -z "${DOUBAO_API_KEY}" ]; then
  echo
  echo "[配置] 豆包密钥是硬性前提，没有它服务不启动。"
  read -r -s -p "  粘贴豆包密钥后回车: " DOUBAO_API_KEY
  echo
  if [ -z "${DOUBAO_API_KEY}" ]; then
    echo "  没填密钥，退出。"
    exit 1
  fi
fi

if [ -z "${QWEN_API_KEY}" ]; then
  read -r -s -p "  通义千问密钥（不用就回车跳过）: " QWEN_API_KEY || true
  echo
fi

if [ -z "${DEEPSEEK_API_KEY}" ]; then
  read -r -s -p "  DeepSeek 密钥（不用就回车跳过）: " DEEPSEEK_API_KEY || true
  echo
fi

# 服务访问密钥：没配就自动生成一串
if [ -z "${ACCESS_KEY}" ]; then
  ACCESS_KEY=$(python3 -c "import secrets;print(secrets.token_hex(16))")
  echo "[配置] 已自动生成访问密钥：${ACCESS_KEY}"
fi

# 写回 .env（已被 .gitignore 排除，不会进仓库）
{
  echo "DOUBAO_API_KEY=${DOUBAO_API_KEY}"
  echo "DOUBAO_MODEL=${DOUBAO_MODEL:-doubao-pro-32k}"
  echo "QWEN_API_KEY=${QWEN_API_KEY}"
  echo "QWEN_MODEL=${QWEN_MODEL:-qwen-plus}"
  echo "DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}"
  echo "DEEPSEEK_MODEL=${DEEPSEEK_MODEL:-deepseek-chat}"
  echo "ACCESS_KEY=${ACCESS_KEY}"
  echo "MAX_CHARS=${MAX_CHARS:-40000}"
  echo "MIN_INTERVAL_MS=${MIN_INTERVAL_MS:-1000}"
  echo "PORT=${PORT:-8000}"
} > .env
chmod 600 .env
echo "[配置] 已写入 .env（权限 600，且不会被 git 提交）"

# 2) 环境
if [ ! -d .venv ]; then
  echo "[环境] 创建虚拟环境 .venv"
  python3 -m venv .venv
fi
. .venv/bin/activate

echo "[环境] 安装依赖（首次约 1 分钟）"
pip install -q --upgrade pip
pip install -q -r requirements.txt

# 3) 启动
echo "[启动] 端口 ${PORT:-8000} / 字数上限 ${MAX_CHARS:-40000} / 间隔 ${MIN_INTERVAL_MS:-1000}ms"
echo "[启动] 打开方式：端口面板把 ${PORT:-8000} 设为 Public"
echo "[启动] 访问地址：https://<你的空间名>-${PORT:-8000}.app.github.dev/?key=${ACCESS_KEY}"
exec python app.py
