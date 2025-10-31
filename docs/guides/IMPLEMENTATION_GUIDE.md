# 实施指南 - 长篇小说生成系统

## 项目概述

基于你提供的全局导演(GD)工作流设计,本系统整合了:
- **MCP (Model Context Protocol)**: 管理长期记忆、证据库、世界状态
- **Claude Agent SDK**: 执行复杂的多步骤任务(章节生成、场景细化等)
- **LiteLLM**: 统一多个 LLM 提供商,实现模型路由和负载均衡

## 已完成工作

### ✅ 1. 架构设计
- 详细架构文档: `ARCHITECTURE.md`
- 系统总览、技术栈选型、核心模块设计
- 开发路线图(分4个阶段)

### ✅ 2. 项目结构
```
mn_xiao_shuo/
├── src/
│   ├── models/           # ✅ 数据模型(已完成)
│   │   ├── world_state.py
│   │   ├── event_node.py
│   │   ├── action_queue.py
│   │   └── clue.py
│   ├── llm/              # ✅ LiteLLM 客户端(已完成)
│   │   └── litellm_client.py
│   ├── director/         # 🚧 待实现
│   ├── mcp_server/       # 🚧 待实现
│   └── utils/            # 🚧 待实现
├── config/               # ✅ 配置文件(已完成)
│   ├── litellm_config.yaml
│   └── novel_types.yaml
├── examples/             # ✅ 示例设定(已完成)
│   ├── scifi_setting.json
│   └── xianxia_setting.json
├── requirements.txt      # ✅
├── .env.example          # ✅
└── README.md             # ✅
```

### ✅ 3. 数据模型
核心数据结构已完整定义:
- `WorldState`: 世界状态管理
- `EventNode` & `EventArc`: 事件系统
- `ActionQueue`: 动作队列
- `Clue`, `Setup`, `Evidence`: 线索经济

### ✅ 4. LiteLLM 集成
- 完整的 `LiteLLMClient` 实现
- 支持:
  - 基础文本生成
  - 结构化输出(JSON Schema)
  - 函数调用
  - 批量生成

### ✅ 5. 配置文件
- **LiteLLM 配置**: 模型路由、降级策略、重试逻辑
- **小说类型配置**: 科幻/玄幻的评分权重和节奏参数
- **示例设定**: 科幻《能源纪元》、玄幻《逆天改命录》

---

## 下一步实施计划

### 🎯 Phase 1: MVP 核心功能(2-3周)

#### 第1周: 核心引擎

**1. 实现全局导演(Global Director)**
文件: `src/director/gd.py`

关键功能:
```python
class GlobalDirector:
    async def run_scene_loop(self):
        """场景循环主逻辑"""
        while not self.is_story_complete():
            # 1. 评分选择事件
            next_event = await self.score_and_select_event()
            # 2. 生成动作队列
            action_queue = await self.generate_action_queue(next_event)
            # 3. 执行动作
            result = await self.execute_actions(action_queue)
            # 4. 一致性审计
            is_valid = await self.consistency_audit(result)
            # 5. 更新状态
            await self.apply_state_patch(result)
            # 6. 管理线索与伏笔
            await self.update_clue_economy(result)
            yield result

    def _score_playability(self, event) -> float:
        """可玩性评分"""
        pass

    def _score_narrative(self, event) -> float:
        """叙事评分"""
        pass

    def _score_hybrid(self, event) -> float:
        """混合评分(动态权重)"""
        pass
```

**2. 实现评分系统**
文件: `src/director/scoring.py`

- 实现可玩性评分函数
- 实现叙事评分函数
- 实现混合评分(动态调整权重)

**3. 实现一致性审计**
文件: `src/director/consistency.py`

```python
class ConsistencyAuditor:
    def check_hard_rules(self, result, world_state) -> bool:
        """检查硬规则"""
        pass

    def check_causality(self, result, world_state) -> bool:
        """检查因果链"""
        pass

    def check_resource_conservation(self, result, world_state) -> bool:
        """检查资源守恒"""
        pass
```

#### 第2周: 状态管理与数据库

**4. 数据库层实现**
文件: `src/utils/database.py`

- SQLite 初始化脚本
- 状态持久化
- 事件历史查询

```bash
# 初始化数据库
python scripts/init_db.py
```

**5. 设定解析器**
文件: `src/utils/setting_parser.py`

```python
def parse_setting_json(setting_path: str) -> Tuple[WorldState, List[EventArc]]:
    """解析设定JSON,生成初始世界状态和事件线"""
    pass
```

