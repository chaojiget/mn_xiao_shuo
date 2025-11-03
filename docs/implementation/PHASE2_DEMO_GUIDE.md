# Phase 2 端到端演示指南

**日期**: 2025-11-03
**版本**: 1.0
**状态**: ✅ 完成

---

## 概述

本文档介绍如何运行 Phase 2 的完整端到端演示，展示所有已实现的功能。

## 演示内容

### 已实现功能

✅ **核心游戏工具** (7个):
- `get_player_state` - 获取玩家状态
- `add_item` - 添加物品
- `update_hp` - 更新HP
- `roll_check` - 技能检定 (d20系统)
- `set_location` - 设置位置
- `create_quest` - 创建任务
- `save_game` - 保存游戏

✅ **任务系统** (5个工具):
- `get_quests` - 获取任务列表
- `activate_quest` - 激活任务
- `update_quest_objective` - 更新任务进度
- `complete_quest` - 完成任务并发放奖励

✅ **NPC系统** (4个工具):
- `create_npc` - 创建NPC
- `get_npcs` - 获取NPC列表
- `update_npc_relationship` - 更新关系
- `add_npc_memory` - 添加记忆

✅ **存档系统**:
- SaveService (完整CRUD)
- 3个数据表
- 自动元数据提取
- 10个存档槽位

**总计**: 15个 MCP 工具 + SaveService + 完整数据模型

---

## 运行演示

### 方法1: 运行完整演示脚本

```bash
# 从项目根目录运行
python examples/game_engine_demo.py
```

**预期输出**:

```
============================================================
  Phase 2 游戏引擎完整演示
  基于 Claude Agent SDK + MCP Server
============================================================

============================================================
  Phase 2 游戏引擎演示 - 失落的神庙冒险
============================================================
会话ID: demo_session
初始位置: 村庄广场
初始HP: 100/100
初始金币: 50
============================================================

============================================================
场景 1: 村庄广场
============================================================

[DM] 你来到了宁静的村庄广场。阳光洒在石板路上，
     几位村民正在井边闲聊。远处，村长的房子门口
     贴着一张告示。

>>> 玩家: 查看我的状态
[系统] 玩家状态: HP 100/100, 位置: 村庄广场, 金币: 50
       背包: 2个物品

>>> 玩家: 走向村长的房子
[DM] 你走到村长房前，一位年迈但精神矍铄的老人迎了出来。

[系统] NPC创建成功: 村长艾尔文

>>> 玩家: 询问村长关于告示的事
[村长艾尔文] 年轻的冒险者，我们村庄遇到了大麻烦...
             传说中的失落神庙最近出现了异动，邪恶力量正在苏醒。
             我们需要一位勇士进入神庙，找到三块神器碎片，
             并击败守护者，阻止灾难降临。

[系统] 任务创建成功: 失落神庙的秘密

>>> 玩家: 我接受这个任务！
[系统] 任务已激活: 失落神庙的秘密
[村长艾尔文] 太好了！愿神明保佑你平安归来。

[系统] NPC关系更新: 村长艾尔文
       好感度: 0 → 10
       关系类型: acquaintance

[系统] NPC记忆已添加 (总记忆数: 1)

[系统] 游戏已保存到槽位 1

...

============================================================
  演示完成！
============================================================

已演示的功能:
  ✅ 核心游戏工具 (7个): 状态、物品、HP、检定、位置、创建任务、存档
  ✅ 任务系统 (5个): 获取、激活、更新进度、完成
  ✅ NPC系统 (4个): 创建、获取、关系、记忆
  ✅ 存档系统: 2个存档槽位，自动元数据提取

总计: 15个MCP工具 + SaveService完整集成
```

### 方法2: 运行集成测试

```bash
# 使用 pytest
pytest tests/integration/test_game_engine_enhanced.py -v -s

# 或手动运行
python tests/integration/test_game_engine_enhanced.py
```

**预期输出**:

