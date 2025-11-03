# Phase 2 技术实现计划（基于 Claude Agent SDK）

**文档版本**: 3.0
**创建日期**: 2025-11-02
**更新日期**: 2025-11-03
**目标**: 使用 Claude Agent SDK 构建游戏 Agent 系统

**实施状态**: 🟡 进行中 (Week 1-2)

---

## 核心架构说明

### 技术栈选型

**核心原则**: 使用 **Claude Agent SDK 构建项目中的所有 Agent**

1. **Claude Agent SDK** (`claude-agent-sdk`):
   - Anthropic 官方 Agent 框架
   - 支持 **自定义工具** (通过 MCP Server)
   - 支持 **内置工具** (Read/Write/Bash等)
   - 支持 **流式输出** (SSE)
   - 支持 **对话历史管理**
   - 支持 **Hook 系统** (PreToolUse/PostToolUse)

2. **MCP (Model Context Protocol)**:
   - 用于定义自定义工具
   - 使用 `create_sdk_mcp_server` 创建游戏工具服务器
   - 工具自动注册到 Agent

3. **LiteLLM Proxy** (可选):
   - 已配置完成 (localhost:4000)
   - Claude Agent SDK 可能支持通过环境变量路由
   - 需要验证兼容性

### 架构图

```
┌─────────────────────────────────────────────────┐
│  FastAPI Backend (web/backend/)                │
│  ┌───────────────────────────────────────────┐ │
│  │  Agent 层                                  │ │
│  │  ┌─────────────────────────────────────┐  │ │
│  │  │  DM Agent                           │  │ │
│  │  │  - 游戏回合处理                      │  │ │
│  │  │  - 工具调用                          │  │ │
│  │  └─────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────┐  │ │
│  │  │  NPC Agent                          │  │ │
│  │  │  - 对话生成                          │  │ │
│  │  │  - 记忆管理                          │  │ │
│  │  └─────────────────────────────────────┘  │ │
│  │  ┌─────────────────────────────────────┐  │ │
│  │  │  Quest Agent                        │  │ │
│  │  │  - 任务生成                          │  │ │
│  │  │  - 数据库操作                        │  │ │
│  │  └─────────────────────────────────────┘  │ │
│  └───────────────────────────────────────────┘ │
│                     │                           │
│                     ▼                           │
│  ┌───────────────────────────────────────────┐ │
│  │  MCP Server (自定义游戏工具)               │ │
│  │  - roll_check                             │ │
│  │  - add_item / remove_item                 │ │
│  │  - update_hp                              │ │
│  │  - set_location                           │ │
│  │  - create_quest / update_quest            │ │
│  │  - save_game / load_game                  │ │
│  └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
                      │
                      ▼ Claude Code CLI
┌─────────────────────────────────────────────────┐
│  Claude API (可能通过 LiteLLM Proxy)            │
│  - DeepSeek V3 (主力模型)                        │
│  - Claude Sonnet (高质量备用)                     │
└─────────────────────────────────────────────────┘
```

### 为什么使用 Claude Agent SDK?

1. **Agent 是第一公民**:
   - DM Agent、NPC Agent、Quest Agent 都是独立的智能体
   - 每个 Agent 有自己的系统提示词、工具集、记忆

2. **自定义工具支持**:
   - 通过 MCP Server 定义游戏工具
   - Agent SDK 自动处理工具调用循环
   - 不需要手动解析和执行

3. **对话历史管理**:
   - SDK 自动管理多轮对话
   - 适合 NPC 记忆和 DM 上下文

4. **流式输出**:
   - 原生支持 SSE
   - 更好的用户体验

5. **开发效率**:
   - 减少 60% 样板代码
   - 专注业务逻辑而非基础设施
```

---

## 目录

1. [存档系统详细设计](#1-存档系统详细设计)
2. [任务系统实现方案](#2-任务系统实现方案)
3. [NPC系统架构设计](#3-npc系统架构设计)
4. [游戏工具系统（Tool Use）](#4-游戏工具系统tool-use)
5. [性能优化方案](#5-性能优化方案)
6. [测试策略](#6-测试策略)

---

## 1. 存档系统详细设计

### 1.1 数据库Schema

```sql
-- 游戏存档表
CREATE TABLE game_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default_user',
    slot_id INTEGER NOT NULL CHECK(slot_id >= 1 AND slot_id <= 10),
    save_name TEXT NOT NULL,
    game_state TEXT NOT NULL,  -- JSON格式的完整游戏状态
    metadata TEXT,              -- JSON格式的元数据
    screenshot_url TEXT,        -- 存档截图URL（可选）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, slot_id)
);

-- 存档快照表（用于回滚）
CREATE TABLE save_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    snapshot_data TEXT NOT NULL,  -- JSON格式的状态快照
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (save_id) REFERENCES game_saves(id) ON DELETE CASCADE
);

-- 自动保存记录表
CREATE TABLE auto_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    game_state TEXT NOT NULL,
    turn_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 创建索引
CREATE INDEX idx_game_saves_user_id ON game_saves(user_id);
CREATE INDEX idx_save_snapshots_save_id ON save_snapshots(save_id);
CREATE INDEX idx_auto_saves_user_id ON auto_saves(user_id);
```

### 1.2 API接口设计

#### 1.2.1 保存游戏

**端点**: `POST /api/game/save`

**请求体**:
```json
{
  "slot_id": 1,
  "save_name": "冒险的开始",
  "game_state": {
    "player": {...},
    "world": {...},
    "quests": [...],
    "turn_number": 42
  },
  "auto_save": false
}
```

**响应**:
```json
{
  "save_id": 123,
  "slot_id": 1,
  "save_name": "冒险的开始",
  "created_at": "2025-11-02T10:30:00Z",
  "message": "游戏保存成功"
}
```

#### 1.2.2 其他API

- `GET /api/game/saves` - 获取存档列表
- `GET /api/game/save/{save_id}` - 加载存档
- `DELETE /api/game/save/{save_id}` - 删除存档
- `POST /api/game/save/{save_id}/snapshot` - 创建快照

### 1.3 Python实现

**文件**: `web/backend/services/save_service.py`

```python
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import sqlite3

