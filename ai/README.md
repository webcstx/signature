# 三模型对话（豆包 / 通义千问 / DeepSeek）

一套 OpenAI 兼容接口，三个模型随时切换。豆包密钥是硬性前提，没有它服务不启动。

## 一、启动（在 Codespace 终端里）

```bash
cd /workspaces/signature && git pull && bash ai/start.sh
```

第一次会自动建 `.venv`、装依赖。看到 `Uvicorn running on http://0.0.0.0:8000` 就成功了。

## 二、配密钥

```bash
cd /workspaces/signature/ai
cp .env.example .env
nano .env
```

至少填 `DOUBAO_API_KEY`，想用千问/DeepSeek 就把对应的也填上。存盘后重新 `bash start.sh`。

- 豆包（火山方舟）：`DOUBAO_API_KEY`，`DOUBAO_MODEL` 一般填接入点 ID（`ep-` 开头）
- 通义千问（DashScope）：`QWEN_API_KEY`，模型默认 `qwen-plus`
- DeepSeek：`DEEPSEEK_API_KEY`，模型默认 `deepseek-chat`

## 三、打开页面

Codespace 会把端口自动转发：在「端口」面板里把 8000 设为公开（Public），
浏览器打开对应的 https 地址即可。手机也能直接访问。

## 四、规则

| 规则 | 值 | 触发后的返回 |
|---|---|---|
| 单次对话总字数 | 40000 | 413 |
| 同一 IP 请求间隔 | ≥1000ms | 429 |
| 未配密钥的模型 | 不可选、置灰 | 400 |
| 没有豆包密钥 | 服务拒绝启动 | 退出码 1 |

## 五、接口

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H 'Content-Type: application/json' \
  -d '{"model":"doubao","messages":[{"role":"user","content":"你好"}]}'
```

`model` 取 `doubao` / `qwen` / `deepseek`。`GET /api/models` 返回可选模型与限制。