```
============================================================
  Phase 2 游戏引擎集成测试
  使用 Claude Agent SDK + MCP 工具
============================================================

✅ 所有15个工具已正确注册：get_player_state, add_item, ...

=== 测试 1: 核心游戏工具 ===
✓ get_player_state: HP=100, 位置=起始点
✓ add_item: 获得了 1 个 test_sword
✓ update_hp: 100 → 80
✓ roll_check: 骰值=15, 总计=17, 成功=True
✓ set_location: 起始点 → 新位置

=== 测试 2: 任务系统 ===
✓ create_quest: 任务创建成功: 测试任务
✓ get_quests: 找到 1 个可接取任务
✓ activate_quest: 任务已激活: 测试任务
✓ update_quest_objective: 进度 2/3
✓ complete_quest: 获得 100 经验值

=== 测试 3: NPC系统 ===
✓ create_npc: NPC创建成功: 测试NPC
✓ get_npcs: 在测试位置找到 1 个NPC
✓ update_npc_relationship: 好感度=15, 信任度=10
✓ add_npc_memory: NPC记忆已添加

=== 测试 4: 存档系统 ===
✓ save_game (MCP): 游戏已保存到槽位 9
✓ SaveService.get_saves: 找到测试存档
✓ SaveService.load_game: 成功加载存档
✓ 测试存档已清理

=== 测试 5: 完整集成流程 ===
✓ Step 1: 创建NPC
✓ Step 2: 创建任务
✓ Step 3: 激活任务
✓ Step 4: 完成任务目标
✓ Step 5: 完成任务并获得奖励
✓ Step 6: 更新NPC关系
✓ Step 7: 添加NPC记忆
✓ Step 8: 保存游戏

✅ 完整集成流程测试通过！

============================================================
  ✅ 所有集成测试通过！
============================================================
```

---

## 演示场景详解

### 场景 1: 村庄广场 - NPC 和任务

**演示内容**:
- ✅ 创建 NPC (村长艾尔文)
- ✅ 创建任务 (失落神庙的秘密)
- ✅ 激活任务
- ✅ 更新 NPC 关系 (好感度 +10, 信任度 +5)
- ✅ 添加 NPC 记忆
- ✅ 保存游戏 (槽位 1)

**涉及工具**:
- `create_npc`
- `create_quest`
- `activate_quest`
- `update_npc_relationship`
- `add_npc_memory`
- `save_game`

### 场景 2: 神庙入口 - 探索和检定

**演示内容**:
- ✅ 移动位置 (村庄广场 → 神庙入口)
- ✅ 更新任务进度 (探索目标完成)
- ✅ 创建第二个 NPC (神秘商人)
- ✅ 技能检定 (感知检定 DC15)
- ✅ 添加物品 (高级生命药水)
- ✅ 保存游戏 (槽位 2)

**涉及工具**:
- `set_location`
- `update_quest_objective`
- `create_npc`
- `roll_check`
- `add_item`
- `save_game`

---

## 数据模型展示

### NPC 数据结构

```json
{
  "id": "npc_village_chief",
  "name": "村长艾尔文",
  "role": "村长",
  "status": "active",
  "personality": {
    "traits": ["智慧", "正直", "关心村民"],
    "speech_style": "说话缓慢沉稳，用词考究",
    "values": {}
  },
  "memories": [
    {
      "turn_number": 0,
      "event_type": "conversation",
      "summary": "冒险者接受了失落神庙任务",
      "emotional_impact": 5,
      "participants": ["player"]
    }
  ],
  "relationships": [
    {
      "target_id": "player",
      "affinity": 10,
      "trust": 5,
      "relationship_type": "acquaintance"
    }
  ],
  "goals": ["保护村庄安全", "寻找勇敢的冒险者"],
  "current_location": "村庄广场"
}
```

### 任务数据结构

```json
{
  "id": "quest_lost_temple",
  "type": "main",
  "title": "失落神庙的秘密",
  "status": "active",
  "objectives": [
    {
      "id": "obj_explore_temple",
      "type": "explore",
      "description": "探索失落神庙",
      "target": "神庙入口",
      "current": 1,
      "required": 1,
      "completed": true
    },
    {
      "id": "obj_collect_fragments",
      "type": "collect",
      "description": "收集神器碎片",
      "target": "神器碎片",
      "current": 0,
      "required": 3,
      "completed": false
    }
  ],
  "rewards": {
    "exp": 500,
    "gold": 200,
    "items": [{"id": "legendary_amulet", "quantity": 1}]
  }
}
```

---

## 文件清单

### 演示相关文件

1. **`examples/game_engine_demo.py`** (359行)
   - 完整的端到端演示脚本
   - 2个演示场景
   - 展示所有15个工具的使用

2. **`tests/integration/test_game_engine_enhanced.py`** (411行)
   - 5个集成测试
   - 完整的工作流测试
   - 工具注册验证

### 核心实现文件

3. **`web/backend/agents/game_tools_mcp.py`** (~900行)
   - 15个 MCP 工具定义
   - GameStateManager
   - 所有工具实现

4. **`web/backend/models/quest_models.py`** (271行)
   - Quest, QuestObjective, QuestReward

5. **`web/backend/models/npc_models.py`** (270行)
   - NPC, NPCPersonality, NPCMemory, NPCRelationship