class SaveService:
    """游戏存档服务"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def save_game(
        self,
        user_id: str,
        slot_id: int,
        save_name: str,
        game_state: Dict[str, Any],
        auto_save: bool = False
    ) -> int:
        """保存游戏"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 提取元数据
            metadata = {
                "turn_number": game_state.get("turn_number", 0),
                "playtime": game_state.get("playtime", 0),
                "location": game_state.get("world", {}).get("current_location"),
                "level": game_state.get("player", {}).get("level", 1)
            }

            # 插入或更新存档
            cursor.execute("""
                INSERT INTO game_saves (user_id, slot_id, save_name, game_state, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, slot_id) DO UPDATE SET
                    save_name = ?,
                    game_state = ?,
                    metadata = ?,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id, slot_id, save_name,
                json.dumps(game_state),
                json.dumps(metadata),
                save_name,
                json.dumps(game_state),
                json.dumps(metadata)
            ))

            save_id = cursor.lastrowid

            # 如果不是自动保存，创建快照
            if not auto_save:
                cursor.execute("""
                    INSERT INTO save_snapshots (save_id, turn_number, snapshot_data)
                    VALUES (?, ?, ?)
                """, (save_id, game_state.get("turn_number", 0), json.dumps(game_state)))

            conn.commit()
            return save_id

        finally:
            conn.close()

    def get_saves(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有存档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, slot_id, save_name, metadata,
                       screenshot_url, created_at, updated_at
                FROM game_saves
                WHERE user_id = ?
                ORDER BY slot_id
            """, (user_id,))

            saves = []
            for row in cursor.fetchall():
                saves.append({
                    "save_id": row[0],
                    "slot_id": row[1],
                    "save_name": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "screenshot_url": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                })

            return saves

        finally:
            conn.close()

    def load_game(self, save_id: int) -> Optional[Dict[str, Any]]:
        """加载存档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT game_state, metadata
                FROM game_saves
                WHERE id = ?
            """, (save_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "game_state": json.loads(row[0]),
                    "metadata": json.loads(row[1]) if row[1] else {}
                }
            return None

        finally:
            conn.close()
```

---

## 2. 任务系统实现方案

### 2.1 任务数据模型

**文件**: `web/backend/models/quest_models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class QuestType(str, Enum):
    MAIN = "main"
    SIDE = "side"
    HIDDEN = "hidden"

class QuestStatus(str, Enum):
    AVAILABLE = "available"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"

class ObjectiveType(str, Enum):
    EXPLORE = "explore"
    COLLECT = "collect"
    DEFEAT = "defeat"
    TALK = "talk"
    REACH = "reach"

class QuestObjective(BaseModel):
    id: str
    type: ObjectiveType
    description: str
    target: str  # location_id, item_id, npc_id, enemy_id
    current: int = 0
    required: int = 1
    completed: bool = False

class QuestReward(BaseModel):
    exp: int = 0
    gold: int = 0
    items: List[Dict[str, Any]] = Field(default_factory=list)

class Quest(BaseModel):
    id: str
    type: QuestType
    title: str
    description: str
    level_requirement: int = 1

    # 目标和进度
    objectives: List[QuestObjective]
    status: QuestStatus = QuestStatus.AVAILABLE

    # 奖励
    rewards: QuestReward

    # 关联
    prerequisite_quests: List[str] = Field(default_factory=list)
    next_quests: List[str] = Field(default_factory=list)

    # 元数据
    giver_npc: Optional[str] = None
    location: Optional[str] = None
```

### 2.2 任务生成器（使用 Anthropic SDK）

**文件**: `web/backend/services/quest_generator.py`

```python
from anthropic import Anthropic
from typing import Dict, Any
import os
import json

