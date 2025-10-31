# 长篇小说生成系统 - 系统架构设计

## 一、系统总览

本系统是一个基于 AI 驱动的长篇小说生成平台，支持科幻超长小说和玄幻/仙侠网络小说两大类型。

### 核心组件

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                              │
│            (CLI / Web API / WebSocket)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              全局导演 (Global Director)                      │
│  - 事件线评分与调度                                          │
│  - 状态管理与一致性审计                                      │
│  - 线索经济与伏笔管理                                        │
└─────┬──────────┬──────────┬──────────────────────┬─────────┘
      │          │          │                      │
┌─────▼─────┐ ┌─▼────────┐ ┌▼──────────────┐ ┌────▼─────────┐
│Claude Agent│ │LiteLLM   │ │MCP Context    │ │State Store   │
│   SDK      │ │  Proxy   │ │  Manager      │ │(SQLite/PG)   │
│(任务执行)  │ │(模型路由)│ │(上下文/记忆)  │ │(持久化)      │
└───────────┘ └──────────┘ └───────────────┘ └──────────────┘
```

## 二、技术栈选型

### 2.1 核心框架
- **Python 3.11+**: 主要开发语言
- **FastAPI**: Web API 框架（可选，用于提供 REST API）
- **asyncio**: 异步任务调度

### 2.2 AI 组件

#### MCP (Model Context Protocol)
- **包**: `mcp` (PyPI)
- **用途**: 上下文管理、长期记忆、证据库
- **集成方式**:
  ```python
  from mcp import Server, Resource, Tool

  # 创建自定义 MCP server 用于管理小说世界状态
  server = Server("novel-world-server")

  @server.resource("world://state")
  async def get_world_state():
      return current_world_state

  @server.tool("query-evidence")
  async def query_evidence(query: str):
      return evidence_db.search(query)
  ```

#### Claude Agent SDK
- **包**: `anthropic-agents` (需从 GitHub 安装)
- **用途**: 执行复杂的多步骤任务（如章节生成、场景细化）
- **集成方式**:
  ```python
  from anthropic_agents import Agent, Task

  agent = Agent(
      api_key=os.getenv("ANTHROPIC_API_KEY"),
      model="claude-sonnet-4-5-20250929"
  )

  task = Task(
      description="根据事件节点生成详细场景",
      context=event_context
  )
  result = await agent.execute(task)
  ```

#### LiteLLM
- **包**: `litellm`
- **用途**: 统一多个 LLM 提供商的 API，支持负载均衡和回退
- **配置方式**:
  ```yaml
  # litellm_config.yaml
  model_list:
    - model_name: claude-sonnet
      litellm_params:
        model: anthropic/claude-sonnet-4-5-20250929
        api_key: ${ANTHROPIC_API_KEY}

    - model_name: gpt-4
      litellm_params:
        model: openai/gpt-4-turbo
        api_key: ${OPENAI_API_KEY}

  router_settings:
    routing_strategy: least-busy
    fallbacks: ["claude-sonnet", "gpt-4"]
  ```

### 2.3 数据层
- **SQLite**: 开发环境状态存储
- **PostgreSQL**: 生产环境（可选）
- **ChromaDB / FAISS**: 向量数据库（证据检索、语义搜索）

## 三、核心模块设计

### 3.1 全局导演 (Global Director)

```python
# src/director/gd.py

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum

class NovelType(Enum):
    SCIFI = "scifi"
    XIANXIA = "xianxia"

class Preference(Enum):
    PLAYABILITY = "playability"
    NARRATIVE = "narrative"
    HYBRID = "hybrid"

@dataclass
class WorldState:
    """世界状态"""
    time: int  # 时间戳
    locations: Dict[str, Dict]  # 地点状态
    characters: Dict[str, Dict]  # 角色状态
    factions: Dict[str, Dict]  # 势力状态
    resources: Dict[str, float]  # 资源池
    events_log: List[Dict]  # 事件历史

@dataclass
class EventNode:
    """事件节点"""
    id: str
    arc_id: str  # 所属事件线
    goal: str
    prerequisites: List[str]  # 前置条件
    effects: Dict[str, any]  # 状态变化
    tension_delta: float  # 张力增量
    setups: List[str]  # 埋下的伏笔
    clues: List[Dict]  # 提供的线索

