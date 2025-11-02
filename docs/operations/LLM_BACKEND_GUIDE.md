# LLM 后端切换指南

## 📖 概述

系统现在支持灵活切换不同的 LLM 后端，无需修改代码即可更换模型提供商。

**支持的后端:**
- ✅ **LiteLLM** - 支持多种模型（DeepSeek, Claude, GPT等）
- ✅ **Claude Agent SDK** - Anthropic 官方实现（可选）

---

## 🎯 快速开始

### 方法 1: 默认配置（推荐）

保持默认配置，使用 LiteLLM + DeepSeek V3:

```yaml
# config/llm_backend.yaml
backend: "litellm"
```

**优势:**
- ✅ 成本低 (~$0.001/回合)
- ✅ 中文优秀
- ✅ 无需额外配置

### 方法 2: 切换到 Claude

```bash
# 1. 安装 Anthropic SDK
uv pip install anthropic

# 2. 设置 API Key
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# 3. 修改配置
# 编辑 config/llm_backend.yaml
backend: "claude"
```

**注意:**
- ⚠️ 成本高 (~$0.015/回合，10-20倍)
- ✅ 质量最高（特别是英文）

---

## 📁 文件结构

```
web/backend/llm/
├── __init__.py           # 模块入口，工厂函数
├── base.py               # 抽象基类
├── litellm_backend.py    # LiteLLM 实现
├── claude_backend.py     # Claude 实现（可选）
└── config_loader.py      # 配置加载器

config/
├── llm_backend.yaml      # 后端配置
└── litellm_config.yaml   # LiteLLM 模型配置
```

---

## ⚙️ 配置文件详解

### config/llm_backend.yaml

```yaml
# 选择后端类型
backend: "litellm"  # 或 "claude"

# LiteLLM 配置
litellm:
  config_path: "./config/litellm_config.yaml"
  model: "deepseek"  # deepseek, claude-sonnet, gpt-4, qwen等
  temperature: 0.7
  max_tokens: 1000

# Claude 配置
claude:
  api_key: ${ANTHROPIC_API_KEY}
  model: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 4096
```

---

## 🔧 使用方法

### Python 代码中使用

```python
from llm import create_backend, get_available_backends

# 方法1: 使用工厂函数（推荐）
backend = create_backend("litellm")

# 方法2: 直接实例化
from llm import LiteLLMBackend
backend = LiteLLMBackend(config={"model": "deepseek"})

# 方法3: 使用配置加载器
from llm.config_loader import LLMConfigLoader

loader = LLMConfigLoader()
backend_type = loader.get_backend_type()
backend_config = loader.get_backend_config()
backend = create_backend(backend_type, backend_config)
```

### 检查可用后端

```python
from llm import get_available_backends

backends = get_available_backends()
print(backends)

# 输出:
# {
#   "litellm": {
#     "available": True,
#     "description": "LiteLLM - 支持多种模型",
#     "cost": "低",
#     "models": ["deepseek", "claude-sonnet", ...]
#   },
#   "claude": {
#     "available": False,  # 如果未安装 anthropic
#     "description": "Claude Agent SDK",
#     "cost": "高",
#     "requires": "anthropic"
#   }
# }
```

---

## 📊 性能对比

### 成本对比

| 后端 | 模型 | 成本/回合 | 月成本(50回合/天) |
|------|------|-----------|-------------------|
| LiteLLM | DeepSeek V3 | $0.001 | $1.50 |
| LiteLLM | Qwen 2.5 | $0.002 | $3.00 |
| LiteLLM | Claude Haiku | $0.002 | $3.00 |
| Claude SDK | Claude Sonnet | $0.015 | $22.50 |
| LiteLLM | GPT-4 | $0.020 | $30.00 |

### 质量对比

| 指标 | DeepSeek V3 | Claude Sonnet 4 |
|------|-------------|-----------------|
| 中文叙事 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 英文叙事 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 工具调用 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 推理能力 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 响应速度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 成本效益 | ⭐⭐⭐⭐⭐ | ⭐⭐ |

---

## 🎮 使用场景建议

### 场景 1: 中文文字冒险游戏（当前项目）

**推荐:** LiteLLM + DeepSeek V3 ✅

**理由:**
- 中文生成质量优秀
- 成本极低，可持续运行
- 支持工具调用
- 响应速度快