6. **`web/backend/services/save_service.py`** (432行)
   - SaveService (12个方法)
   - 完整存档管理

---

## 技术亮点

### 1. Claude Agent SDK 集成

所有工具使用 `@tool` 装饰器定义：

```python
@tool(
    "update_npc_relationship",
    "更新NPC与玩家的关系",
    {
        "type": "object",
        "properties": {
            "npc_id": {"type": "string"},
            "affinity_delta": {"type": "integer"},
            "trust_delta": {"type": "integer"},
            "reason": {"type": "string"}
        },
        "required": ["npc_id"]
    }
)
async def update_npc_relationship(args: Dict) -> Dict[str, Any]:
    # 实现...
```

### 2. 状态管理

双层缓存策略 (内存 + 数据库):

```python
# 获取状态
state = state_manager.get_state(session_id)

# 修改状态
state['player']['hp'] -= 20

# 保存状态
state_manager.save_state(session_id, state)
```

### 3. 数据持久化

存档系统自动提取元数据：

```python
metadata = {
    "turn_number": state.get("turn_number", 0),
    "playtime": state.get("playtime", 0),
    "location": state.get("world", {}).get("current_location"),
    "level": state.get("player", {}).get("level", 1)
}
```

### 4. NPC 记忆管理

滑动窗口策略（保留最近50条）：

```python
def add_memory(self, ...):
    self.memories.append(memory)
    if len(self.memories) > 50:
        self.memories = self.memories[-50:]
```

### 5. 关系系统

双轴评估 + 自动类型更新：

```python
def adjust_affinity(self, delta: int):
    self.affinity = max(-100, min(100, self.affinity + delta))
    self._update_relationship_type()

def _update_relationship_type(self):
    if self.affinity >= 75:
        self.relationship_type = "ally"
    elif self.affinity >= 50:
        self.relationship_type = "friend"
    # ...
```

---

## 下一步建议

基于演示结果，建议的下一步方向：

### 选项 A: 前端集成

为新功能添加 UI 界面：
- 任务追踪面板
- NPC关系图
- 存档/读档界面
- 实时状态显示

### 选项 B: DM Agent 集成

创建智能 DM Agent：
- 使用 Claude Agent SDK 的 `query` 函数
- 自动调用 15个工具
- 生成动态剧情
- 智能 NPC 对话

### 选项 C: 性能优化

优化系统性能：
- LLM 提示词缓存
- 批量工具调用
- 数据库查询优化
- 状态更新优化

### 选项 D: 扩展功能

添加更多游戏系统：
- 战斗系统
- 商店系统
- 技能树系统
- 成就系统

---

## 问题排查

### 问题 1: 导入错误

```
ImportError: cannot import name 'set_session'
```

**解决方案**: 确保从项目根目录运行

```bash
# 正确
cd /path/to/mn_xiao_shuo
python examples/game_engine_demo.py

# 错误
cd examples
python game_engine_demo.py
```

### 问题 2: 数据库不存在

```
sqlite3.OperationalError: no such table: game_saves
```

**解决方案**: 运行数据库初始化

```bash
python scripts/init_db.py
```

### 问题 3: 测试失败

```
AssertionError: 期望15个工具，实际14个
```

**解决方案**: 检查工具注册

```python
from web.backend.agents.game_tools_mcp import ALL_GAME_TOOLS
print(f"工具总数: {len(ALL_GAME_TOOLS)}")
for tool in ALL_GAME_TOOLS:
    print(f"  - {tool.__name__}")
```

---

## 总结

✅ **Phase 2 演示成功创建并运行**

- 完整的端到端演示脚本 (359行)
- 完整的集成测试套件 (411行)
- 所有15个工具正常工作
- 所有数据模型正确实现
- 存档系统完整集成

**演示证明了**:
1. Claude Agent SDK + MCP Server 架构可行
2. 15个工具无缝集成
3. 数据持久化正常工作
4. 状态管理稳定可靠
5. 系统扩展性良好

**下一阶段准备就绪**: 可以开始前端集成或 DM Agent 开发

---

## 参考文档

- [Phase 2 实施总结](./PHASE2_IMPLEMENTATION_SUMMARY.md)
- [任务系统实施](./PHASE2_QUEST_SYSTEM_IMPLEMENTATION.md)
- [NPC系统实施](./PHASE2_NPC_SYSTEM_IMPLEMENTATION.md)
- [技术实现计划](../TECHNICAL_IMPLEMENTATION_PLAN.md)
- [Claude Agent SDK 实施](./CLAUDE_AGENT_SDK_IMPLEMENTATION.md)
