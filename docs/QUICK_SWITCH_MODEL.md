# 快速切换模型指南

## 问题说明

之前后端 API 初始化时硬编码了 DeepSeek 模型，导致即使修改了 `.env` 文件也无法切换模型。

**已修复的文件**:
- `web/backend/api/dm_api.py` - 初始化函数现在读取环境变量
- `web/backend/agents/dm_agent_langchain.py` - 默认值改为 Kimi K2

## 方法 1: 使用脚本（推荐）

我们创建了一个便捷的模型切换脚本：

```bash
# 切换到 Kimi K2 Thinking
./scripts/dev/switch_model.sh kimi

# 切换到 DeepSeek V3
./scripts/dev/switch_model.sh deepseek

# 切换到 Claude 3.5 Sonnet
./scripts/dev/switch_model.sh claude-sonnet

# 查看所有可用模型
./scripts/dev/switch_model.sh
```

**可用模型**:
- `kimi` → moonshotai/kimi-k2-thinking
- `deepseek` → deepseek/deepseek-v3.1-terminus
- `claude-sonnet` → anthropic/claude-3.5-sonnet
- `claude-haiku` → anthropic/claude-3-haiku
- `gpt-4` → openai/gpt-4-turbo
- `qwen` → qwen/qwen-2.5-72b-instruct

**脚本功能**:
- ✅ 自动备份 `.env` 文件
- ✅ 验证模型名称
- ✅ 显示当前配置
- ✅ 提示重启服务

---

## 方法 2: 手动修改（备选）

### 步骤 1: 编辑 .env 文件

```bash
# 打开 .env 文件
nano .env

# 或使用你喜欢的编辑器
code .env
```

### 步骤 2: 修改 DEFAULT_MODEL

```bash
# 修改为 Kimi K2
DEFAULT_MODEL=moonshotai/kimi-k2-thinking

# 或 DeepSeek V3
DEFAULT_MODEL=deepseek/deepseek-v3.1-terminus

# 或 Claude 3.5 Sonnet
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

### 步骤 3: 保存并重启服务

```bash
# 保存文件后重启
./scripts/start/start_all_with_agent.sh
```

---

## 验证模型切换

### 方法 1: 查看后端日志

启动后端时会显示使用的模型：

```bash
cd web/backend
uv run uvicorn main:app --reload --port 8000
```

**预期输出**:
```
✅ DM Agent 已初始化 (模型: moonshotai/kimi-k2-thinking, LangChain + Checkpoint)
```

### 方法 2: 检查 .env 文件

```bash
cat .env | grep DEFAULT_MODEL
```

**预期输出**:
```
DEFAULT_MODEL=moonshotai/kimi-k2-thinking
```

### 方法 3: 测试游戏

1. 访问 `http://localhost:3000/game/play`
2. 输入一个复杂问题（如"我想探索洞穴"）
3. 如果使用 Kimi K2，应该看到思考过程展示

---

## 常见问题

### Q1: 修改了 .env 但后端仍使用旧模型

**原因**: 后端进程未重启

**解决**:
```bash
# 停止所有服务
./scripts/start/stop_all.sh

# 重新启动
./scripts/start/start_all_with_agent.sh
```

### Q2: 如何确认模型真的切换了？

**方法 1**: 查看后端启动日志
```bash
cd web/backend
uv run uvicorn main:app --reload --log-level info
```

**方法 2**: 测试模型特性
- Kimi K2: 会显示思考过程
- DeepSeek: 响应速度快，无思考过程
- Claude: 高质量输出

### Q3: 脚本报错 "permission denied"

**原因**: 脚本没有执行权限

**解决**:
```bash
chmod +x scripts/dev/switch_model.sh
```

### Q4: 切换模型后 OpenRouter 报错

**原因**: API key 可能没有权限访问某些模型

**解决**:
1. 检查 OpenRouter 账户余额
2. 确认 API key 有访问该模型的权限
3. 查看 OpenRouter 控制台的使用限制

---

## 模型对比

| 模型 | 简写 | 速度 | 推理能力 | 中文质量 | 思考过程 | 成本 |
|------|------|------|----------|----------|----------|------|
| Kimi K2 Thinking | `kimi` | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ✅ | $$ |
| DeepSeek V3 | `deepseek` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | $ |
| Claude 3.5 Sonnet | `claude-sonnet` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | $$$ |
| Claude 3 Haiku | `claude-haiku` | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ❌ | $ |
| GPT-4 Turbo | `gpt-4` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ | $$$ |
| Qwen 2.5 | `qwen` | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | $$ |

