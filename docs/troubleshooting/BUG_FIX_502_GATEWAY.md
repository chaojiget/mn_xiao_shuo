# 修复 502 Bad Gateway 错误

## 问题描述

前端聊天界面返回错误:
```
Server error '502 Bad Gateway' for url 'http://0.0.0.0:4000/chat/completions'
```

## 根本原因

有三个配置问题导致后端无法正确连接到 LiteLLM Proxy:

### 1. 环境变量展开问题

在 `.env` 文件中:
```bash
ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}  # ❌ 错误
```

环境变量不会自动展开 `${...}` 引用,导致 `ANTHROPIC_AUTH_TOKEN` 的值是字面量字符串 `"${LITELLM_MASTER_KEY}"` 而不是实际的 key。

### 2. 缺少 proxy_url 配置

`config/llm_backend.yaml` 中的 `litellm` 部分缺少 `proxy_url` 字段,导致后端使用了错误的默认地址。

### 3. 启动脚本环境变量传递问题

`start_all_with_agent.sh` 使用 `uv run uvicorn` 启动后端,但 `uv run` 不会自动传递环境变量给子进程,导致后端无法读取到 `.env` 中的配置。

## 解决方案

### 修复 1: 直接设置环境变量值

修改 `.env` 文件:
```bash
# 修复前
ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}

# 修复后
ANTHROPIC_AUTH_TOKEN=sk-litellm-70a5a521f6d59321dc6618f00d64eee9
```

### 修复 2: 添加 proxy_url 配置

修改 `config/llm_backend.yaml`:
```yaml
litellm:
  proxy_url: "http://0.0.0.0:4000"  # ✅ 添加此行
  config_path: "./config/litellm_config.yaml"
  model: "deepseek"
  temperature: 0.7
  max_tokens: 1000
```

### 修复 3: 修复启动脚本

修改 `start_all_with_agent.sh`:
```bash
# 修复前 (使用 uv run，环境变量不会传递)
cd web/backend
uv run uvicorn main:app --reload --port 8000 > ../../logs/backend.log 2>&1 &

# 修复后 (直接调用 .venv 中的 uvicorn，确保环境变量传递)
cd web/backend
../../.venv/bin/uvicorn main:app --reload --port 8000 > ../../logs/backend.log 2>&1 &
```

### 修复 4: 使用修复后的脚本启动

```bash
# 停止所有服务
./stop_all.sh

# 使用修复后的脚本启动
./start_all_with_agent.sh
```

## 验证修复

### 方法1: 测试聊天API

```bash
source .venv/bin/activate
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/chat/stream',
    json={'message': '你好', 'history': []},
    stream=True
)
print(f'状态码: {response.status_code}')
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
"
```

预期输出:
```
状态码: 200
data: {"type": "text", "content": "你好"}
data: {"type": "text", "content": "！"}
...
data: {"type": "done"}
```

### 方法2: 使用前端UI

1. 打开浏览器访问 `http://localhost:3000`
2. 进入聊天页面
3. 发送消息
4. 应该能看到流式响应,而不是 502 错误

## 相关文件

- `.env` - 环境变量配置
- `config/llm_backend.yaml` - LLM后端配置
- `start_all_with_agent.sh:106-107` - 后端启动命令
- `web/backend/llm/litellm_backend.py:40` - Proxy URL 读取逻辑
- `web/backend/llm/litellm_backend.py:59-63` - HTTP 客户端初始化

## 防止问题再次发生

1. **环境变量文档化**: 在 `.env.example` 中添加注释说明不要使用 `${VAR}` 语法
2. **配置验证**: 在启动时验证 `proxy_url` 配置是否存在
3. **更好的错误消息**: 在认证失败时提供更清晰的错误信息
4. **启动脚本规范**: 避免使用 `uv run` 启动需要环境变量的服务,直接调用虚拟环境中的可执行文件

## 时间线

- **2025-02-11 17:14**: 首次报告 502 错误
- **2025-02-11 17:18**: 识别环境变量和配置问题
- **2025-02-11 17:21**: 修复 .env 和 llm_backend.yaml
- **2025-02-11 17:25**: 用户反馈UI仍报错
- **2025-02-11 17:27**: 发现 start_all_with_agent.sh 的 `uv run` 问题
- **2025-02-11 17:29**: 修复启动脚本并验证成功

## 相关问题

无

## 受影响的版本

所有使用 LiteLLM Proxy 的版本

## 修复状态

✅ 已修复并验证