class QuestGenerator:
    """使用 Anthropic SDK 生成任务"""

    def __init__(self):
        # 初始化 Anthropic 客户端（通过 LiteLLM Proxy）
        self.client = Anthropic(
            api_key=os.getenv("LITELLM_MASTER_KEY"),
            base_url="http://localhost:4000"  # LiteLLM Proxy
        )
        self.model = "deepseek"  # 通过 LiteLLM 路由到 DeepSeek V3

    async def generate_quest(
        self,
        quest_type: str,
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成任务"""

        # 构建提示词
        prompt = f"""基于当前游戏状态生成一个{quest_type}任务。

游戏状态:
- 玩家等级: {game_state.get('player', {}).get('level', 1)}
- 当前位置: {game_state.get('world', {}).get('current_location')}
- 已完成任务数: {len(game_state.get('completed_quests', []))}

要求:
1. 任务应适合当前等级
2. 任务目标清晰（1-3个）
3. 奖励合理
4. 包含简短的背景故事

返回JSON格式，包含:
{{
  "title": "任务标题",
  "description": "任务描述",
  "objectives": [
    {{"type": "explore|collect|defeat", "description": "目标描述", "target": "目标ID", "required": 数量}}
  ],
  "rewards": {{"exp": 经验值, "gold": 金币, "items": []}}
}}
"""

        # 调用 Anthropic API
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # 提取响应文本
        response_text = message.content[0].text

        # 解析 JSON
        quest_data = json.loads(response_text)

        return quest_data

    def check_objective_completion(
        self,
        objective: QuestObjective,
        game_state: Dict[str, Any]
    ) -> bool:
        """检查目标是否完成"""

        if objective.type == ObjectiveType.EXPLORE:
            return game_state.get("world", {}).get("current_location") == objective.target

        elif objective.type == ObjectiveType.COLLECT:
            player_items = game_state.get("player", {}).get("inventory", [])
            count = sum(1 for item in player_items if item.get("id") == objective.target)
            return count >= objective.required

        elif objective.type == ObjectiveType.DEFEAT:
            defeated = game_state.get("defeated_enemies", [])
            return objective.target in defeated

        return False
```

---

## 3. NPC系统架构设计

### 3.1 NPC数据模型

**文件**: `web/backend/models/npc_models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from enum import Enum

class NPCStatus(str, Enum):
    SEED = "seed"
    ACTIVE = "active"
    INACTIVE = "inactive"
    RETIRED = "retired"

class NPCPersonality(BaseModel):
    traits: List[str] = Field(default_factory=list)
    values: Dict[str, int] = Field(default_factory=dict)
    speech_style: str = ""

class NPCMemory(BaseModel):
    turn_number: int
    event_type: str
    summary: str
    emotional_impact: int = 0

class NPC(BaseModel):
    id: str
    name: str
    role: str
    status: NPCStatus = NPCStatus.SEED

    # 属性
    level: int = 1
    personality: NPCPersonality = Field(default_factory=NPCPersonality)

    # 记忆和目标
    memories: List[NPCMemory] = Field(default_factory=list)
    goals: List[str] = Field(default_factory=list)

    # 位置
    current_location: Optional[str] = None
    available_quests: List[str] = Field(default_factory=list)
```

### 3.2 NPC管理器（使用 Anthropic SDK）

**文件**: `web/backend/services/npc_manager.py`

```python
from anthropic import Anthropic
from typing import Dict, Any
import os
import json

class NPCManager:
    """NPC 生命周期管理器"""

    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv("LITELLM_MASTER_KEY"),
            base_url="http://localhost:4000"
        )
        self.model = "deepseek"

    async def generate_npc(
        self,
        location: str,
        role: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """生成 NPC"""

        prompt = f"""在{location}创建一个{role}角色。

上下文信息:
- 世界观: {context.get('world_theme')}
- 当前剧情: {context.get('current_story')}

生成角色的:
1. 名字（符合世界观）
2. 外貌描述
3. 性格特征（3-5个）
4. 说话风格
5. 目标/动机

返回JSON格式。
"""

        message = await self.client.messages.create(
            model=self.model,
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )

        npc_data = json.loads(message.content[0].text)
        return npc_data

    async def npc_dialogue(
        self,
        npc: NPC,
        player_message: str,
        game_state: Dict[str, Any]
    ) -> str:
        """NPC 对话"""

        # 构建系统提示词
        system_prompt = f"""你是{npc.name}，一个{npc.role}。

性格特征: {', '.join(npc.personality.traits)}
说话风格: {npc.personality.speech_style}

你的目标:
{chr(10).join([f"- {goal}" for goal in npc.goals])}

最近记忆:
{self._format_memories(npc.memories[-5:])}

保持角色一致性，根据记忆调整对玩家的态度。
"""

        # 调用 API
        message = await self.client.messages.create(
            model=self.model,
            max_tokens=500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": f"玩家说: {player_message}"}
            ]
        )

        response = message.content[0].text

        # 更新 NPC 记忆
        npc.memories.append(NPCMemory(
            turn_number=game_state.get("turn_number", 0),
            event_type="conversation",
            summary=f"玩家: {player_message[:50]}... | {npc.name}: {response[:50]}..."
        ))

        return response

    def _format_memories(self, memories: List[NPCMemory]) -> str:
        if not memories:
            return "（首次见面）"
        return "\n".join([f"- 回合{m.turn_number}: {m.summary}" for m in memories])
```

---

## 4. 游戏工具系统（MCP Server）

这是核心部分 - 使用 **Claude Agent SDK 的 MCP Server** 实现游戏工具。

### 4.1 MCP 工具定义与实现

**文件**: `web/backend/agents/game_tools.py`

```python
from typing import Dict, Any
from claude_agent_sdk import tool
import random

# ============= 游戏状态管理 =============

# 全局游戏状态（实际应从数据库或session获取）
_game_states: Dict[str, Dict[str, Any]] = {}

class GameStateManager:
    """游戏状态管理器 - 处理数据库访问"""

    def __init__(self, db_connection):
        self.db = db_connection

    def get_state(self, session_id: str) -> Dict[str, Any]:
        """从数据库获取游戏状态"""
        # 先查内存缓存
        if session_id in _game_states:
            return _game_states[session_id]

        # 从数据库加载
        state = self.db.load_game_state(session_id)
        if state:
            _game_states[session_id] = state
            return state

        # 创建新状态
        return self._create_new_state(session_id)

    def save_state(self, session_id: str, state: Dict[str, Any]):
        """保存游戏状态到数据库"""
        _game_states[session_id] = state
        self.db.save_game_state(session_id, state)

    def _create_new_state(self, session_id: str) -> Dict[str, Any]:
        """创建新游戏状态"""
        state = {
            "player": {
                "hp": 100,
                "max_hp": 100,
                "stamina": 100,
                "inventory": [],
                "gold": 0
            },
            "world": {
                "current_location": "起始村庄",
                "theme": "奇幻世界"
            },
            "turn_number": 0,
            "logs": []
        }
        _game_states[session_id] = state
        return state

# 全局状态管理器实例（在应用启动时初始化）
state_manager: GameStateManager = None

def init_state_manager(db_connection):
    """初始化状态管理器"""
    global state_manager
    state_manager = GameStateManager(db_connection)

# ============= MCP 工具定义 =============

# 当前会话ID（从上下文传入）
current_session_id: str = "default"

def set_session(session_id: str):
    """设置当前会话ID"""
    global current_session_id
    current_session_id = session_id

# 工具装饰器定义
# @tool(name, description, input_schema)

@tool(
    "get_player_state",
    "获取玩家当前状态（HP、背包、位置等）",
    {
        "type": "object",
        "properties": {},
        "required": []
    }
)
async def get_player_state(args: Dict) -> Dict[str, Any]:
    """获取玩家状态

    这个工具会从数据库读取游戏状态
    """
    state = state_manager.get_state(current_session_id)
    player = state.get('player', {})

    return {
        "hp": player.get('hp', 100),
        "max_hp": player.get('max_hp', 100),
        "stamina": player.get('stamina', 100),
        "location": state.get('world', {}).get('current_location'),
        "inventory": player.get('inventory', []),
        "gold": player.get('gold', 0)
    }

@tool(
    "add_item",
    "向玩家背包添加物品",
    {
        "type": "object",
        "properties": {
            "item_id": {
                "type": "string",
                "description": "物品ID"
            },
            "quantity": {
                "type": "integer",
                "description": "数量",
                "minimum": 1,
                "default": 1
            }
        },
        "required": ["item_id"]
    }
)
async def add_item(args: Dict) -> Dict[str, Any]:
    """添加物品到背包

    这个工具会修改游戏状态并保存到数据库
    """
    item_id = args['item_id']
    quantity = args.get('quantity', 1)

    # 从数据库获取状态
    state = state_manager.get_state(current_session_id)
    player = state.setdefault('player', {})
    inventory = player.setdefault('inventory', [])

    # 查找已存在的物品
    existing = next((item for item in inventory if item['id'] == item_id), None)

    if existing:
        existing['quantity'] += quantity
    else:
        inventory.append({
            "id": item_id,
            "name": item_id,
            "quantity": quantity
        })

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "message": f"获得了 {quantity} 个 {item_id}",
        "current_inventory": inventory
    }

@tool(
    "update_hp",
    "更新玩家HP",
    {
        "type": "object",
        "properties": {
            "change": {
                "type": "integer",
                "description": "HP变化量（正数为恢复，负数为伤害）"
            },
            "reason": {
                "type": "string",
                "description": "原因描述",
                "default": ""
            }
        },
        "required": ["change"]
    }
)
async def update_hp(args: Dict) -> Dict[str, Any]:
    """更新HP

    这个工具会修改HP并保存到数据库
    """
    change = args['change']
    reason = args.get('reason', '')

    state = state_manager.get_state(current_session_id)
    player = state.setdefault('player', {})

    old_hp = player.get('hp', 100)
    max_hp = player.get('max_hp', 100)

    new_hp = max(0, min(max_hp, old_hp + change))
    player['hp'] = new_hp

    # 记录日志
    logs = state.setdefault('logs', [])
    logs.append(f"HP变化: {old_hp} → {new_hp} ({reason})")

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    result = {
        "old_hp": old_hp,
        "new_hp": new_hp,
        "change": change,
        "reason": reason
    }

    if new_hp == 0:
        result["status"] = "死亡"
    elif new_hp < max_hp * 0.3:
        result["status"] = "危险"
    else:
        result["status"] = "正常"

    return result

@tool(
    "roll_check",
    "进行技能检定（d20系统）",
    {
        "type": "object",
        "properties": {
            "skill": {
                "type": "string",
                "description": "技能名称（如：力量、敏捷、感知）"
            },
            "dc": {
                "type": "integer",
                "description": "难度等级（DC）"
            },
            "modifier": {
                "type": "integer",
                "description": "修正值",
                "default": 0
            },
            "advantage": {
                "type": "boolean",
                "description": "是否有优势",
                "default": False
            }
        },
        "required": ["skill", "dc"]
    }
)
async def roll_check(args: Dict) -> Dict[str, Any]:
    """技能检定

    这个工具不需要访问数据库，只是执行随机检定
    """
    skill = args['skill']
    dc = args['dc']
    modifier = args.get('modifier', 0)
    advantage = args.get('advantage', False)

    if advantage:
        roll1 = random.randint(1, 20)
        roll2 = random.randint(1, 20)
        roll = max(roll1, roll2)
        detail = f"优势检定: {roll1}, {roll2} -> {roll}"
    else:
        roll = random.randint(1, 20)
        detail = f"检定: {roll}"

    total = roll + modifier
    success = total >= dc

    # 记录到游戏日志
    state = state_manager.get_state(current_session_id)
    logs = state.setdefault('logs', [])
    logs.append(f"{skill}检定: {total} vs DC{dc} ({'成功' if success else '失败'})")
    state_manager.save_state(current_session_id, state)

    return {
        "skill": skill,
        "roll": roll,
        "modifier": modifier,
        "total": total,
        "dc": dc,
        "success": success,
        "detail": detail,
        "result": "成功!" if success else "失败!"
    }

@tool(
    "set_location",
    "设置玩家位置",
    {
        "type": "object",
        "properties": {
            "location_id": {
                "type": "string",
                "description": "位置ID"
            },
            "description": {
                "type": "string",
                "description": "位置描述",
                "default": ""
            }
        },
        "required": ["location_id"]
    }
)
async def set_location(args: Dict) -> Dict[str, Any]:
    """设置位置

    这个工具会更新世界状态并保存到数据库
    """
    location_id = args['location_id']
    description = args.get('description', '')

    state = state_manager.get_state(current_session_id)
    world = state.setdefault('world', {})

    old_location = world.get('current_location', '未知')
    world['current_location'] = location_id

    # 记录到日志
    logs = state.setdefault('logs', [])
    logs.append(f"从 {old_location} 移动到 {location_id}")

    # 保存到数据库
    state_manager.save_state(current_session_id, state)

    return {
        "success": True,
        "old_location": old_location,
        "new_location": location_id,
        "description": description
    }

# ============= 数据库工具（用于任务系统等）=============

@tool(
    "create_quest",
    "创建新任务并保存到数据库",
    {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "任务标题"},
            "description": {"type": "string", "description": "任务描述"},
            "objectives": {
                "type": "array",
                "description": "任务目标列表",
                "items": {"type": "object"}
            },
            "rewards": {
                "type": "object",
                "description": "任务奖励"
            }
        },
        "required": ["title", "description", "objectives", "rewards"]
    }
)
async def create_quest(args: Dict) -> Dict[str, Any]:
    """创建任务

    这个工具直接操作数据库
    """
    quest_data = {
        "title": args["title"],
        "description": args["description"],
        "objectives": args["objectives"],
        "rewards": args["rewards"],
        "status": "available"
    }

    # 保存到数据库
    quest_id = state_manager.db.save_quest(quest_data)

    # 也更新游戏状态
    state = state_manager.get_state(current_session_id)
    available_quests = state.setdefault('available_quests', [])
    available_quests.append(quest_id)
    state_manager.save_state(current_session_id, state)

    return {
        "quest_id": quest_id,
        "message": f"任务 '{args['title']}' 创建成功"
    }

@tool(
    "save_game",
    "保存游戏到存档槽位",
    {
        "type": "object",
        "properties": {
            "slot_id": {"type": "integer", "minimum": 1, "maximum": 10},
            "save_name": {"type": "string"}
        },
        "required": ["slot_id", "save_name"]
    }
)
async def save_game(args: Dict) -> Dict[str, Any]:
    """保存游戏

    这个工具将当前游戏状态保存到指定存档槽位
    """
    slot_id = args['slot_id']
    save_name = args['save_name']

    # 获取当前游戏状态
    state = state_manager.get_state(current_session_id)

    # 保存到存档表
    save_id = state_manager.db.save_to_slot(
        user_id="default_user",
        slot_id=slot_id,
        save_name=save_name,
        game_state=state
    )

    return {
        "save_id": save_id,
        "slot_id": slot_id,
        "save_name": save_name,
        "message": "游戏保存成功"
    }

# ============= 导出所有工具 =============

ALL_GAME_TOOLS = [
    get_player_state,
    add_item,
    update_hp,
    roll_check,
    set_location,
    create_quest,
    save_game
]
```

### 4.2 创建 MCP Server

**文件**: `web/backend/agents/mcp_servers.py`

```python
from claude_agent_sdk import create_sdk_mcp_server
from .game_tools import ALL_GAME_TOOLS, init_state_manager

def create_game_mcp_server(db_connection):
    """创建游戏工具 MCP Server

    Args:
        db_connection: 数据库连接对象

    Returns:
        MCP Server 实例
    """
    # 初始化状态管理器
    init_state_manager(db_connection)

    # 创建 MCP Server
    server = create_sdk_mcp_server(
        name="game-tools",
        version="1.0.0",
        tools=ALL_GAME_TOOLS
    )

    return server

# 使用示例
def get_game_server():
    """获取游戏 MCP Server（单例）"""
    from ..database.world_db import WorldDatabase

    # 获取数据库连接
    db = WorldDatabase("data/sqlite/game.db")

    # 创建 MCP Server
    return create_game_mcp_server(db)
```

### 4.3 在 Agent 中使用 MCP Server

**文件**: `web/backend/agents/dm_agent.py`

```python
from claude_agent_sdk import query, ClaudeAgentOptions
from typing import Dict, Any
from .mcp_servers import get_game_server
from .game_tools import set_session

class DMAgent:
    """游戏主持人 Agent"""

    def __init__(self):
        # 获取 MCP Server
        self.game_server = get_game_server()

        # 配置 Agent 选项
        self.base_options = ClaudeAgentOptions(
            mcp_servers={"game": self.game_server},
            allowed_tools=[
                "mcp__game__get_player_state",
                "mcp__game__add_item",
                "mcp__game__update_hp",
                "mcp__game__roll_check",
                "mcp__game__set_location"
            ]
        )

    async def process_turn(
        self,
        session_id: str,
        player_action: str,
        game_state: Dict[str, Any]
    ):
        """处理游戏回合

        Args:
            session_id: 会话ID（用于区分不同玩家）
            player_action: 玩家行动
            game_state: 当前游戏状态
        """
        # 设置当前会话
        set_session(session_id)

        # 构建系统提示词
        system_prompt = f"""你是一个单人跑团游戏的游戏主持人（DM）。

世界设定:
{game_state.get('world', {}).get('theme', '奇幻世界')}

当前状态:
- 位置: {game_state.get('world', {}).get('current_location', '未知')}
- 回合数: {game_state.get('turn_number', 0)}

你的职责:
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具调用来更新游戏状态:
   - get_player_state: 获取玩家状态
   - add_item: 给予物品
   - update_hp: 修改HP
   - roll_check: 进行技能检定
   - set_location: 移动到新位置
5. 提供2-3个有趣的行动建议

重要: 当玩家行动导致状态变化时，必须调用相应的工具！
"""

        # 构建提示词
        prompt = f"""玩家行动: {player_action}

请作为DM处理这个行动，使用工具更新游戏状态，并生成精彩的场景描述。
"""

        # 配置选项
        options = ClaudeAgentOptions(
            system_prompt=system_prompt,
            mcp_servers={"game": self.game_server},
            allowed_tools=self.base_options.allowed_tools
        )

        # 流式返回
        async for message in query(prompt=prompt, options=options):
            yield message
```

### 4.4 关键要点

1. **状态管理**:
   - 使用 `GameStateManager` 统一管理游戏状态
   - 状态先缓存在内存，然后同步到数据库
   - 每个会话有独立的状态（通过 `session_id` 区分）

2. **工具定义**:
   - 使用 `@tool` 装饰器定义工具
   - 参数使用 JSON Schema 验证
   - 工具函数内部可以访问数据库

3. **MCP Server**:
   - 使用 `create_sdk_mcp_server` 创建服务器
   - 一个 MCP Server 可以包含多个工具
   - 在 Agent 中通过 `mcp_servers` 参数注册

4. **数据库访问**:
   - 工具函数通过 `state_manager.db` 访问数据库
   - 支持读取和写入操作
   - 自动处理缓存和持久化

5. **工具命名**:
   - 在 Agent 中使用 `mcp__<server>__<tool>` 格式
   - 例如: `mcp__game__roll_check`

---

## 5. 游戏引擎（Agent 集成）

### 5.1 完整的 DM Agent

将上面的代码整合，创建完整的游戏引擎：

**文件**: `web/backend/game/game_engine.py` → `web/backend/agents/game_engine.py`

```python
from typing import Dict, Any, AsyncIterator
from .dm_agent import DMAgent
from .game_tools import set_session, state_manager

class GameEngine:
    """游戏引擎 - 基于 Claude Agent SDK"""

    def __init__(self):
        self.dm_agent = DMAgent()

    async def process_turn(
        self,
        session_id: str,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        """处理游戏回合（流式）

        Args:
            session_id: 会话ID
            player_action: 玩家行动
            game_state: 当前游戏状态

        Yields:
            事件字典（类型: narration/tool_call/complete）
        """
        # 设置会话
        set_session(session_id)

        # 调用 DM Agent
        async for message in self.dm_agent.process_turn(
            session_id=session_id,
            player_action=player_action,
            game_state=game_state
        ):
            # 解析消息类型
            if hasattr(message, 'type'):
                if message.type == 'text':
                    yield {
                        "type": "narration",
                        "content": message.text
                    }
                elif message.type == 'tool_use':
                    yield {
                        "type": "tool_call",
                        "tool": message.name,
                        "input": message.input
                    }
                elif message.type == 'tool_result':
                    yield {
                        "type": "tool_result",
                        "result": message.output
                    }

        # 获取更新后的状态
        updated_state = state_manager.get_state(session_id)
        updated_state['turn_number'] = updated_state.get('turn_number', 0) + 1

        yield {
            "type": "complete",
            "state": updated_state
        }
```

---

## 6. API 路由（FastAPI 集成）

### 6.1 游戏 API

**文件**: `web/backend/api/game_api.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, AsyncIterator
import json

from ..agents.game_engine import GameEngine

router = APIRouter(prefix="/api/game", tags=["game"])

# 全局引擎实例
game_engine = GameEngine()

class GameTurnRequest(BaseModel):
    session_id: str
    action: str
    state: Dict[str, Any]

@router.post("/turn/stream")
async def process_turn_stream(request: GameTurnRequest):
    """处理游戏回合（流式）"""

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in game_engine.process_turn(
                session_id=request.session_id,
                player_action=request.action,
                game_state=request.state
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

现在 MCP 工具系统的完整构建方式已经清楚了：

1. **定义工具** (`@tool` 装饰器)
2. **访问数据库** (通过 `GameStateManager`)
3. **创建 MCP Server** (`create_sdk_mcp_server`)
4. **在 Agent 中使用** (`ClaudeAgentOptions.mcp_servers`)
5. **API 集成** (FastAPI 路由)
    {
        "name": "get_player_state",
        "description": "获取玩家当前状态（HP、背包、位置等）",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "add_item",
        "description": "向玩家背包添加物品",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {
                    "type": "string",
                    "description": "物品ID"
                },
                "quantity": {
                    "type": "integer",
                    "description": "数量",
                    "minimum": 1
                }
            },
            "required": ["item_id"]
        }
    },
    {
        "name": "remove_item",
        "description": "从背包移除物品",
        "input_schema": {
            "type": "object",
            "properties": {
                "item_id": {"type": "string"},
                "quantity": {"type": "integer", "minimum": 1}
            },
            "required": ["item_id"]
        }
    },
    {
        "name": "update_hp",
        "description": "更新玩家HP",
        "input_schema": {
            "type": "object",
            "properties": {
                "change": {
                    "type": "integer",
                    "description": "HP变化量（正数为恢复，负数为伤害）"
                },
                "reason": {
                    "type": "string",
                    "description": "原因描述"
                }
            },
            "required": ["change"]
        }
    },
    {
        "name": "roll_check",
        "description": "进行技能检定（d20系统）",
        "input_schema": {
            "type": "object",
            "properties": {
                "skill": {
                    "type": "string",
                    "description": "技能名称（如：力量、敏捷、感知）"
                },
                "dc": {
                    "type": "integer",
                    "description": "难度等级（DC）"
                },
                "modifier": {
                    "type": "integer",
                    "description": "修正值",
                    "default": 0
                },
                "advantage": {
                    "type": "boolean",
                    "description": "是否有优势",
                    "default": False
                }
            },
            "required": ["skill", "dc"]
        }
    },
    {
        "name": "set_location",
        "description": "设置玩家位置",
        "input_schema": {
            "type": "object",
            "properties": {
                "location_id": {"type": "string"},
                "description": {"type": "string"}
            },
            "required": ["location_id"]
        }
    }
]

# ============= 工具实现函数 =============

class GameToolExecutor:
    """游戏工具执行器"""

    def __init__(self, game_state: Dict[str, Any]):
        self.game_state = game_state

    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """执行工具调用"""

        method = getattr(self, tool_name, None)
        if not method:
            return {"error": f"Unknown tool: {tool_name}"}

        return method(tool_input)

    def get_player_state(self, args: Dict) -> Dict[str, Any]:
        """获取玩家状态"""
        player = self.game_state.get('player', {})
        return {
            "hp": player.get('hp', 100),
            "max_hp": player.get('max_hp', 100),
            "stamina": player.get('stamina', 100),
            "location": self.game_state.get('world', {}).get('current_location'),
            "inventory": player.get('inventory', []),
            "gold": player.get('gold', 0)
        }

    def add_item(self, args: Dict) -> Dict[str, Any]:
        """添加物品"""
        item_id = args['item_id']
        quantity = args.get('quantity', 1)

        player = self.game_state.setdefault('player', {})
        inventory = player.setdefault('inventory', [])

        # 查找已存在的物品
        existing = next((item for item in inventory if item['id'] == item_id), None)

        if existing:
            existing['quantity'] += quantity
        else:
            inventory.append({
                "id": item_id,
                "name": item_id,
                "quantity": quantity
            })

        return {
            "success": True,
            "message": f"获得了 {quantity} 个 {item_id}"
        }

    def remove_item(self, args: Dict) -> Dict[str, Any]:
        """移除物品"""
        item_id = args['item_id']
        quantity = args.get('quantity', 1)

        inventory = self.game_state.get('player', {}).get('inventory', [])
        existing = next((item for item in inventory if item['id'] == item_id), None)

        if not existing:
            return {"success": False, "message": f"背包中没有 {item_id}"}

        if existing['quantity'] < quantity:
            return {"success": False, "message": f"{item_id} 数量不足"}

        existing['quantity'] -= quantity
        if existing['quantity'] == 0:
            inventory.remove(existing)

        return {"success": True, "message": f"失去了 {quantity} 个 {item_id}"}

    def update_hp(self, args: Dict) -> Dict[str, Any]:
        """更新HP"""
        change = args['change']
        reason = args.get('reason', '')

        player = self.game_state.setdefault('player', {})
        old_hp = player.get('hp', 100)
        max_hp = player.get('max_hp', 100)

        new_hp = max(0, min(max_hp, old_hp + change))
        player['hp'] = new_hp

        result = {
            "old_hp": old_hp,
            "new_hp": new_hp,
            "change": change,
            "reason": reason
        }

        if new_hp == 0:
            result["status"] = "死亡"
        elif new_hp < max_hp * 0.3:
            result["status"] = "危险"
        else:
            result["status"] = "正常"

        return result

    def roll_check(self, args: Dict) -> Dict[str, Any]:
        """技能检定"""
        import random

        skill = args['skill']
        dc = args['dc']
        modifier = args.get('modifier', 0)
        advantage = args.get('advantage', False)

        if advantage:
            roll1 = random.randint(1, 20)
            roll2 = random.randint(1, 20)
            roll = max(roll1, roll2)
            detail = f"优势检定: {roll1}, {roll2} -> {roll}"
        else:
            roll = random.randint(1, 20)
            detail = f"检定: {roll}"

        total = roll + modifier
        success = total >= dc

        return {
            "skill": skill,
            "roll": roll,
            "modifier": modifier,
            "total": total,
            "dc": dc,
            "success": success,
            "detail": detail,
            "result": "成功!" if success else "失败!"
        }

    def set_location(self, args: Dict) -> Dict[str, Any]:
        """设置位置"""
        location_id = args['location_id']
        description = args.get('description', '')

        world = self.game_state.setdefault('world', {})
        old_location = world.get('current_location', '未知')
        world['current_location'] = location_id

        # 记录到日志
        logs = self.game_state.setdefault('logs', [])
        logs.append(f"从 {old_location} 移动到 {location_id}")

        return {
            "success": True,
            "old_location": old_location,
            "new_location": location_id,
            "description": description
        }
```

### 4.2 游戏引擎（集成 Tool Use）

**文件**: `web/backend/game/game_engine.py`

```python
from anthropic import Anthropic
from typing import Dict, Any, List
import os
import json
from .game_tools import GAME_TOOLS, GameToolExecutor

class GameEngine:
    """游戏引擎 - 使用 Anthropic SDK Tool Use"""

    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv("LITELLM_MASTER_KEY"),
            base_url="http://localhost:4000"
        )
        self.model = "deepseek"

    async def process_turn(
        self,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """处理游戏回合"""

        # 构建系统提示词
        system_prompt = self._build_system_prompt(game_state)

        # 构建用户消息
        user_message = self._build_user_message(player_action, game_state)

        # 初始化工具执行器
        tool_executor = GameToolExecutor(game_state)

        # 调用 Anthropic API with tools
        messages = [{"role": "user", "content": user_message}]

        while True:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                system=system_prompt,
                messages=messages,
                tools=GAME_TOOLS  # 传入工具定义
            )

            # 检查是否有工具调用
            if response.stop_reason == "tool_use":
                # 处理工具调用
                tool_results = []

                for content_block in response.content:
                    if content_block.type == "tool_use":
                        # 执行工具
                        tool_name = content_block.name
                        tool_input = content_block.input

                        result = tool_executor.execute_tool(tool_name, tool_input)

                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": content_block.id,
                            "content": json.dumps(result)
                        })

                # 将助手消息和工具结果添加到对话历史
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            else:
                # 没有更多工具调用，返回最终响应
                break

        # 提取旁白文本
        narration = ""
        for block in response.content:
            if block.type == "text":
                narration += block.text

        # 更新回合数
        game_state['turn_number'] = game_state.get('turn_number', 0) + 1

        return {
            "narration": narration,
            "state": game_state
        }

    async def process_turn_stream(
        self,
        player_action: str,
        game_state: Dict[str, Any]
    ):
        """流式处理游戏回合"""

        system_prompt = self._build_system_prompt(game_state)
        user_message = self._build_user_message(player_action, game_state)
        tool_executor = GameToolExecutor(game_state)

        messages = [{"role": "user", "content": user_message}]

        # 使用流式 API
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=2000,
            system=system_prompt,
            messages=messages,
            tools=GAME_TOOLS
        ) as stream:
            # 逐步输出文本
            async for event in stream:
                if event.type == "text":
                    yield {
                        "type": "narration",
                        "content": event.text
                    }

                elif event.type == "tool_use":
                    # 执行工具
                    result = tool_executor.execute_tool(
                        event.name,
                        event.input
                    )

                    yield {
                        "type": "tool_call",
                        "tool": event.name,
                        "input": event.input,
                        "result": result
                    }

        # 更新回合数
        game_state['turn_number'] = game_state.get('turn_number', 0) + 1

        yield {
            "type": "complete",
            "state": game_state
        }

    def _build_system_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建系统提示词"""
        return f"""你是一个单人跑团游戏的游戏主持人（DM）。

世界设定:
{game_state.get('world', {}).get('theme', '奇幻世界')}

当前状态:
- 位置: {game_state.get('world', {}).get('current_location', '未知')}
- 回合数: {game_state.get('turn_number', 0)}

你的职责:
1. 描述场景和环境（生动且富有细节）
2. 管理NPC互动和对话
3. 处理玩家行动的后果
4. 使用工具调用来:
   - 修改游戏状态（add_item, remove_item, update_hp）
   - 进行技能检定（roll_check）
   - 管理位置（set_location）
5. 提供2-3个有趣的行动建议

响应格式要求:
1. 旁白部分: 描述场景和结果
2. 工具调用: 使用提供的工具更新状态
3. 建议: 给玩家2-3个行动选项
"""

    def _build_user_message(
        self,
        player_action: str,
        game_state: Dict[str, Any]
    ) -> str:
        """构建用户消息"""
        context = []

        # 玩家状态
        player = game_state.get('player', {})
        context.append(f"玩家状态: HP {player.get('hp', 100)}/{player.get('max_hp', 100)}")

        # 当前任务
        quests = game_state.get('active_quests', [])
        if quests:
            context.append(f"当前任务: {quests[0].get('title', '无')}")

        # 最近事件
        recent_logs = game_state.get('logs', [])[-3:]
        if recent_logs:
            context.append("最近事件:")
            for log in recent_logs:
                context.append(f"  - {log}")

        context_str = "\n".join(context)

        return f"""上下文:
{context_str}

玩家行动:
{player_action}

请作为游戏主持人处理这个行动，使用必要的工具调用来更新游戏状态。
"""
```

### 4.3 API 路由（支持流式）

**文件**: `web/backend/api/game_api.py`

```python
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Dict, Any, AsyncIterator
import json

from ..game.game_engine import GameEngine

router = APIRouter(prefix="/api/game", tags=["game"])

# 全局引擎实例
game_engine = GameEngine()

class GameTurnRequest(BaseModel):
    action: str
    state: Dict[str, Any]

@router.post("/turn")
async def process_turn(request: GameTurnRequest):
    """处理游戏回合（非流式）"""
    try:
        result = await game_engine.process_turn(
            player_action=request.action,
            game_state=request.state
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/turn/stream")
async def process_turn_stream(request: GameTurnRequest):
    """处理游戏回合（流式）"""

    async def event_generator() -> AsyncIterator[str]:
        try:
            async for event in game_engine.process_turn_stream(
                player_action=request.action,
                game_state=request.state
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )
```

---

## 5. 性能优化方案

### 5.1 LLM响应缓存

**文件**: `web/backend/services/llm_cache.py`

```python
import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import sqlite3

class LLMCache:
    """LLM响应缓存"""

    def __init__(self, db_path: str, ttl_hours: int = 24):
        self.db_path = db_path
        self.ttl = timedelta(hours=ttl_hours)
        self._init_cache_table()

    def _init_cache_table(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_cache (
                cache_key TEXT PRIMARY KEY,
                prompt_hash TEXT NOT NULL,
                response_data TEXT NOT NULL,
                model TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hit_count INTEGER DEFAULT 0
            )
        """)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_llm_cache_prompt_hash ON llm_cache(prompt_hash)")
        conn.commit()
        conn.close()

    def _generate_cache_key(
        self,
        prompt: str,
        model: str,
        temperature: float,
        max_tokens: int
    ) -> str:
        key_data = f"{prompt}|{model}|{temperature}|{max_tokens}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def get(
        self,
        prompt: str,
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1000
    ) -> Optional[Dict[str, Any]]:
        cache_key = self._generate_cache_key(prompt, model, temperature, max_tokens)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT response_data, created_at
                FROM llm_cache
                WHERE cache_key = ?
            """, (cache_key,))

            row = cursor.fetchone()
            if row:
                created_at = datetime.fromisoformat(row[1])

                if datetime.now() - created_at < self.ttl:
                    cursor.execute("""
                        UPDATE llm_cache
                        SET hit_count = hit_count + 1
                        WHERE cache_key = ?
                    """, (cache_key,))
                    conn.commit()

                    return json.loads(row[0])

            return None

        finally:
            conn.close()

    def set(
        self,
        prompt: str,
        model: str,
        response: Dict[str, Any],
        temperature: float = 0.7,
        max_tokens: int = 1000
    ):
        cache_key = self._generate_cache_key(prompt, model, temperature, max_tokens)
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO llm_cache
                (cache_key, prompt_hash, response_data, model)
                VALUES (?, ?, ?, ?)
            """, (cache_key, prompt_hash, json.dumps(response), model))

            conn.commit()

        finally:
            conn.close()
```

---

## 6. 测试策略

### 6.1 单元测试

**文件**: `tests/unit/test_game_tools.py`

```python
import pytest
from web.backend.game.game_tools import GameToolExecutor

@pytest.fixture
def game_state():
    return {
        "player": {
            "hp": 100,
            "max_hp": 100,
            "inventory": []
        },
        "world": {
            "current_location": "forest"
        }
    }

def test_add_item(game_state):
    executor = GameToolExecutor(game_state)
    result = executor.add_item({"item_id": "sword", "quantity": 1})

    assert result["success"] == True
    assert len(game_state["player"]["inventory"]) == 1
    assert game_state["player"]["inventory"][0]["id"] == "sword"

def test_update_hp(game_state):
    executor = GameToolExecutor(game_state)
    result = executor.update_hp({"change": -30, "reason": "战斗受伤"})

    assert result["new_hp"] == 70
    assert result["status"] == "正常"

def test_roll_check(game_state):
    executor = GameToolExecutor(game_state)
    result = executor.roll_check({
        "skill": "力量",
        "dc": 15,
        "modifier": 3
    })

    assert "roll" in result
    assert result["roll"] >= 1 and result["roll"] <= 20
    assert "success" in result
```

### 6.2 集成测试

**文件**: `tests/integration/test_game_engine.py`

```python
import pytest
from web.backend.game.game_engine import GameEngine

@pytest.mark.asyncio
async def test_process_turn():
    engine = GameEngine()

    game_state = {
        "player": {"hp": 100, "max_hp": 100, "inventory": []},
        "world": {"current_location": "forest", "theme": "奇幻世界"},
        "turn_number": 0
    }

    result = await engine.process_turn(
        player_action="我想探索森林",
        game_state=game_state
    )

    assert "narration" in result
    assert "state" in result
    assert result["state"]["turn_number"] == 1
```

---

## 7. 实施时间表

### Week 1-2: 核心系统

**Day 1-3: 工具系统**
- [ ] 实现 `game_tools.py` (工具定义和执行器)
- [ ] 实现 `game_engine.py` (集成 Tool Use)
- [ ] 单元测试

**Day 4-7: 存档系统**
- [ ] 数据库 Schema
- [ ] `save_service.py` 实现
- [ ] API 路由
- [ ] 集成测试

**Day 8-10: 任务系统**
- [ ] 数据模型 `quest_models.py`
- [ ] `quest_generator.py` 实现
- [ ] 任务追踪逻辑

### Week 3-4: 高级功能

**Day 11-14: NPC系统**
- [ ] NPC 数据模型
- [ ] `npc_manager.py` 实现
- [ ] NPC 对话系统

**Day 15-17: 性能优化**
- [ ] LLM 缓存系统
- [ ] 性能测试
- [ ] 优化 Prompt

**Day 18-21: 流式输出**
- [ ] 流式 API 实现
- [ ] 前端集成
- [ ] SSE 测试

### Week 5-6: 测试和文档

**Day 22-28: 全面测试**
- [ ] 单元测试覆盖率 > 80%
- [ ] 集成测试
- [ ] 端到端测试

**Day 29-35: 文档和优化**
- [ ] API 文档
- [ ] 开发指南
- [ ] 性能调优

---

## 8. 关键要点

### ✅ 正确做法

1. **使用 Anthropic Python SDK 的 Tool Use**
   - 通过 `tools=GAME_TOOLS` 传入工具定义
   - SDK 自动处理工具调用循环
   - 支持流式输出

2. **通过 LiteLLM Proxy 路由**
   - 已配置完成，运行在 `localhost:4000`
   - 使用 DeepSeek V3 降低成本
   - 设置 `base_url="http://localhost:4000"`

3. **清晰的工具定义**
   - JSON Schema 格式
   - 明确的描述和参数
   - 类型验证

### ❌ 避免的错误

1. **不要使用 Claude Agent SDK**
   - Claude Agent SDK 是用于 Claude Code CLI 的
   - 不适用于自定义游戏工具

2. **不要手动解析工具调用**
   - Anthropic SDK 会自动处理
   - `response.stop_reason == "tool_use"` 时循环调用

3. **不要忽略流式支持**
   - 使用 `messages.stream()` 提供更好的用户体验
   - 支持 SSE (Server-Sent Events)

---

**文档状态**: v2.0 - 基于 Anthropic SDK 正确实现