---

## 使用建议

### 使用 Kimi K2 的场景

✅ **适合**:
- 需要理解 AI 思考过程
- 复杂推理任务
- 教育/演示场景
- 调试 AI 决策逻辑

❌ **不适合**:
- 简单问答
- 大量批量生成
- 成本敏感场景

### 使用 DeepSeek V3 的场景

✅ **适合**:
- 常规对话
- 批量章节生成
- 成本敏感场景
- 需要快速响应

❌ **不适合**:
- 需要展示思考过程
- 极高质量要求

### 使用 Claude 3.5 Sonnet 的场景

✅ **适合**:
- 高质量创作
- 复杂推理
- 英文内容生成

❌ **不适合**:
- 成本敏感场景
- 大量批量生成

---

## 完整切换流程

### 示例：切换到 Kimi K2

```bash
# 步骤 1: 停止现有服务
./scripts/start/stop_all.sh

# 步骤 2: 切换模型
./scripts/dev/switch_model.sh kimi

# 步骤 3: 验证 .env 文件
cat .env | grep DEFAULT_MODEL
# 输出: DEFAULT_MODEL=moonshotai/kimi-k2-thinking

# 步骤 4: 重启服务
./scripts/start/start_all_with_agent.sh

# 步骤 5: 查看启动日志（确认模型）
# 输出: ✅ DM Agent 已初始化 (模型: moonshotai/kimi-k2-thinking, ...)

# 步骤 6: 测试游戏
# 访问 http://localhost:3000/game/play
# 输入复杂问题，观察思考过程
```

---

## 故障排除

### 场景 1: 切换后前端无法连接

**检查清单**:
1. ✅ 后端是否成功启动？
2. ✅ 端口 8000 是否被占用？
3. ✅ .env 文件是否有语法错误？

**解决步骤**:
```bash
# 1. 检查后端进程
lsof -ti:8000

# 2. 如果有进程，杀掉它
lsof -ti:8000 | xargs kill

# 3. 重新启动
cd web/backend
uv run uvicorn main:app --reload --port 8000
```

### 场景 2: 模型切换但仍显示旧输出

**原因**: 浏览器缓存

**解决**:
1. 清除浏览器缓存 (Ctrl+Shift+R)
2. 或使用隐身模式
3. 或清除游戏状态：
   ```javascript
   localStorage.clear()
   ```

### 场景 3: OpenRouter API 错误

**检查清单**:
1. ✅ API key 是否正确？
2. ✅ 账户是否有余额？
3. ✅ 模型名称是否正确？

**验证方法**:
```bash
# 测试 OpenRouter 连接
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

---

## 高级配置

### 为不同环境使用不同模型

**开发环境** (快速迭代):
```bash
DEFAULT_MODEL=deepseek/deepseek-v3.1-terminus
```

**演示环境** (展示思考过程):
```bash
DEFAULT_MODEL=moonshotai/kimi-k2-thinking
```

**生产环境** (高质量输出):
```bash
DEFAULT_MODEL=anthropic/claude-3.5-sonnet
```

### 代码中动态切换模型

```python
# 在特定场景使用特定模型
dm_agent_thinking = DMAgentLangChain(model_name="kimi")
dm_agent_fast = DMAgentLangChain(model_name="deepseek")

# 根据任务类型选择
if task_type == "complex_reasoning":
    dm_agent = dm_agent_thinking
else:
    dm_agent = dm_agent_fast
```

---

## 相关文档

- [Kimi K2 集成指南](./features/KIMI_K2_INTEGRATION.md)
- [AI 思考过程可视化 UI](./features/AI_THINKING_UI.md)
- [模型切换脚本源码](../scripts/dev/switch_model.sh)
- [OpenRouter 配置指南](./guides/OPENROUTER_SETUP.md)

---

## 更新日志

- **2025-11-08**: 修复后端硬编码模型问题
- **2025-11-08**: 创建模型切换脚本
- **2025-11-08**: 添加快速切换指南

---

**提示**: 如果遇到任何问题，请查看 `docs/troubleshooting/TROUBLESHOOTING.md`