**配置:**
```yaml
backend: "litellm"
litellm:
  model: "deepseek"
```

### 场景 2: 英文 RPG 游戏

**推荐:** Claude Agent SDK + Sonnet 4

**理由:**
- 英文叙事质量最高
- 复杂推理能力强
- 官方支持

**配置:**
```yaml
backend: "claude"
claude:
  model: "claude-sonnet-4-20250514"
```

### 场景 3: 多语言支持

**推荐:** LiteLLM（可切换模型）

**理由:**
- 支持多个模型
- 可根据语言动态切换
- 成本可控

**配置:**
```yaml
backend: "litellm"
litellm:
  model: "deepseek"  # 中文
  # 或 "claude-sonnet"  # 英文
  # 或 "qwen"  # 中文优化
```

### 场景 4: 原型开发/测试

**推荐:** LiteLLM + DeepSeek/Haiku

**理由:**
- 开发成本低
- 快速迭代
- 足够的质量

---

## 🚀 高级用法

### 动态切换后端

```python
class GameEngine:
    def __init__(self):
        # 根据配置加载后端
        loader = LLMConfigLoader()
        backend_type = loader.get_backend_type()
        backend_config = loader.get_backend_config()

        self.backend = create_backend(backend_type, backend_config)

        # 打印后端信息
        info = self.backend.get_backend_info()
        print(f"使用后端: {info['backend']}")
        print(f"模型: {info['model']}")

    async def process_turn(self, ...):
        # 使用统一接口
        response = await self.backend.generate(...)
        return response
```

### 混合模式（未来）

```python
# 根据任务复杂度选择模型
if task.complexity < 5:
    backend = create_backend("litellm", {"model": "deepseek"})
elif task.requires_english:
    backend = create_backend("claude")
else:
    backend = create_backend("litellm", {"model": "qwen"})
```

---

## ❓ 常见问题

### Q: 如何切换回 LiteLLM?

A: 编辑 `config/llm_backend.yaml`:
```yaml
backend: "litellm"
```

### Q: Claude 后端需要什么?

A:
1. 安装: `uv pip install anthropic`
2. 设置环境变量: `ANTHROPIC_API_KEY=sk-ant-...`
3. 修改配置: `backend: "claude"`

### Q: 可以同时使用两个后端吗?

A: 当前版本只支持一个后端，但可以通过配置轻松切换。
未来可能支持混合模式。

### Q: 哪个后端更好?

A: 取决于需求:
- 成本敏感 → LiteLLM + DeepSeek
- 中文内容 → LiteLLM + DeepSeek/Qwen
- 英文内容 → Claude Agent SDK
- 最高质量 → Claude Agent SDK（但贵）

### Q: 如何查看当前使用的后端?

A:
```python
info = backend.get_backend_info()
print(info)
```

---

## 🔍 故障排除

### 问题: Claude 后端导入失败

```
ImportError: Claude 后端需要安装 anthropic 包
```

**解决:**
```bash
uv pip install anthropic
```

### 问题: ANTHROPIC_API_KEY 未设置

```
ValueError: 未设置 ANTHROPIC_API_KEY
```

**解决:**
```bash
# 添加到 .env 文件
echo "ANTHROPIC_API_KEY=sk-ant-..." >> .env

# 或临时设置
export ANTHROPIC_API_KEY=sk-ant-...
```

### 问题: 配置文件不存在

```
[WARNING] 配置文件不存在: config/llm_backend.yaml
[INFO] 使用默认配置: LiteLLM + DeepSeek
```

**解决:**
```bash
# 复制示例配置
cp config/llm_backend.yaml.example config/llm_backend.yaml
```

---

## 📋 检查清单

切换后端前检查:

- [ ] 确认新后端已安装所需依赖
- [ ] 设置必要的环境变量
- [ ] 修改配置文件
- [ ] 测试后端是否可用
- [ ] 评估成本影响
- [ ] 备份当前配置

---

## 📚 相关文档

- [Claude Agent SDK 评估](./CLAUDE_AGENT_SDK_EVALUATION.md)
- [LiteLLM 配置](../config/litellm_config.yaml)
- [架构设计](./architecture/ARCHITECTURE.md)

---

**最后更新**: 2025-11-01
**版本**: v1.0
