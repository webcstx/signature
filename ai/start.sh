#!/usr/bin/env bash
# 一键启动：建虚拟环境 -> 装依赖 -> 读 .env -> 起服务
set -e
cd "$(dirname "$0")"

if [ ! -d .venv ]; then
  echo "[1/4] 创建 Python 虚拟环境 .venv"
  python3 -m venv .venv
fi
source .venv/bin/activate

echo "[2/4] 安装依赖"
pip install -q --upgrade pip
pip install -q -r requirements.txt

echo "[3/4] 读取配置"
if [ -f .env ]; then
  set -a; source .env; set +a
  echo "    已加载 .env"
else
  echo "    没有 .env，使用系统环境变量"
fi

if [ -z "${DOUBAO_API_KEY}" ]; then
  echo "    错误：DOUBAO_API_KEY 为空，服务无法启动"
  echo "    做法：cp .env.example .env 然后填上豆包密钥"
  exit 1
fi

echo "[4/4] 启动服务，端口 ${PORT:-8000}"
exec python app.py
