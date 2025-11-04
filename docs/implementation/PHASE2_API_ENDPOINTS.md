# Phase 2 游戏 API 端点文档

本文档列出了 Phase 2 实现的所有游戏相关 API 端点，基于现有的 MCP 工具封装。

## 目录

- [存档系统 API](#存档系统-api)
- [任务系统 API](#任务系统-api)
- [NPC 系统 API](#npc-系统-api)
- [DM Agent API](#dm-agent-api)

---

## 存档系统 API

### 1. 保存游戏

**端点**: `POST /api/game/save`

**请求体**:
```json
{
  "user_id": "default_user",
  "slot_id": 1,
  "save_name": "第一章完成",
  "game_state": {
    "player": {...},
    "world": {...},
    "turn_number": 10
  }
}
```

**响应**:
```json
{
  "success": true,
  "save_id": 42,
  "slot_id": 1,
  "save_name": "第一章完成",
  "message": "游戏已保存到槽位 1"
}
```

---

### 2. 获取存档列表

**端点**: `GET /api/game/saves/{user_id}`

**参数**:
- `user_id` (路径): 用户ID，默认 "default_user"

**响应**:
```json
{
  "success": true,
  "saves": [
    {
      "save_id": 42,
      "slot_id": 1,
      "save_name": "第一章完成",
      "metadata": {
        "turn_number": 10,
        "location": "森林",
        "hp": 80,
        "max_hp": 100
      },
      "screenshot_url": null,
      "created_at": "2025-11-03T12:00:00",
      "updated_at": "2025-11-03T14:30:00"
    }
  ]
}
```

---

### 3. 加载存档

**端点**: `GET /api/game/save/{save_id}`

**参数**:
- `save_id` (路径): 存档ID

**响应**:
```json
{
  "success": true,
  "game_state": {
    "player": {...},
    "world": {...},
    "turn_number": 10
  },
  "metadata": {...},
  "save_info": {
    "save_id": 42,
    "slot_id": 1,
    "save_name": "第一章完成",
    "screenshot_url": null,
    "created_at": "2025-11-03T12:00:00",
    "updated_at": "2025-11-03T14:30:00"
  }
}
```

---

### 4. 删除存档

**端点**: `DELETE /api/game/save/{save_id}`

**参数**:
- `save_id` (路径): 存档ID

**响应**:
```json
{
  "success": true,
  "message": "存档 42 已删除"
}
```

---

### 5. 获取快照列表

**端点**: `GET /api/game/save/{save_id}/snapshots`

**参数**:
- `save_id` (路径): 存档ID

**响应**:
```json
{
  "success": true,
  "snapshots": [
    {
      "snapshot_id": 101,
      "turn_number": 8,
      "created_at": "2025-11-03T13:00:00"
    },
    {
      "snapshot_id": 102,
      "turn_number": 10,
      "created_at": "2025-11-03T14:00:00"
    }
  ]
}
```

---

### 6. 获取最新自动保存

**端点**: `GET /api/game/auto-save/{user_id}`

**参数**:
- `user_id` (路径): 用户ID

**响应**:
```json
{
  "success": true,
  "auto_save_id": 201,
  "game_state": {...},
  "turn_number": 12,
  "created_at": "2025-11-03T15:00:00"
}
```

---

## 任务系统 API

### 1. 创建任务

**端点**: `POST /api/game/quests`

**请求体**:
```json
{
  "quest_id": "quest_village_rescue",
  "quest_type": "main",
  "title": "拯救村庄",
  "description": "村庄被怪物围困，需要消灭所有怪物",
  "level_requirement": 1,
  "objectives": [
    {
      "id": "obj_1",
      "description": "消灭森林狼",
      "current": 0,
      "required": 5
    },
    {
      "id": "obj_2",
      "description": "与村长对话",
      "current": 0,
      "required": 1
    }
  ],
  "rewards": {
    "exp": 100,
    "gold": 50,
    "items": [
      {
        "id": "sword_iron",
        "name": "铁剑",
        "quantity": 1
      }
    ]
  }
}
```

**响应**:
```json
{
  "success": true,
  "quest_id": "quest_village_rescue",
  "message": "任务 '拯救村庄' 创建成功"
}
```

---

### 2. 获取任务列表

**端点**: `GET /api/game/quests?status={status}`

**查询参数**:
- `status` (可选): 筛选状态 - `available`, `active`, `completed`, `failed`

**响应**:
```json
{
  "success": true,
  "quests": [
    {
      "id": "quest_village_rescue",
      "type": "main",
      "title": "拯救村庄",
      "description": "村庄被怪物围困，需要消灭所有怪物",
      "status": "active",
      "objectives": [
        {
          "id": "obj_1",
          "description": "消灭森林狼",
          "current": 3,
          "required": 5,
          "completed": false
        }
      ],
      "rewards": {...}
    }
  ],
  "count": 1,
  "total": 1
}
```

---

### 3. 激活任务

**端点**: `POST /api/game/quests/{quest_id}/activate`

**参数**:
- `quest_id` (路径): 任务ID

**响应**:
```json
{
  "success": true,
  "quest_id": "quest_village_rescue",
  "message": "任务 '拯救村庄' 已激活"
}
```

---

### 4. 更新任务进度

**端点**: `PUT /api/game/quests/{quest_id}/progress`

**参数**:
- `quest_id` (路径): 任务ID

**请求体**:
```json
{
  "objective_id": "obj_1",
  "amount": 1
}
```

**响应**:
```json
{
  "success": true,
  "quest_id": "quest_village_rescue",
  "objective_id": "obj_1",
  "objective": {
    "id": "obj_1",
    "description": "消灭森林狼",
    "current": 4,
    "required": 5,
    "completed": false
  },
  "current": 4,
  "required": 5,
  "completed": false,
  "message": "目标进度: 4/5"
}
```

---

### 5. 完成任务

**端点**: `POST /api/game/quests/{quest_id}/complete`

**参数**:
- `quest_id` (路径): 任务ID

**响应**:
```json
{
  "success": true,
  "quest_id": "quest_village_rescue",
  "quest_title": "拯救村庄",
  "rewards": {
    "exp": 100,
    "gold": 50,
    "items": [
      {
        "id": "sword_iron",
        "name": "铁剑",
        "quantity": 1
      }
    ]
  },
  "message": "任务 '拯救村庄' 已完成！"
}
```

---

## NPC 系统 API

### 1. 创建 NPC

**端点**: `POST /api/game/npcs`

**请求体**:
```json
{
  "npc_id": "npc_blacksmith",
  "name": "铁匠老王",
  "role": "铁匠",
  "description": "一位经验丰富的铁匠，擅长打造武器和铠甲",
  "location": "村庄",
  "personality_traits": ["耿直", "热心"],
  "speech_style": "粗犷豪放",
  "goals": ["完成一件传说武器", "培养接班人"]
}
```

**响应**:
```json
{
  "success": true,
  "npc_id": "npc_blacksmith",
  "name": "铁匠老王",
  "message": "NPC '铁匠老王' 创建成功，位于 村庄"
}
```

---

### 2. 获取 NPC 列表

**端点**: `GET /api/game/npcs?location={location}&status={status}`

**查询参数**:
- `location` (可选): 按位置筛选
- `status` (可选): 按状态筛选 - `active`, `inactive`, `retired`

**响应**:
```json
{
  "success": true,
  "npcs": [
    {
      "id": "npc_blacksmith",
      "name": "铁匠老王",
      "role": "铁匠",
      "description": "一位经验丰富的铁匠",
      "status": "active",
      "current_location": "村庄",
      "personality": {
        "traits": ["耿直", "热心"],
        "speech_style": "粗犷豪放"
      },
      "goals": ["完成一件传说武器"],
      "memories": [],
      "relationships": []
    }
  ],
  "count": 1,
  "total": 1,
  "location": "村庄"
}
```

---

### 3. 更新 NPC 关系

**端点**: `PUT /api/game/npcs/{npc_id}/relationship`

**参数**:
- `npc_id` (路径): NPC ID

**请求体**:
```json
{
  "affinity_delta": 10,
  "trust_delta": 5,
  "reason": "帮助修理了武器"
}
```

**响应**:
```json
{
  "success": true,
  "npc_id": "npc_blacksmith",
  "npc_name": "铁匠老王",
  "affinity": 10,
  "trust": 5,
  "relationship_type": "acquaintance",
  "changes": {
    "affinity": "+0 → +10",
    "trust": "0 → 5"
  },
  "message": "与 铁匠老王 的关系更新为: acquaintance"
}
```

---

### 4. 添加 NPC 记忆

**端点**: `POST /api/game/npcs/{npc_id}/memories`

**参数**:
- `npc_id` (路径): NPC ID

**请求体**:
```json
{
  "event_type": "conversation",
  "summary": "玩家询问了关于传说武器的信息",
  "emotional_impact": 3
}
```

**响应**:
```json
{
  "success": true,
  "npc_id": "npc_blacksmith",
  "npc_name": "铁匠老王",
  "memory_count": 1,
  "message": "为 铁匠老王 添加了记忆"
}
```

---

## DM Agent API

### 1. 处理玩家行动（同步）

**端点**: `POST /api/dm/action`

**请求体**:
```json
{
  "session_id": "player_001",
  "player_action": "我向北走，进入森林",
  "game_state": {
    "player": {
      "hp": 100,
      "location": "村庄"
    },
    "world": {
      "current_location": "村庄",
      "theme": "奇幻世界"
    },
    "turn_number": 5
  }
}
```

**响应**:
```json
{
  "success": true,
  "narration": "你离开了宁静的村庄，沿着小径向北走去。不久，茂密的森林出现在你眼前。阳光透过树叶洒下斑驳的光影，空气中弥漫着泥土和青草的气息。突然，你听到前方传来低沉的咆哮声...",
  "tool_calls": [
    {
      "tool": "set_location",
      "input": {
        "location_id": "forest_entrance"
      }
    }
  ],
  "updated_state": {
    "player": {
      "hp": 100,
      "location": "forest_entrance"
    },
    "world": {
      "current_location": "forest_entrance",
      "theme": "奇幻世界"
    },
    "turn_number": 6
  },
  "turn": 6,
  "suggestions": [
    "仔细观察周围",
    "悄悄接近咆哮声",
    "准备武器"
  ]
}
```

---

### 2. WebSocket 实时交互

**端点**: `WS /api/dm/ws/{session_id}`

**客户端发送**:
```json
{
  "type": "action",
  "player_action": "我拔出剑，准备迎战",
  "game_state": {...}
}
```

**服务端流式返回**:

1. 叙述文本块:
```json
{
  "type": "narration_chunk",
  "data": {
    "text": "你迅速拔出腰间的剑，剑刃在阳光下闪烁着寒光。"
  }
}
```

2. 工具调用:
```json
{
  "type": "tool_call",
  "data": {
    "tool": "roll_check",
    "input": {
      "skill": "perception",
      "dc": 12
    }
  }
}
```

3. 工具结果:
```json
{
  "type": "tool_result",
  "data": {
    "tool": "roll_check",
    "result": {
      "success": true,
      "roll": 15,
      "total": 17
    }
  }
}
```

4. 完成消息:
```json
{
  "type": "complete",
  "data": {
    "narration": "完整的叙述文本...",
    "tool_calls": [...],
    "turn": 7,
    "updated_state": {...}
  }
}
```

---

### 3. 获取 DM 状态

**端点**: `GET /api/dm/state/{session_id}`

**参数**:
- `session_id` (路径): 会话ID

**响应**:
```json
{
  "success": true,
  "session_id": "player_001",
  "status": "active",
  "available_tools": [
    "mcp__game__get_player_state",
    "mcp__game__add_item",
    "mcp__game__update_hp",
    "mcp__game__roll_check",
    "mcp__game__set_location",
    "mcp__game__create_quest",
    "mcp__game__save_game"
  ]
}
```

---

### 4. 重置 DM 会话

**端点**: `POST /api/dm/reset/{session_id}`

**参数**:
- `session_id` (路径): 会话ID

**响应**:
```json
{
  "success": true,
  "message": "会话 player_001 已重置"
}
```

---

### 5. 获取可用工具列表

**端点**: `GET /api/dm/tools`

**响应**:
```json
{
  "success": true,
  "tools": [
    {
      "name": "get_player_state",
      "full_name": "mcp__game__get_player_state",
      "description": "游戏工具: get_player_state"
    },
    {
      "name": "add_item",
      "full_name": "mcp__game__add_item",
      "description": "游戏工具: add_item"
    }
  ],
  "count": 7
}
```

---

### 6. 健康检查

**端点**: `GET /api/dm/health`

**响应**:
```json
{
  "status": "ok",
  "dm_agent_initialized": true
}
```

---

## 错误响应格式

所有 API 在发生错误时都会返回以下格式：

```json
{
  "detail": "错误描述信息"
}
```

HTTP 状态码：
- `400 Bad Request`: 请求参数错误
- `404 Not Found`: 资源不存在
- `500 Internal Server Error`: 服务器内部错误

---

## 使用示例

### Python 示例

```python
import requests

# 创建任务
response = requests.post("http://localhost:8000/api/game/quests", json={
    "title": "拯救村庄",
    "description": "消灭森林狼",
    "objectives": [
        {"id": "obj_1", "description": "消灭森林狼", "required": 5}
    ],
    "rewards": {"exp": 100, "gold": 50}
})
print(response.json())

# 获取任务列表
response = requests.get("http://localhost:8000/api/game/quests?status=active")
print(response.json())

# DM 处理行动
response = requests.post("http://localhost:8000/api/dm/action", json={
    "session_id": "player_001",
    "player_action": "我向北走",
    "game_state": {...}
})
print(response.json())
```

### JavaScript 示例

```javascript
// 创建 NPC
fetch('http://localhost:8000/api/game/npcs', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    npc_id: 'npc_merchant',
    name: '商人张三',
    role: '商人',
    location: '市场'
  })
})
.then(res => res.json())
.then(data => console.log(data));

// WebSocket 连接
const ws = new WebSocket('ws://localhost:8000/api/dm/ws/player_001');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message.data);
};

ws.send(JSON.stringify({
  type: 'action',
  player_action: '我向北走',
  game_state: {...}
}));
```

---

## 注意事项

1. **会话管理**: 所有 DM Agent 操作需要提供 `session_id` 以区分不同玩家
2. **状态同步**: 客户端需要在每次请求中传入完整的 `game_state`
3. **工具调用**: DM Agent 会自动调用相应工具更新游戏状态
4. **流式输出**: 使用 WebSocket 可获得实时的叙述文本流
5. **错误处理**: 所有端点都有适当的错误处理和验证

---

## 相关文档

- [Phase 2 技术实现计划](../TECHNICAL_IMPLEMENTATION_PLAN.md)
- [Claude Agent SDK 集成指南](./CLAUDE_AGENT_SDK_IMPLEMENTATION.md)
- [存档系统实现](./PHASE2_SAVE_SYSTEM_IMPLEMENTATION.md)
- [任务系统实现](./PHASE2_QUEST_SYSTEM_IMPLEMENTATION.md)
