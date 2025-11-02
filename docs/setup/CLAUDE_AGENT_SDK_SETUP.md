# Claude Agent SDK 集成指南

本文档说明如何配置 **Claude Agent SDK** 使用 LiteLLM Proxy，从而替换默认的 Anthropic API 服务，改用更经济的模型（如 DeepSeek）。

## 核心原理

Claude Agent SDK 支持通过环境变量配置自定义的 API 端点：

```bash
ANTHROPIC_BASE_URL     # API 基础 URL（默认：https://api.anthropic.com）
ANTHROPIC_AUTH_TOKEN   # 认证 Token
ANTHROPIC_MODEL        # 模型名称
```

通过将 `ANTHROPIC_BASE_URL` 指向 LiteLLM Proxy，我们可以：
- ✅ 使用 DeepSeek/Qwen 等经济模型（成本降低 10 倍以上）
- ✅ 保持 Claude Agent SDK 的完整功能
- ✅ 无需修改代码

## 快速配置

### 方式1: 自动配置（推荐）

运行启动脚本会自动设置所有环境变量：

```bash
./start_litellm_proxy.sh
```

脚本会：
1. 生成或读取 `LITELLM_MASTER_KEY`
2. 自动导出 Claude Agent SDK 环境变量
3. 启动 LiteLLM Proxy

### 方式2: 手动配置

#### 1. 确保 LiteLLM Proxy 运行

```bash
./start_litellm_proxy.sh
```

#### 2. 设置环境变量

在你的终端或脚本中：

```bash
# 读取 Master Key
export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)

# 配置 Claude Agent SDK
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

#### 3. 运行你的 Claude Agent SDK 代码

现在 Claude Agent SDK 会自动使用 LiteLLM Proxy 和 DeepSeek 模型！

## 环境变量详解

### ANTHROPIC_BASE_URL

**作用**: 指定 API 服务器地址

**默认值**: `https://api.anthropic.com`

**配置为 LiteLLM Proxy**:
```bash
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
```

**说明**:
- 使用 `0.0.0.0` 允许本地和容器内访问
- 使用 `localhost` 仅限本地访问
- 端口 `4000` 是 LiteLLM Proxy 的默认端口

### ANTHROPIC_AUTH_TOKEN

**作用**: API 认证令牌

**默认值**: 无（需要真实的 Anthropic API Key）

**配置为 LiteLLM Master Key**:
```bash
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
```

**说明**:
- LiteLLM Proxy 使用 `LITELLM_MASTER_KEY` 进行认证
- 这个 Key 由启动脚本自动生成并保存到 `.env`
- 格式: `sk-litellm-xxxxxxxxxxxxxxxx`

### ANTHROPIC_MODEL

**作用**: 指定使用的模型

**默认值**: Claude 模型名称

**配置为 OpenRouter 模型**:
```bash
# DeepSeek（推荐，性价比最高）
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324

# 或其他模型
export ANTHROPIC_MODEL=openrouter/anthropic/claude-sonnet-4.5
export ANTHROPIC_MODEL=openrouter/qwen/qwen-2.5-72b-instruct
```

**说明**:
- 必须使用 `openrouter/` 前缀
- 完整格式: `openrouter/<provider>/<model-name>`
- 可用模型见 [OpenRouter 文档](https://openrouter.ai/docs)

## 模型选择建议

### 推荐组合

| 场景 | 模型 | 成本 | 说明 |
|------|------|------|------|
| **默认推荐** | `openrouter/deepseek/deepseek-chat-v3-0324` | 💰 极低 | 中文友好，性价比最高 |
| 简单任务 | `openrouter/qwen/qwen-2.5-72b-instruct` | 💰 低 | 中文优化，快速响应 |
| 高质量输出 | `openrouter/anthropic/claude-sonnet-4.5` | 💰💰💰 高 | 原生 Claude 模型 |
| 快速原型 | `openrouter/anthropic/claude-3.5-haiku` | 💰💰 中 | Claude 快速模型 |

### 成本对比

以 1M tokens 为例：

- DeepSeek V3: ~$0.14 (输入) + $0.28 (输出)
- Qwen 2.5 72B: ~$0.35 (输入) + $0.40 (输出)
- Claude Sonnet 4.5: ~$3.00 (输入) + $15.00 (输出)

💡 **使用 DeepSeek 可以节省 90% 以上成本！**

## 验证配置

### 检查环境变量

```bash
echo "ANTHROPIC_BASE_URL=$ANTHROPIC_BASE_URL"
echo "ANTHROPIC_AUTH_TOKEN=$ANTHROPIC_AUTH_TOKEN"
echo "ANTHROPIC_MODEL=$ANTHROPIC_MODEL"
```

预期输出：
```
ANTHROPIC_BASE_URL=http://0.0.0.0:4000
ANTHROPIC_AUTH_TOKEN=sk-litellm-xxxxxxxxxxxxxxxx
ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

### 测试连接

```bash
curl -X POST $ANTHROPIC_BASE_URL/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ANTHROPIC_AUTH_TOKEN" \
  -d "{
    \"model\": \"deepseek\",
    \"messages\": [{\"role\": \"user\", \"content\": \"你好\"}]
  }"
```

### 使用 Claude Agent SDK

创建测试文件 `test_claude_sdk.py`:

```python
import os
from anthropic import Anthropic

# 环境变量已自动设置，直接使用
client = Anthropic()

# 这会通过 LiteLLM Proxy 调用 DeepSeek 模型
message = client.messages.create(
    model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
    max_tokens=1024,
    messages=[
        {"role": "user", "content": "你好，请用一句话介绍一下你自己"}
    ]
)

print(message.content[0].text)
```

运行：
```bash
python test_claude_sdk.py
```

## 在不同场景中使用

### Shell 脚本

```bash
#!/bin/bash

# 加载环境变量
source .env

# 设置 Claude Agent SDK
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324

# 运行你的程序
python your_script.py
```

### Docker Compose

```yaml
services:
  app:
    environment:
      - ANTHROPIC_BASE_URL=http://litellm-proxy:4000
      - ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}
      - ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
    depends_on:
      - litellm-proxy

  litellm-proxy:
    image: ghcr.io/berriai/litellm:latest
    ports:
      - "4000:4000"
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - LITELLM_MASTER_KEY=${LITELLM_MASTER_KEY}
    volumes:
      - ./config/litellm_config.yaml:/app/config.yaml
