"""三模型统一配置：豆包（火山方舟）/ 通义千问（DashScope）/ DeepSeek。

三家都提供 OpenAI 兼容的 /chat/completions 接口，
所以只要换 base_url + api_key + model 就能切换，调用代码完全共用。
"""
import os

# 如果装了 python-dotenv，就自动读取同目录的 .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
except Exception:
    pass

# ---------- 硬性限制 ----------
MAX_CHARS = int(os.environ.get("MAX_CHARS", "40000"))   # 单次对话总字数上限
MIN_INTERVAL_MS = int(os.environ.get("MIN_INTERVAL_MS", "1000"))  # 同一 IP 最小请求间隔

# ---------- 豆包：火山引擎方舟 ----------
DOUBAO = {
    "key": os.environ.get("DOUBAO_API_KEY", ""),
    "base": os.environ.get("DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"),
    # 方舟一般填接入点 ID（ep- 开头），也可以填模型名
    "model": os.environ.get("DOUBAO_MODEL", "doubao-pro-32k"),
    "label": "豆包",
}

# ---------- 通义千问：阿里云 DashScope 兼容模式 ----------
QWEN = {
    "key": os.environ.get("QWEN_API_KEY", ""),
    "base": os.environ.get("QWEN_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1"),
    "model": os.environ.get("QWEN_MODEL", "qwen-plus"),
    "label": "通义千问",
}

# ---------- DeepSeek ----------
DEEPSEEK = {
    "key": os.environ.get("DEEPSEEK_API_KEY", ""),
    "base": os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
    "model": os.environ.get("DEEPSEEK_MODEL", "deepseek-chat"),
    "label": "DeepSeek",
}

PROVIDERS = {
    "doubao": DOUBAO,
    "qwen": QWEN,
    "deepseek": DEEPSEEK,
}

REQUIRED_PROVIDER = "doubao"   # 豆包密钥是启动的硬性前提
