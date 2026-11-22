"""三模型聊天服务（豆包 / 通义千问 / DeepSeek），统一走 OpenAI 兼容协议。

启动：
    python app.py            # 默认 0.0.0.0:8000
    PORT=8080 python app.py

规则：
    1. 没有豆包密钥，服务直接拒绝启动；
    2. 单次对话总字数超过 MAX_CHARS（默认 40000）→ 413；
    3. 同一 IP 两次请求间隔小于 MIN_INTERVAL_MS（默认 1000ms）→ 429。
"""
import os
import sys
import time
import json
import threading

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

import config

# ---------------- 启动自检 ----------------
if not config.PROVIDERS[config.REQUIRED_PROVIDER]["key"].strip():
    print("=" * 60)
    print("启动失败：没有检测到豆包（火山方舟）密钥。")
    print("豆包密钥是整个服务的硬性前提，请先设置环境变量：")
    print("    export DOUBAO_API_KEY=你的豆包密钥")
    print("如果还需要千问 / DeepSeek，再分别设置 QWEN_API_KEY、DEEPSEEK_API_KEY。")
    print("=" * 60)
    sys.exit(1)

app = FastAPI(title="三模型聊天服务")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_lock = threading.Lock()
_last_request = {}          # ip -> 上次请求时间戳
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@app.get("/")
async def index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/models")
async def models():
    data = []
    for pid, cfg in config.PROVIDERS.items():
        data.append({
            "id": pid,
            "label": cfg["label"],
            "model": cfg["model"],
            "enabled": bool(cfg["key"].strip()),
        })
    return {
        "models": data,
        "max_chars": config.MAX_CHARS,
        "min_interval_ms": config.MIN_INTERVAL_MS,
        "required": config.REQUIRED_PROVIDER,
    }


@app.post("/api/chat")
async def chat(request: Request):
    ip = _client_ip(request)
    now = time.time()

    with _lock:
        last = _last_request.get(ip, 0)
        gap_ms = (now - last) * 1000
        if gap_ms < config.MIN_INTERVAL_MS:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "请求过于频繁",
                    "detail": f"同一 IP 最少间隔 {config.MIN_INTERVAL_MS} 毫秒，"
                              f"当前 {int(gap_ms)} 毫秒，请稍后再试",
                },
            )
        _last_request[ip] = now

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "请求体不是合法 JSON"})

    model_id = (body.get("model") or "").strip()
    messages = body.get("messages") or []

    if model_id not in config.PROVIDERS:
        return JSONResponse(
            status_code=400,
            content={"error": f"未知模型：{model_id}", "detail": f"可选：{'、'.join(config.PROVIDERS)}"},
        )

    cfg = config.PROVIDERS[model_id]

    if not cfg["key"].strip():
        return JSONResponse(
            status_code=400,
            content={"error": f"{cfg['label']} 尚未配置密钥",
                     "detail": f"请设置环境变量后重启服务"},
        )

    if not isinstance(messages, list) or not messages:
        return JSONResponse(status_code=400, content={"error": "消息不能为空"})

    total_chars = 0
    for m in messages:
        if not isinstance(m, dict):
            return JSONResponse(status_code=400, content={"error": "消息格式错误"})
        content = m.get("content")
        if not isinstance(content, str):
            return JSONResponse(status_code=400, content={"error": "消息内容必须是字符串"})
        total_chars += len(content)
        if m.get("role") not in ("system", "user", "assistant"):
            return JSONResponse(status_code=400, content={"error": f"不支持的角色：{m.get('role')}"})

    if total_chars > config.MAX_CHARS:
        return JSONResponse(
            status_code=413,
            content={
                "error": "对话已超过字数上限",
                "detail": f"上限 {config.MAX_CHARS} 字，当前 {total_chars} 字",
            },
        )

    payload = {
        "model": cfg["model"],
        "messages": messages,
    }
    if body.get("temperature") is not None:
        payload["temperature"] = body["temperature"]
    if body.get("max_tokens") is not None:
        payload["max_tokens"] = body["max_tokens"]

    url = cfg["base"].rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {cfg['key'].strip()}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(url, headers=headers, json=payload)
    except httpx.TimeoutException:
        return JSONResponse(status_code=504, content={"error": "上游模型响应超时"})
    except Exception as e:
        return JSONResponse(status_code=502, content={"error": "请求上游失败", "detail": str(e)})

    if resp.status_code != 200:
        try:
            upstream = resp.json()
        except Exception:
            upstream = {"raw": resp.text[:800]}
        return JSONResponse(
            status_code=502,
            content={
                "error": f"上游返回 {resp.status_code}",
                "provider": model_id,
                "upstream": upstream,
            },
        )

    data = resp.json()
    try:
        text = data["choices"][0]["message"]["content"]
    except Exception:
        return JSONResponse(status_code=502, content={"error": "上游返回结构异常", "upstream": data})

    usage = data.get("usage") or {}
    return {
        "model": model_id,
        "model_name": cfg["model"],
        "reply": text,
        "usage": usage,
        "chars": total_chars,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", "8000"))
    print(f"服务启动：http://0.0.0.0:{port}  （字数上限 {config.MAX_CHARS}，间隔 {config.MIN_INTERVAL_MS}ms）")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
