# LiteLLM Proxy 设置指南

本文档介绍如何使用 LiteLLM Proxy 模式运行小说生成系统。

## 架构概述

```
┌─────────────────┐
│  前端 (Next.js) │
└────────┬────────┘
         │
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  后端 (FastAPI) │
│  LiteLLMBackend │
└────────┬────────┘
         │
         │ HTTP (OpenAI-compatible API)
         │ Authorization: Bearer $LITELLM_MASTER_KEY
         ▼
┌──────────────────┐
│ LiteLLM Proxy    │
│ localhost:4000   │
└────────┬─────────┘
         │
         │ OpenRouter API
         │ api_key: $OPENROUTER_API_KEY
         ▼
┌──────────────────┐
│  OpenRouter      │
│  各种 LLM 模型   │
└──────────────────┘
```

## 关键组件

### 1. LiteLLM Proxy 服务器

- **地址**: `http://localhost:4000`
- **配置文件**: `config/litellm_config.yaml`
- **启动脚本**: `./start_litellm_proxy.sh`

### 2. 环境变量

需要在 `.env` 文件中配置：

```bash
# OpenRouter API Key (必需)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# LiteLLM Master Key (自动生成或手动设置)
LITELLM_MASTER_KEY=sk-litellm-xxxxx
```

### 3. 模型别名

在配置文件中定义了以下模型别名：

- `deepseek` → `openrouter/deepseek/deepseek-v3.1-terminus-v3-0324` (推荐，性价比最高)
- `claude-sonnet` → `openrouter/anthropic/claude-sonnet-4.5`
- `claude-haiku` → `openrouter/anthropic/claude-3.5-haiku`
- `gpt-4` → `openrouter/openai/gpt-4-turbo`
- `qwen` → `openrouter/qwen/qwen-2.5-72b-instruct`

## 快速开始

### 第一步：启动 LiteLLM Proxy

```bash
./start_litellm_proxy.sh
```

这个脚本会：
1. 检查并安装 `litellm[proxy]`
2. 从 `.env` 读取或生成 `LITELLM_MASTER_KEY`
3. 导出 `OPENROUTER_API_KEY` 环境变量
4. 启动 LiteLLM Proxy 在 `http://0.0.0.0:4000`

### 第二步：测试 Proxy

在另一个终端中运行：

```bash
./test_proxy_e2e.sh
```

或者手动测试：

```bash
# 设置环境变量
export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)

# 测试 API
curl -X POST http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 第三步：启动 Web 服务

```bash
./web/start-web.sh
```

这会启动：
- 后端 FastAPI 服务器 (端口 8000)
- 前端 Next.js 服务器 (端口 3000)

访问 `http://localhost:3000` 开始使用。

## 认证机制

### LiteLLM Proxy 认证

LiteLLM Proxy 使用 **Master Key** 进行认证：

1. 启动时，通过环境变量 `LITELLM_MASTER_KEY` 设置
2. 所有请求必须在 HTTP Header 中携带：
   ```
   Authorization: Bearer $LITELLM_MASTER_KEY
   ```

### 后端代码配置

`web/backend/llm/litellm_backend.py` 中已自动配置：

```python
class LiteLLMBackend(LLMBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 从环境变量读取
        self.api_key = os.environ.get("LITELLM_MASTER_KEY", "")

        # 创建 HTTP 客户端，自动添加 Authorization header
        self.http_client = httpx.AsyncClient(
            base_url=self.proxy_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0
        )
```

## 配置文件说明

### `config/litellm_config.yaml`

```yaml
model_list:
  - model_name: deepseek
    litellm_params:
      model: openrouter/deepseek/deepseek-v3.1-terminus-v3-0324
      api_key: os.environ/OPENROUTER_API_KEY  # 从环境变量读取
      api_base: https://openrouter.ai/api/v1
      max_tokens: 4000
      temperature: 0.7

litellm_settings:
  drop_params: true
  set_verbose: false
  master_key: os.environ/LITELLM_MASTER_KEY  # Proxy 认证密钥
  allow_requests_on_db_unavailable: true     # 允许无数据库运行

general_settings:
  database_url: null                         # 禁用数据库
  store_model_in_db: false
  disable_spend_logs: true
```

## 常见问题

### Q1: 启动失败，提示 "No api key passed in"

**原因**: 环境变量 `LITELLM_MASTER_KEY` 未设置

**解决方案**:
```bash
# 方案1: 手动设置
export LITELLM_MASTER_KEY="sk-123"

# 方案2: 让脚本自动生成（推荐）
./start_litellm_proxy.sh  # 会自动生成并保存到 .env
```

### Q2: 请求返回 401 Unauthorized

**原因**: 客户端请求未携带正确的 Authorization header

**解决方案**:
```python
# 确保所有请求都带上 Authorization header
headers = {"Authorization": f"Bearer {master_key}"}
```

### Q3: 模型调用失败，提示 OpenRouter API 错误

**原因**: `OPENROUTER_API_KEY` 无效或未设置

**解决方案**:
1. 检查 `.env` 文件中的 `OPENROUTER_API_KEY`
2. 确认启动脚本正确导出了环境变量
3. 在 OpenRouter 控制台验证 API Key 有效性

### Q4: 如何切换模型？

在请求中指定不同的 model 名称：

```python
# Python
response = await client.post("/chat/completions", json={
    "model": "claude-sonnet",  # 或 "deepseek", "gpt-4", "qwen"
    "messages": [...]
})
```

```bash
# curl
curl -X POST http://localhost:4000/chat/completions \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{"model": "claude-sonnet", "messages": [...]}'
```

## 开发指南

### 添加新模型

1. 编辑 `config/litellm_config.yaml`
2. 在 `model_list` 中添加新模型：

```yaml
model_list:
  - model_name: my-new-model
    litellm_params:
      model: openrouter/provider/model-name
      api_key: os.environ/OPENROUTER_API_KEY
      api_base: https://openrouter.ai/api/v1
      max_tokens: 4000
      temperature: 0.7
```

3. 重启 LiteLLM Proxy

### 调试模式

启用详细日志：

```yaml
# config/litellm_config.yaml
litellm_settings:
  set_verbose: true  # 开发时打开
```

或者启动时添加 `--debug` 参数：

```bash
litellm --config ./config/litellm_config.yaml --port 4000 --debug
```

## 性能优化

### 1. 模型选择策略

- **简单任务**: 使用 `claude-haiku` 或 `deepseek` (便宜10倍+)
- **复杂任务**: 使用 `claude-sonnet` 或 `gpt-4`
- **中文内容**: 优先使用 `deepseek` 或 `qwen` (中文效果更好)
- **批量生成**: 使用 `deepseek` (性价比最高)

### 2. 并发控制

配置文件中已设置：

```yaml
router_settings:
  default_max_parallel_requests: 10  # 最大并发请求数
```

### 3. 超时设置

```yaml
router_settings:
  timeout: 120  # 单个请求超时时间(秒)
```

## 相关文档

- [OpenRouter 文档](https://openrouter.ai/docs)
- [LiteLLM 文档](https://docs.litellm.ai/)
- [项目主 README](../README.md)
- [快速启动指南](./QUICK_START.md)
