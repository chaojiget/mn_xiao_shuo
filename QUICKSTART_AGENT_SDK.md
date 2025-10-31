# 🚀 快速启动 - Agent SDK + DeepSeek 模式

## 一条命令启动完整系统

```bash
./start_all_with_agent.sh
```

这会自动启动：
- ✅ LiteLLM Proxy (端口 4000) - 路由到 DeepSeek
- ✅ FastAPI Backend (端口 8000)
- ✅ Next.js Frontend (端口 3000)

## 前提条件

### 1. 设置环境变量

编辑 `.env` 文件：

```bash
# 必需
OPENROUTER_API_KEY=your_openrouter_key_here

# Agent SDK 配置
USE_LITELLM_PROXY=true
ANTHROPIC_API_BASE=http://localhost:4000
ANTHROPIC_API_KEY=sk-proxy-key
```

加载环境变量：

```bash
source .env
```

### 2. 安装依赖

```bash
# 激活虚拟环境
source .venv/bin/activate

# 安装 Agent SDK
pip install claude-agent-sdk

# 安装 LiteLLM Proxy
pip install 'litellm[proxy]'
```

## 使用方法

### 启动系统

```bash
./start_all_with_agent.sh
```

### 访问界面

打开浏览器访问: http://localhost:3000/chat

### 测试流程

1. **输入标题**: "星际迷航"
2. **选择类型**: 🚀 科幻
3. **点击**: "✨ 一键生成完整设定"
4. **等待**: 10-30 秒（AI 正在创作）
5. **查看结果**:
   - 👤 主角信息
   - 🌍 世界观设定
   - 🎭 NPC 列表
6. **开始创作**: 点击按钮进入跑团模式

### 停止系统

```bash
./stop_all.sh
```

或按 `Ctrl+C` (在启动脚本的终端窗口)

## 工作原理

```
你的请求
    ↓
Claude Agent SDK
    ↓
LiteLLM Proxy (localhost:4000)
    ↓
OpenRouter API
    ↓
DeepSeek V3 模型
    ↓
返回结果
```

## 验证配置

### 检查 Proxy 是否运行

```bash
curl http://localhost:4000/health

# 期望输出: {"status": "healthy"}
```

### 测试 DeepSeek 路由

```bash
curl http://localhost:4000/v1/messages \
  -H "Content-Type: application/json" \
  -H "x-api-key: test" \
  -H "anthropic-version: 2023-06-01" \
  -d '{
    "model": "claude-3-5-sonnet-20241022",
    "max_tokens": 100,
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

### 查看日志

```bash
# LiteLLM Proxy 日志
tail -f logs/litellm_proxy.log

# 后端日志
tail -f logs/backend.log

# 前端日志
tail -f logs/frontend.log
```

## 常见问题

### Q: 端口被占用

```
Error: Address already in use: 4000
```

**解决**: 停止占用端口的程序

```bash
lsof -ti:4000 | xargs kill -9
lsof -ti:8000 | xargs kill -9
lsof -ti:3000 | xargs kill -9
```

### Q: OPENROUTER_API_KEY 未设置

**解决**:

```bash
export OPENROUTER_API_KEY=your-key
# 或
source .env
```

### Q: Agent SDK 未安装

**解决**:

```bash
pip install claude-agent-sdk
```

### Q: 生成失败

**检查**:
1. LiteLLM Proxy 是否正常运行
2. 查看 `logs/litellm_proxy.log` 日志
3. 确认 OPENROUTER_API_KEY 有效

## 成本对比

使用 DeepSeek 而非 Claude 可节省 **90-95%** 的成本：

| 操作 | Claude Sonnet 3.5 | DeepSeek V3 | 节省 |
|------|-------------------|-------------|------|
| 生成 1 个设定 (约 2000 tokens) | $0.03 | $0.0003 | 99% |
| 100 次生成 | $3.00 | $0.03 | 99% |
| 1000 次对话 | $30.00 | $0.30 | 99% |

## 下一步

✅ **阶段 1 完成** - 自动生成系统
🚀 **阶段 2** - 多 Agent 跑团系统（进行中）

准备好开始多 Agent 交互了吗？

## 相关文档

- [完整配置指南](docs/guides/AGENT_SDK_WITH_DEEPSEEK.md)
- [阶段 1 实现总结](web/PHASE1_IMPLEMENTATION.md)
- [流式输出实现](web/STREAMING_IMPLEMENTATION.md)

## 技术支持

遇到问题？检查：
1. 环境变量是否正确设置
2. 所有服务是否正常运行
3. 日志文件中的错误信息
4. API Key 是否有效

**祝你使用愉快！** 🎉
