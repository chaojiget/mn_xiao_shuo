# 快速修复检查清单

## 当遇到 502 Bad Gateway 错误时

### 1. 检查环境变量 ✓

```bash
# 检查 .env 文件
cat .env | grep -E "(LITELLM|ANTHROPIC)"

# 确保以下变量正确设置:
# LITELLM_MASTER_KEY=sk-litellm-xxxxx (实际的key，不是${VAR})
# ANTHROPIC_BASE_URL=http://0.0.0.0:4000
# ANTHROPIC_AUTH_TOKEN=sk-litellm-xxxxx (与LITELLM_MASTER_KEY相同)
```

### 2. 检查配置文件 ✓

```bash
# 检查 llm_backend.yaml
cat config/llm_backend.yaml | grep -A 5 "litellm:"

# 确保包含:
# litellm:
#   proxy_url: "http://0.0.0.0:4000"  <-- 这一行必须存在
#   model: "deepseek"
```

### 3. 检查启动脚本 ✓

```bash
# 检查 start_all_with_agent.sh
grep "uvicorn" start_all_with_agent.sh

# 应该看到:
# ../../.venv/bin/uvicorn main:app --reload --port 8000
# 而不是:
# uv run uvicorn main:app --reload --port 8000
```

### 4. 测试 LiteLLM Proxy

```bash
# 测试 Proxy 是否可访问
curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  http://localhost:4000/v1/models

# 应该返回模型列表
```

### 5. 测试后端 API

```bash
source .venv/bin/activate
python -c "
import requests
response = requests.post(
    'http://localhost:8000/api/chat/stream',
    json={'message': '测试', 'history': []},
    stream=True
)
print(f'状态码: {response.status_code}')
for i, line in enumerate(response.iter_lines()):
    if i >= 3:
        break
    if line:
        print(line.decode('utf-8'))
"
```

## 常见问题

### 问题: "No api key passed in"
**原因**: LiteLLM Proxy 要求认证，但客户端没有传递 API key
**解决**: 确保 `.env` 中的 `ANTHROPIC_AUTH_TOKEN` 设置正确

### 问题: "Failed to connect to localhost port 4000"
**原因**: LiteLLM Proxy 没有运行
**解决**:
```bash
cd /Users/lijianyong/mn_xiao_shuo
source .venv/bin/activate
litellm --config ./config/litellm_config.yaml --host 0.0.0.0 --port 4000 &
```

### 问题: 使用 start_all_with_agent.sh 启动后仍然报错
**原因**: 脚本中使用了 `uv run` 导致环境变量未传递
**解决**: 修改脚本使用 `../../.venv/bin/uvicorn` 而不是 `uv run uvicorn`

## 一键修复命令

```bash
# 停止所有服务
./stop_all.sh

# 清理端口
lsof -ti:4000,8000,3000 | xargs kill -9 2>/dev/null

# 使用修复后的脚本启动
./start_all_with_agent.sh

# 等待5秒
sleep 5

# 验证服务状态
curl -s http://localhost:4000/health || echo "LiteLLM Proxy 未启动"
curl -s http://localhost:8000/health || echo "后端未启动"
curl -s http://localhost:3000 > /dev/null && echo "前端正常" || echo "前端未启动"
```

## 参考文档

- [完整修复文档](./BUG_FIX_502_GATEWAY.md)
- [环境变量配置](../.env)
- [LLM后端配置](../config/llm_backend.yaml)
- [LiteLLM配置](../config/litellm_config.yaml)