```

### systemd 服务

```ini
# /etc/systemd/system/litellm-proxy.service
[Unit]
Description=LiteLLM Proxy
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/project
Environment="OPENROUTER_API_KEY=sk-or-v1-xxxxx"
Environment="LITELLM_MASTER_KEY=sk-litellm-xxxxx"
Environment="ANTHROPIC_BASE_URL=http://0.0.0.0:4000"
Environment="ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}"
Environment="ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324"
ExecStart=/path/to/start_litellm_proxy.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

## 切换模型

### 临时切换（单次运行）

```bash
# 使用 Claude Sonnet
export ANTHROPIC_MODEL=openrouter/anthropic/claude-sonnet-4.5
python your_script.py

# 使用 Qwen
export ANTHROPIC_MODEL=openrouter/qwen/qwen-2.5-72b-instruct
python your_script.py
```

### 永久切换

编辑 `.env` 文件：

```bash
# DeepSeek（默认）
ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324

# 或改为 Claude
ANTHROPIC_MODEL=openrouter/anthropic/claude-sonnet-4.5
```

重启 LiteLLM Proxy：

```bash
pkill -f litellm
./start_litellm_proxy.sh
```

## 故障排查

### 问题1: Claude Agent SDK 仍然使用 Anthropic API

**症状**: 收到 Anthropic API Key 错误

**原因**: 环境变量未正确设置

**解决方案**:
```bash
# 确认环境变量
env | grep ANTHROPIC

# 如果为空，重新导出
source .env
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

### 问题2: 连接被拒绝

**症状**: `Connection refused` 或 `Connection error`

**原因**: LiteLLM Proxy 未运行

**解决方案**:
```bash
# 检查 Proxy 状态
curl http://localhost:4000/health

# 如果失败，启动 Proxy
./start_litellm_proxy.sh
```

### 问题3: 认证失败

**症状**: 401 Unauthorized

**原因**: `ANTHROPIC_AUTH_TOKEN` 与 `LITELLM_MASTER_KEY` 不匹配

**解决方案**:
```bash
# 确保一致
export ANTHROPIC_AUTH_TOKEN=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)
```

### 问题4: 模型不可用

**症状**: 模型名称错误或不支持

**原因**: 模型名称格式不正确

**解决方案**:
```bash
# 错误示例
export ANTHROPIC_MODEL=deepseek  # ❌ 缺少 openrouter/ 前缀

# 正确示例
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324  # ✅
```

## 最佳实践

### 1. 使用 .env 文件管理

```bash
# .env
OPENROUTER_API_KEY=sk-or-v1-xxxxx
LITELLM_MASTER_KEY=sk-litellm-xxxxx
ANTHROPIC_BASE_URL=http://0.0.0.0:4000
ANTHROPIC_AUTH_TOKEN=${LITELLM_MASTER_KEY}
ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

在脚本开头：
```bash
source .env
```

### 2. 健康检查

在启动应用前检查 Proxy 是否运行：

```bash
if ! curl -s http://localhost:4000/health > /dev/null; then
    echo "❌ LiteLLM Proxy 未运行，正在启动..."
    ./start_litellm_proxy.sh &
    sleep 5
fi
```

### 3. 日志记录

保留请求日志用于调试：

```bash
# 启用详细日志
litellm --config ./config/litellm_config.yaml --port 4000 --debug > litellm.log 2>&1
```

## 参考资源

- [LiteLLM Proxy 设置指南](./LITELLM_PROXY_SETUP.md)
- [OpenRouter 文档](https://openrouter.ai/docs)
- [Claude Agent SDK 文档](https://docs.anthropic.com/claude/docs)
- [环境变量配置说明](https://github.com/anthropics/anthropic-sdk-python#custom-base-url)

## 总结

通过配置这三个环境变量：

```bash
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

你可以：
- ✅ 让 Claude Agent SDK 使用 LiteLLM Proxy
- ✅ 替换为更经济的模型（如 DeepSeek）
- ✅ 节省 90% 以上的 API 成本
- ✅ 保持代码完全不变

**启动脚本已自动配置这些环境变量，直接运行即可！**