@dataclass
class ActionQueue:
    """动作队列（一幕的具体执行）"""
    event_id: str
    steps: List[Dict]  # scene/interaction/check/tool/outcome
    hints: List[Dict]  # 提示槽位
    state_patch_schema: Dict  # 状态补丁模板

class GlobalDirector:
    """全局导演 - 系统核心调度器"""

    def __init__(
        self,
        setting: Dict,
        novel_type: NovelType,
        preference: Preference
    ):
        self.setting = setting
        self.novel_type = novel_type
        self.preference = preference
        self.world_state = WorldState(...)
        self.event_graph = {}  # 事件线图
        self.clue_registry = {}  # 线索登记册
        self.setup_debt = {}  # 伏笔债务（SLA）

    async def run_scene_loop(self):
        """场景循环主逻辑"""
        while not self.is_story_complete():
            # 1. 评分并选择下一个事件节点
            next_event = await self.score_and_select_event()

            # 2. 细化为动作队列
            action_queue = await self.generate_action_queue(next_event)

            # 3. 执行动作（调用 Agent）
            result = await self.execute_actions(action_queue)

            # 4. 一致性审计
            is_valid = await self.consistency_audit(result)
            if not is_valid:
                result = await self.rewrite_or_retry(result)

            # 5. 更新状态
            await self.apply_state_patch(result)

            # 6. 管理线索与伏笔债务
            await self.update_clue_economy(result)

            yield result

    async def score_and_select_event(self) -> EventNode:
        """评分并选择下一个事件"""
        candidates = self.get_available_events()
        scores = []

        for event in candidates:
            if self.preference == Preference.PLAYABILITY:
                score = self._score_playability(event)
            elif self.preference == Preference.NARRATIVE:
                score = self._score_narrative(event)
            else:  # HYBRID
                score = self._score_hybrid(event)
            scores.append((event, score))

        # 选择得分最高的
        return max(scores, key=lambda x: x[1])[0]

    def _score_playability(self, event: EventNode) -> float:
        """可玩性评分"""
        return (
            event.puzzle_density * 0.3 +
            event.skill_checks_variety * 0.2 +
            event.failure_grace * 0.15 +
            event.hint_latency * 0.15 +
            event.exploit_resistance * 0.1 +
            event.reward_loop * 0.1
        )

    def _score_narrative(self, event: EventNode) -> float:
        """叙事评分"""
        return (
            event.arc_progress * 0.25 +
            event.theme_echo * 0.2 +
            event.conflict_gradient * 0.2 +
            event.payoff_debt * 0.15 +
            event.scene_specificity * 0.1 +
            event.pacing_smoothness * 0.1
        )

    def _score_hybrid(self, event: EventNode) -> float:
        """混合评分"""
        playability = self._score_playability(event)
        narrative = self._score_narrative(event)

        # 动态调整权重
        if self.is_stalled(rounds=2):
            return playability * 0.7 + narrative * 0.3
        elif self.has_overdue_setups():
            return playability * 0.3 + narrative * 0.7
        else:
            return playability * 0.6 + narrative * 0.4

    async def generate_action_queue(self, event: EventNode) -> ActionQueue:
        """将事件节点细化为可执行的动作队列"""
        # 调用 LLM 生成详细步骤
        prompt = self._build_action_generation_prompt(event)
        response = await self.llm_client.generate(prompt)

        return ActionQueue.from_dict(response)

    async def execute_actions(self, queue: ActionQueue) -> Dict:
        """执行动作队列（委托给 Agent）"""
        from .agent_executor import AgentExecutor

        executor = AgentExecutor(
            agent_sdk=self.agent_sdk,
            mcp_client=self.mcp_client
        )

        return await executor.run(queue)

    async def consistency_audit(self, result: Dict) -> bool:
        """一致性审计"""
        checks = [
            self._check_hard_rules(result),
            self._check_causality(result),
            self._check_resource_conservation(result),
            self._check_theme_consistency(result)
        ]
        return all(checks)
```

### 3.2 Agent 执行器

```python
# src/director/agent_executor.py

from anthropic_agents import Agent, Task
from mcp import Client as MCPClient

