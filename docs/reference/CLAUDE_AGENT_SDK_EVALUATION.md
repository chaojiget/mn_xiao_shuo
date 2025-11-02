# Claude Agent SDK 替换评估

## 📊 当前方案 vs Agent SDK

### 当前实现 (LiteLLM + DeepSeek V3)

**优势:**
- ✅ 成本极低: ~$0.001 USD/回合
- ✅ 中文优秀: DeepSeek 中文生成质量高
- ✅ 已验证: 系统运行稳定
- ✅ 灵活性: 支持多模型切换
- ✅ 简单部署: 无需额外容器

**劣势:**
- ⚠️ 非官方 SDK: 不是 Anthropic 官方方案
- ⚠️ 工具调用: 通过 JSON schema 模拟，不如原生支持
- ⚠️ 会话管理: 需自行实现上下文管理

---

### Claude Agent SDK 方案

**架构文档期望:**
```python
# 使用 Claude Agent SDK
from anthropic import Agent

agent = Agent(
    model="claude-sonnet-4",
    tools=[...],
    system_prompt="...",
    sandbox=True  # 沙盒容器
)

response = agent.execute(user_input)
```

**优势:**
- ✅ 官方支持: Anthropic 官方 SDK
- ✅ 原生工具调用: 更强大的 function calling
- ✅ 沙盒环境: 安全的代码执行
- ✅ 会话管理: 内置上下文持久化
- ✅ 文件系统: Agent 可访问文件进行上下文增强

**劣势:**
- ❌ 成本高: ~$0.01-0.02 USD/回合 (10-20倍)
- ❌ 仅限 Claude: 不支持其他模型
- ❌ 复杂部署: 需要容器环境
- ❌ 英文倾向: 中文可能不如 DeepSeek

---

## 🎯 实施建议

### 方案 A: 完全替换 (不推荐)

**步骤:**
1. 安装 `anthropic` Python SDK
2. 重写 `game_engine.py` 使用 Agent API
3. 配置沙盒容器环境
4. 迁移所有工具定义

**问题:**
- 成本激增 10-20 倍
- 失去模型选择灵活性
- 中文生成质量可能下降

### 方案 B: 抽象层 + 可选后端 (推荐) ✅

**架构:**
```
GameEngine
    ↓
LLMBackend (抽象接口)
    ↙        ↘
LiteLLM   ClaudeAgent
Backend   Backend
```

**优势:**
- 保留当前低成本方案
- 支持按需切换
- 向后兼容
- 用户可根据需求选择

**实现:**
```python
# 抽象基类
class LLMBackend(ABC):
    @abstractmethod
    async def generate(self, prompt, tools, **kwargs):
        pass

# LiteLLM 后端
class LiteLLMBackend(LLMBackend):
    async def generate(self, prompt, tools, **kwargs):
        # 当前实现
        pass

# Claude Agent 后端
class ClaudeAgentBackend(LLMBackend):
    async def generate(self, prompt, tools, **kwargs):
        # 使用 Anthropic SDK
        pass
```

### 方案 C: 混合模式 (高级)

**场景划分:**
- 简单叙事: DeepSeek (便宜快速)
- 复杂决策: Claude Sonnet (高质量)
- 紧急情况: Claude Haiku (快速响应)

---

## 💡 实际可行性分析

### 技术可行性: ⭐⭐⭐⭐ (可行)

Claude Agent SDK 本质上是：
```bash
# 安装
npm install -g @anthropic-ai/claude-code

# 或 Python SDK
pip install anthropic
```

**Python SDK 示例:**
```python
from anthropic import Anthropic

client = Anthropic(api_key="...")

response = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    tools=[{
        "name": "get_player_state",
        "description": "获取玩家状态",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }],
    messages=[{
        "role": "user",
        "content": "玩家向北走"
    }]
)
```

### 经济可行性: ⭐⭐ (成本高)

**成本对比:**

| 模型 | 输入 | 输出 | 每回合成本 |
|------|------|------|-----------|
| DeepSeek V3 | $0.27/M | $1.10/M | ~$0.001 |
| Claude Sonnet 4.5 | $3/M | $15/M | ~$0.015 |
| Claude Haiku | $0.25/M | $1.25/M | ~$0.002 |

**日常使用:**
- 100 回合 DeepSeek: $0.10
- 100 回合 Claude: $1.50

**月成本(平均每天 50 回合):**
- DeepSeek: $1.50/月
- Claude: $22.50/月