#### 第3周: CLI 与测试

**6. CLI 入口程序**
文件: `src/cli.py`

```python
import asyncio
from director.gd import GlobalDirector, NovelType, Preference

async def main():
    # 加载设定
    setting = load_setting("examples/scifi_setting.json")

    # 创建导演
    director = GlobalDirector(
        setting=setting,
        novel_type=NovelType.SCIFI,
        preference=Preference.HYBRID
    )

    # 生成章节
    async for scene in director.run_scene_loop():
        print(f"\n{'='*60}\n")
        print(scene["content"])

        # 用户交互
        user_input = input("\n> ")
        if user_input == "quit":
            break

if __name__ == "__main__":
    asyncio.run(main())
```

**7. 基础测试**
- 单元测试(pytest)
- 集成测试(端到端场景生成)

```bash
# 运行测试
pytest tests/ -v
```

---

### 🚀 Phase 2: 增强功能(2-3周)

#### 第4-5周: MCP 集成

**8. 实现 MCP Server**
文件: `src/mcp_server/novel_world_server.py`

```python
from mcp import Server

class NovelWorldServer:
    def __init__(self):
        self.server = Server("novel-world-server")
        self._register_resources()
        self._register_tools()

    def _register_resources(self):
        @self.server.resource("world://state/{location}")
        async def get_location_state(location: str):
            return world_state.locations.get(location)

    def _register_tools(self):
        @self.server.tool("query-evidence")
        async def query_evidence(query: str):
            # 向量搜索证据库
            return chromadb.query(query)
```

**9. 向量数据库集成**
文件: `src/utils/vector_db.py`

- ChromaDB 初始化
- 证据向量化存储
- 语义搜索

#### 第6周: Claude Agent SDK

**10. Agent 执行器**
文件: `src/director/agent_executor.py`

```python
from anthropic_agents import Agent, Task

class AgentExecutor:
    async def run(self, action_queue: ActionQueue) -> Dict:
        """执行动作队列"""
        context = await self._prepare_context(action_queue)

        task = Task(
            description=f"执行事件 {action_queue.event_id}",
            context=context,
            steps=action_queue.steps
        )

        result = await self.agent.execute(task)
        return self._parse_result(result)
```

**关键点**: Claude Agent SDK 的安装

```bash
# Claude Agent SDK 目前可能需要从 GitHub 安装
pip install git+https://github.com/anthropics/anthropic-agents.git
```

> **注意**: 如果 Claude Agent SDK 尚未公开发布,可以先用简单的提示词工程实现类似功能,后续再迁移。

---

### ⚡ Phase 3: 优化(2周)

**11. 异步任务调度**
- 并发执行独立事件
- 任务队列管理

**12. 缓存机制**
- Redis 缓存LLM响应
- 向量检索结果缓存

**13. PostgreSQL 迁移**
- 生产环境数据库
- Alembic 数据库迁移

---

### 🎨 Phase 4: 产品化(3周)

**14. Web API**
文件: `src/api.py`

```python
from fastapi import FastAPI, WebSocket

app = FastAPI()

@app.websocket("/ws/generate")
async def websocket_generate(websocket: WebSocket):
    await websocket.accept()
    # 实时流式生成章节
    async for scene in director.run_scene_loop():
        await websocket.send_json(scene)
```

**15. 导出功能**
- Markdown 导出
- EPUB 生成

**16. 部署**
- Docker 容器化
- 部署脚本

---

## 快速开始(现在就能做的)

### 1. 环境配置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env,填入你的 ANTHROPIC_API_KEY
```

### 2. 测试 LiteLLM 客户端

创建测试脚本 `test_litellm.py`:

```python
import asyncio
from src.llm.litellm_client import LiteLLMClient

async def test():
    client = LiteLLMClient()

    # 测试基础生成
    result = await client.generate(
        prompt="写一段科幻小说的开头,主题是能源危机。",
        model="claude-sonnet"
    )

    print(result)

if __name__ == "__main__":
    asyncio.run(test())
```

运行:
```bash
python test_litellm.py
```

### 3. 测试数据模型

```python
from src.models import WorldState, Character, EventNode

# 创建世界状态
world = WorldState(timestamp=0, turn=0)

# 添加主角
protagonist = Character(
    id="CHAR-001",
    name="林墨",
    role="protagonist",
    attributes={"数据分析": 9, "工程技术": 8},
    resources={"信用点": 50000}
)

world.characters["CHAR-001"] = protagonist