class AgentExecutor:
    """使用 Claude Agent SDK 执行复杂任务"""

    def __init__(self, agent_sdk: Agent, mcp_client: MCPClient):
        self.agent = agent_sdk
        self.mcp_client = mcp_client

    async def run(self, action_queue: ActionQueue) -> Dict:
        """执行动作队列"""
        context = await self._prepare_context(action_queue)

        task = Task(
            description=f"执行事件 {action_queue.event_id}",
            context=context,
            steps=action_queue.steps
        )

        result = await self.agent.execute(task)

        # 后处理：提取结构化输出
        return self._parse_result(result)

    async def _prepare_context(self, queue: ActionQueue) -> str:
        """准备上下文（从 MCP 获取相关记忆）"""
        # 查询 MCP server 获取相关世界状态
        world_state = await self.mcp_client.call_tool(
            "query-world-state",
            {"event_id": queue.event_id}
        )

        # 查询相关证据
        relevant_clues = await self.mcp_client.call_tool(
            "query-evidence",
            {"query": queue.event_id}
        )

        context = f"""
        当前世界状态:
        {world_state}

        相关线索:
        {relevant_clues}

        待执行任务:
        {queue.steps}
        """

        return context
```

### 3.3 MCP 服务器

```python
# src/mcp_server/novel_world_server.py

from mcp import Server, Resource, Tool
from typing import Dict, List
import chromadb

class NovelWorldServer:
    """小说世界状态管理 MCP Server"""

    def __init__(self):
        self.server = Server("novel-world-server")
        self.db = chromadb.Client()  # 向量数据库
        self.collection = self.db.get_or_create_collection("evidence")

        self._register_resources()
        self._register_tools()

    def _register_resources(self):
        """注册资源"""

        @self.server.resource("world://state/{location}")
        async def get_location_state(location: str):
            """获取特定地点的状态"""
            return self.world_state.locations.get(location, {})

        @self.server.resource("world://character/{char_id}")
        async def get_character_state(char_id: str):
            """获取角色状态"""
            return self.world_state.characters.get(char_id, {})

    def _register_tools(self):
        """注册工具"""

        @self.server.tool("query-evidence")
        async def query_evidence(query: str, limit: int = 5):
            """语义搜索证据库"""
            results = self.collection.query(
                query_texts=[query],
                n_results=limit
            )
            return results

        @self.server.tool("add-evidence")
        async def add_evidence(
            evidence_id: str,
            content: str,
            metadata: Dict
        ):
            """添加新证据"""
            self.collection.add(
                ids=[evidence_id],
                documents=[content],
                metadatas=[metadata]
            )
            return {"status": "success"}

        @self.server.tool("verify-clue")
        async def verify_clue(clue_id: str, evidence_ids: List[str]):
            """验证线索（检查证据链）"""
            # 实现验证逻辑
            return {"verified": True, "confidence": 0.95}
```

### 3.4 LiteLLM 集成

```python
# src/llm/litellm_client.py

import litellm
from litellm import Router
from typing import Dict, List, Optional

class LiteLLMClient:
    """LiteLLM 统一客户端"""

    def __init__(self, config_path: str = "litellm_config.yaml"):
        # 加载配置
        self.router = Router(
            model_list=self._load_config(config_path)
        )

    async def generate(
        self,
        prompt: str,
        model: str = "claude-sonnet",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """生成文本"""
        response = await self.router.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content

    async def generate_structured(
        self,
        prompt: str,
        schema: Dict,
        model: str = "claude-sonnet"
    ) -> Dict:
        """生成结构化输出（JSON）"""
        response = await self.router.acompletion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object", "schema": schema}
        )
        return response.choices[0].message.content
```

## 四、数据模型

### 4.1 数据库 Schema

```sql
-- state_store.sql