### 实用性评估: ⭐⭐⭐ (中等)

**适合场景:**
1. 需要高质量英文叙事
2. 复杂的推理和决策
3. 对成本不敏感的项目
4. 需要官方支持和SLA

**不适合场景:**
1. 中文为主的游戏 (DeepSeek 更优)
2. 成本敏感项目
3. 高频交互场景
4. 个人/学习项目

---

## 🚀 推荐实施方案

### Phase 1: 抽象层重构 (2-3天)

创建 LLM 后端抽象层:

```python
# web/backend/llm/base.py
from abc import ABC, abstractmethod
from typing import Dict, List, Any

class LLMBackend(ABC):
    """LLM 后端抽象基类"""

    @abstractmethod
    async def generate_structured(
        self,
        prompt: str,
        schema: Dict[str, Any],
        tools: List[Dict],
        **kwargs
    ) -> Dict[str, Any]:
        """生成结构化输出"""
        pass

# web/backend/llm/litellm_backend.py
from llm.base import LLMBackend

class LiteLLMBackend(LLMBackend):
    """当前实现"""
    async def generate_structured(self, ...):
        # 使用 LiteLLM
        pass

# web/backend/llm/claude_backend.py
from llm.base import LLMBackend
from anthropic import Anthropic

class ClaudeBackend(LLMBackend):
    """Claude Agent SDK 实现"""
    async def generate_structured(self, ...):
        # 使用 Anthropic SDK
        pass
```

### Phase 2: 配置化选择 (1天)

```yaml
# config/llm_backend.yaml
backend: "litellm"  # 或 "claude"

litellm:
  model: "deepseek"
  config_path: "./config/litellm_config.yaml"

claude:
  model: "claude-sonnet-4"
  api_key: ${ANTHROPIC_API_KEY}
  max_tokens: 4000
```

### Phase 3: 可选升级 Claude (2-3天)

用户可根据需要启用:

```python
# .env
LLM_BACKEND=claude  # 或 litellm
ANTHROPIC_API_KEY=sk-ant-...
```

---

## 📋 实施检查清单

### 准备工作
- [ ] 评估项目预算(Claude 贵 10-20 倍)
- [ ] 测试 Anthropic SDK
- [ ] 设计抽象层接口
- [ ] 准备 API Key

### 开发任务
- [ ] 创建 `llm/base.py` 抽象类
- [ ] 重构 `LiteLLMBackend`
- [ ] 实现 `ClaudeBackend`
- [ ] 配置文件支持
- [ ] 环境变量切换

### 测试验证
- [ ] 单元测试两种后端
- [ ] 集成测试游戏流程
- [ ] 性能对比
- [ ] 成本核算

---

## 🎯 最终建议

### 短期 (当前阶段)
**保持 LiteLLM + DeepSeek V3** ✅

**理由:**
1. 成本优势明显
2. 中文质量优秀
3. 系统稳定运行
4. 灵活性强

### 中期 (功能完善后)
**实现抽象层，支持可选 Claude** ⚡

**理由:**
1. 架构更清晰
2. 用户可选择
3. 便于未来扩展
4. 满足不同场景需求

### 长期 (生产环境)
**混合模式：智能路由** 🚀

**策略:**
```python
if task.complexity < 5:
    use DeepSeek  # 简单叙事
elif task.requires_english:
    use Claude Sonnet  # 英文内容
elif task.urgent:
    use Claude Haiku  # 快速响应
else:
    use DeepSeek  # 默认
```

---

## ❓ 决策问题

### 需要用户回答:

1. **预算考虑**: 能否接受 10-20 倍的成本增加?
2. **内容语言**: 游戏主要是中文还是英文?
3. **质量要求**: 对叙事质量的要求有多高?
4. **紧急程度**: 是否必须立即切换到 Claude?

### 建议:

如果：
- ✅ 中文为主 → 保持 DeepSeek
- ✅ 成本敏感 → 保持 DeepSeek
- ✅ 个人项目 → 保持 DeepSeek

除非：
- ❌ 必须英文叙事
- ❌ 需要官方支持
- ❌ 预算充足

---

**结论**: 建议现阶段**不进行完全替换**，而是实现**抽象层支持可选后端**，让用户根据实际需求选择。

**估计工作量**: 3-5 天 (实现抽象层 + Claude 后端)

**优先级建议**: P2 → P1 (如果实现抽象层的话)

---

**最后更新**: 2025-11-01
**文档版本**: 1.0