# 打印状态
print(world.to_dict())
```

---

## 技术要点

### MCP 使用说明

MCP (Model Context Protocol) 是一个开放协议,用于管理 AI 模型的上下文。

**核心概念**:
1. **Resource**: 只读数据源(如 `world://state/location1`)
2. **Tool**: 可调用的函数(如 `query-evidence`)
3. **Prompt**: 提示词模板

**在本项目中的用途**:
- 管理小说世界的长期状态
- 存储和检索证据库
- 提供结构化的上下文给 LLM

**注意**: MCP 目前主要用于桌面应用(如 Claude Desktop)。服务器端使用需要自行实现客户端连接逻辑。**如果实现复杂,可以先用简单的 Python 类替代,后续再迁移**。

### LiteLLM 使用要点

- **配置驱动**: 所有模型配置在 YAML 中
- **自动降级**: 主模型失败时自动切换备用模型
- **统一接口**: 无需修改代码即可切换模型提供商
- **成本控制**: 可以根据成本选择模型

### Claude Agent SDK 注意事项

**现状**: Claude Agent SDK 可能尚未正式发布(需要确认)。

**替代方案**:
1. **提示词工程**: 使用结构化提示词实现类似效果
2. **LangChain/LlamaIndex**: 使用现有的 Agent 框架
3. **自实现**: 简单的任务分解+循环执行

**建议**: 先用提示词工程实现 MVP,观察 Agent SDK 的发布动态。

---

## 关键挑战与解决方案

### 挑战1: 一致性审计的复杂性

**问题**: 检查硬规则、因果链、资源守恒需要复杂的逻辑推理。

**解决方案**:
1. **规则引擎**: 使用规则引擎(如 Drools/Python-based)
2. **LLM辅助**: 用专门的提示词让 LLM 进行一致性检查
3. **增量验证**: 每步都验证,而不是事后检查

### 挑战2: 伏笔债务管理

**问题**: 跟踪大量伏笔的SLA和偿还状态。

**解决方案**:
- 数据库存储 `setup_debts` 表
- 每回合检查逾期伏笔
- 评分时提高逾期伏笔相关事件的权重

### 挑战3: 提示词注入与越狱

**问题**: 用户输入可能干扰系统提示词。

**解决方案**:
- 输入清洗
- 系统提示词与用户输入明确分离
- 使用 LiteLLM 的 `content_filter`

---

## 成本估算

基于 Claude Sonnet 4.5 定价(假设 $3/1M input tokens, $15/1M output tokens):

**场景**: 生成100章科幻小说(每章3000字)

- 输入: ~500K tokens (设定+上下文)
- 输出: ~10M tokens (生成内容)

**预估成本**: $1.5 (input) + $150 (output) = **~$151.5**

**优化策略**:
1. 使用 Claude Haiku 处理简单任务(便宜10倍)
2. 缓存重复查询
3. 批量生成

---

## 常见问题

### Q1: MCP Context7 是什么?在哪里找到?

**A**: MCP (Model Context Protocol) 是 Anthropic 推出的开放协议。"Context7" 可能是你提到的一个具体实现或服务器。

- MCP 官网: https://modelcontextprotocol.io/
- Python SDK: `pip install mcp`
- 官方 Servers: https://github.com/modelcontextprotocol/servers

如果找不到 Context7,可以自己实现一个 MCP Server(参考架构文档)。

### Q2: Claude Agent SDK 怎么安装?

**A**: 截至2025年1月,Claude Agent SDK 可能尚未正式发布。建议:

1. 关注官方文档: https://docs.anthropic.com/
2. 暂时使用提示词工程替代
3. 或使用 LangChain/LlamaIndex 的 Agent 功能

### Q3: 如何处理长小说的上下文限制?

**A**: 策略:
1. **分层上下文**: 只保留关键信息在上下文中
2. **向量检索**: 用 ChromaDB 存储历史,按需检索
3. **MCP Resource**: 用 MCP 管理世界状态,按需加载
4. **总结压缩**: 定期总结历史事件,替换原始文本

---

## 总结

你现在拥有:
- ✅ 完整的架构设计
- ✅ 项目结构和配置
- ✅ 核心数据模型
- ✅ LiteLLM 集成
- ✅ 两个示例设定

**下一步**:
1. 配置 `.env` (填入 API key)
2. 实现 Global Director 核心逻辑
3. 测试端到端场景生成
4. 迭代优化

预计 **2-3周** 可完成 MVP,能够生成基础的科幻/玄幻小说章节。

祝开发顺利! 🚀