CREATE TABLE world_states (
    id SERIAL PRIMARY KEY,
    timestamp BIGINT NOT NULL,
    state_json JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE event_nodes (
    id VARCHAR(50) PRIMARY KEY,
    arc_id VARCHAR(50) NOT NULL,
    goal TEXT NOT NULL,
    prerequisites JSONB,
    effects JSONB,
    tension_delta FLOAT,
    setups JSONB,
    clues JSONB,
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE clue_registry (
    clue_id VARCHAR(50) PRIMARY KEY,
    content TEXT NOT NULL,
    evidence_ids JSONB,
    verification_method VARCHAR(50),
    discovered_at TIMESTAMP
);

CREATE TABLE setup_debts (
    setup_id VARCHAR(50) PRIMARY KEY,
    description TEXT NOT NULL,
    sla_deadline BIGINT,
    payoff_event_id VARCHAR(50),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50),
    action_queue JSONB,
    result JSONB,
    stall_rounds INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_event_arc ON event_nodes(arc_id);
CREATE INDEX idx_setup_status ON setup_debts(status, sla_deadline);
```

## 五、配置文件

### 5.1 环境变量

```bash
# .env
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key  # 可选
DATABASE_URL=postgresql://user:pass@localhost/novel_db
VECTOR_DB_PATH=./data/chromadb
```

### 5.2 LiteLLM 配置

```yaml
# config/litellm_config.yaml
model_list:
  - model_name: claude-sonnet
    litellm_params:
      model: anthropic/claude-sonnet-4-5-20250929
      api_key: ${ANTHROPIC_API_KEY}
      max_tokens: 8000

  - model_name: claude-haiku
    litellm_params:
      model: anthropic/claude-3-5-haiku-20241022
      api_key: ${ANTHROPIC_API_KEY}
      max_tokens: 4000

router_settings:
  routing_strategy: least-busy
  fallbacks:
    - claude-sonnet
    - claude-haiku

  retry_policy:
    max_retries: 3
    retry_delay: 1.0
```

### 5.3 小说类型配置

```yaml
# config/novel_types.yaml
scifi:
  scoring_weights:
    playability:
      puzzle_density: 0.3
      skill_checks_variety: 0.2
      failure_grace: 0.15
      hint_latency: 0.15
      exploit_resistance: 0.1
      reward_loop: 0.1
    narrative:
      arc_progress: 0.25
      theme_echo: 0.2
      conflict_gradient: 0.2
      payoff_debt: 0.15
      scene_specificity: 0.1
      pacing_smoothness: 0.1

  pacing:
    acts_per_volume: 10
    scenes_per_act: 3
    progress_check_interval: 12  # 章节

xianxia:
  scoring_weights:
    # 玄幻偏重可玩性
    playability: 0.7
    narrative: 0.3

  pacing:
    爽点间隔: 2  # 章节
    阶段跃迁: 25  # 章节
```

## 六、部署架构

### 6.1 开发环境

```
┌─────────────┐
│   CLI/REPL  │
└──────┬──────┘
       │
┌──────▼──────────────────────┐
│  Global Director (Python)   │
│  + MCP Server (in-process)  │
└──────┬──────────────────────┘
       │
┌──────▼─────┐  ┌─────────────┐
│  SQLite    │  │  ChromaDB   │
└────────────┘  └─────────────┘
```

### 6.2 生产环境

```
┌────────────┐
│  用户界面   │ (Web/API)
└─────┬──────┘
      │
┌─────▼────────┐
│ FastAPI +    │
│ WebSocket    │
└─────┬────────┘
      │
┌─────▼────────────────────┐
│  Global Director         │
│  (多进程/异步)            │
└┬─────────┬────────────┬──┘
 │         │            │
 ▼         ▼            ▼
┌────┐  ┌────┐      ┌────┐
│MCP │  │Agent│      │LLM │
│Svr │  │ SDK │      │Proxy│
└────┘  └────┘      └────┘
 │         │            │
 └─────┬───┴────────────┘
       ▼
┌──────────────┐
│ PostgreSQL + │
│ ChromaDB     │
└──────────────┘
```

## 七、开发路线图

### Phase 1: MVP (2-3 周)
1. 项目结构搭建
2. Global Director 核心逻辑
3. 基础 LiteLLM 集成
4. SQLite 状态存储
5. 单线程事件循环
6. CLI 交互界面

### Phase 2: 增强 (2-3 周)
7. MCP Server 实现
8. Claude Agent SDK 集成
9. 向量数据库（证据检索）
10. 一致性审计系统
11. 伏笔债务管理

### Phase 3: 优化 (2 周)
12. 异步任务调度
13. 性能优化（缓存、批处理）
14. PostgreSQL 迁移
15. 监控与日志

### Phase 4: 产品化 (3 周)
16. Web API (FastAPI)
17. 用户认证
18. 多小说并发管理
19. 导出功能（Markdown/EPUB）
20. 部署脚本
