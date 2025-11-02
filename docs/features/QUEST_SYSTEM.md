# 数据驱动的任务系统文档

## 📖 概述

游戏系统现在实现了完整的数据驱动任务系统,允许通过 YAML 配置文件定义任务,无需修改代码即可添加新的游戏内容。

## 🎯 核心特性

- **规则引擎**: 自动检测任务触发条件和完成状态
- **数据驱动**: YAML 配置文件定义任务,易于编辑和扩展
- **阶段管理**: 支持多阶段任务,每个阶段有独立的条件和提示
- **奖励系统**: 自动发放经验、物品、解锁地点等奖励
- **动态提示**: 根据任务进度提供上下文相关的提示

---

## 📂 文件结构

```
data/quests/
├── quest_001.yaml     # 寻找失落的钥匙
├── quest_002.yaml     # 初次探险(教程)
└── quest_XXX.yaml     # 更多任务...

web/backend/game/
├── __init__.py
└── quests.py          # 任务引擎核心代码
```

---

## 📝 任务配置格式

### 基本结构

```yaml
# 任务唯一标识
id: "quest_id_here"

# 任务标题和描述
title: "任务名称"
description: "详细描述这个任务"

# 触发条件(满足所有条件才会激活)
triggers:
  - type: "条件类型"
    param1: value1
    param2: value2

# 任务阶段
stages:
  - id: "stage_1"
    name: "阶段名称"
    description: "阶段描述"
    conditions:
      - type: "完成条件类型"
        param: value
    hints:
      - "提示文本1"
      - "提示文本2"

# 任务奖励
rewards:
  - type: "奖励类型"
    param: value

# 初始提示
initial_hints:
  - "任务相关的提示"
```

---

## 🔧 支持的条件类型

### 1. `always` - 始终满足
```yaml
triggers:
  - type: "always"  # 游戏开始就激活
```

### 2. `location` - 位置检查
```yaml
triggers:
  - type: "location"
    location: "forest"  # 玩家在森林中
```

### 3. `has_item` - 持有物品
```yaml
conditions:
  - type: "has_item"
    item_id: "cave_key"  # 拥有洞穴钥匙
```

### 4. `flag_exists` / `flag_not_exists` - 标志检查
```yaml
triggers:
  - type: "flag_not_exists"
    flag: "quest_completed"  # 任务尚未完成

conditions:
  - type: "flag_exists"
    flag: "met_npc"  # 已经见过某NPC
```

### 5. `flag_equals` - 标志值检查
```yaml
conditions:
  - type: "flag_equals"
    flag: "difficulty"
    value: "hard"
```

### 6. `turn_count` - 回合数检查
```yaml
conditions:
  - type: "turn_count"
    min: 1  # 至少1回合
    max: 10  # 最多10回合
```

### 7. `location_changed` - 位置变化
```yaml
conditions:
  - type: "location_changed"
    from: "start"  # 离开起点
```

### 8. `player_action` - 玩家输入关键词
```yaml
conditions:
  - type: "player_action"
    action_contains: ["背包", "物品", "查看"]
```

---

## 🎁 奖励类型

### 1. 经验值
```yaml
rewards:
  - type: "experience"
    value: 100
```

### 2. 物品
```yaml
rewards:
  - type: "item"
    item_id: "health_potion"
    item_name: "治疗药水"
    quantity: 2
```

### 3. 标志位
```yaml
rewards:
  - type: "flag"
    flag: "quest_001_completed"
```

### 4. 解锁地点
```yaml
rewards:
  - type: "unlock_location"
    location: "cave"
```

---

## 💡 示例任务

### 示例 1: 新手教程

`data/quests/quest_002.yaml`:

```yaml
id: "first_adventure"
title: "初次探险"
description: "熟悉周围的环境，为未来的冒险做准备。"

# 自动激活
triggers:
  - type: "always"

stages:
  - id: "look_around"
    name: "环顾四周"
    description: "观察你所在的位置"
    conditions:
      - type: "turn_count"
        min: 1
    hints:
      - "试着输入'环顾四周'来观察周围"

  - id: "check_inventory"
    name: "检查背包"
    description: "查看你拥有的物品"
    conditions:
      - type: "player_action"
        action_contains: ["背包", "物品", "查看"]
    hints:
      - "输入'查看背包'来了解你有什么"

  - id: "try_move"
    name: "尝试移动"
    description: "前往一个新地点"
    conditions:
      - type: "location_changed"
        from: "start"
    hints:
      - "试着向某个方向移动"
      - "比如'向北走'或'进入森林'"

rewards:
  - type: "experience"
    value: 20
  - type: "flag"
    flag: "tutorial_completed"
  - type: "item"
    item_id: "health_potion"
    item_name: "治疗药水"
    quantity: 2

initial_hints:
  - "这是你的第一次冒险"
  - "慢慢探索，熟悉这个世界"
```

### 示例 2: 探索任务

`data/quests/quest_001.yaml`:

```yaml
id: "find_cave_key"
title: "寻找失落的钥匙"
description: "据说在迷雾森林深处藏有一把古老的钥匙，它能打开神秘洞穴的大门。"

triggers:
  - type: "location"
    location: "start"
  - type: "flag_not_exists"
    flag: "quest_find_cave_key_completed"

stages:
  - id: "stage_1_explore"
    name: "探索森林"
    description: "前往迷雾森林探索"
    conditions:
      - type: "location"
        location: "forest"
    hints:
      - "试着向北走，进入迷雾森林"
      - "森林中可能藏有线索"

  - id: "stage_2_find_key"
    name: "找到钥匙"
    description: "在森林中找到古老的钥匙"
    conditions:
      - type: "has_item"
        item_id: "cave_key"
    hints:
      - "仔细搜索森林的每个角落"
      - "也许需要进行某种检定才能发现隐藏的物品"

rewards:
  - type: "experience"
    value: 50
  - type: "flag"
    flag: "quest_find_cave_key_completed"
  - type: "unlock_location"
    location: "cave"

initial_hints:
  - "村口的老人提到过森林中的秘密"
  - "那把钥匙据说能打开古老洞穴"
```

---

## 🚀 工作流程

### 1. 游戏引擎初始化时

```python
# web/backend/game_engine.py
from game.quests import QuestEngine

class GameEngine:
    def __init__(self, llm_client, quest_data_path=None):
        # 初始化任务引擎
        self.quest_engine = QuestEngine(quest_data_path)
        # 自动加载 data/quests/ 下的所有 .yaml 文件
```

### 2. 每个游戏回合后

```python
# 在 process_turn() 方法中
quest_events = self.quest_engine.update_quests(
    state,
    tools,
    last_player_input=request.playerInput
)

# 任务事件示例:
# ["📜 新任务激活: 寻找失落的钥匙",
#  "✅ 任务进度: 初次探险 - 环顾四周",
#  "🎉 任务完成: 初次探险",
#  "💫 获得 20 点经验",
#  "🎁 获得物品: 治疗药水 x2"]
```

### 3. 任务提示系统

```python
# 获取当前活跃任务的提示
quest_hints = self.quest_engine.get_active_quest_hints(state)

# 返回示例:
# ["[初次探险] 试着输入'环顾四周'来观察周围",
#  "[寻找钥匙] 试着向北走，进入迷雾森林"]
```

---

## 🎮 玩家体验

### 任务激活
```
你站在广场中央...

📜 新任务激活: 初次探险
```

### 任务进度
```
你向北走进了迷雾森林...

✅ 任务进度: 寻找失落的钥匙 - 探索森林

💡 提示:
  [寻找钥匙] 仔细搜索森林的每个角落
```

### 任务完成
```
你在古树下发现了一把古老的钥匙！

✅ 任务进度: 寻找失落的钥匙 - 找到钥匙
🎉 任务完成: 寻找失落的钥匙

💫 获得 50 点经验
🏁 设置标志: quest_find_cave_key_completed
🗺️ 解锁地点: cave
```

---

## 🛠️ 添加新任务的步骤

### 1. 创建 YAML 文件

在 `data/quests/` 目录下创建新的 `.yaml` 文件:

```bash
touch data/quests/quest_003.yaml
```

### 2. 编写任务配置

```yaml
id: "rescue_villager"
title: "营救村民"
description: "有村民被困在废弃矿井中，需要你的帮助"

triggers:
  - type: "flag_exists"
    flag: "met_elder"
  - type: "location"
    location: "village"

stages:
  - id: "find_mine"
    name: "找到废弃矿井"
    description: "前往村庄东边的废弃矿井"
    conditions:
      - type: "location"
        location: "old_mine"
    hints:
      - "村长说矿井在村庄东边"

  - id: "rescue"
    name: "救出村民"
    description: "找到并救出被困的村民"
    conditions:
      - type: "flag_exists"
        flag: "villager_rescued"
    hints:
      - "小心矿井里的危险"
      - "也许需要进行力量检定"

rewards:
  - type: "experience"
    value: 100
  - type: "item"
    item_id: "miners_amulet"
    item_name: "矿工的护符"
  - type: "flag"
    flag: "village_reputation_increased"

initial_hints:
  - "时间紧迫，尽快行动"
```

### 3. 重启服务器

任务系统会在服务器启动时自动加载所有配置:

```bash
# 后端会自动检测文件变化并重新加载
# 或手动重启
```

### 4. 测试任务

在游戏中满足触发条件,观察任务是否正常激活。

---

## 🔍 调试技巧

### 查看任务加载日志

后端启动时会显示:

```
[INFO] 加载任务: first_adventure - 初次探险
[INFO] 加载任务: find_cave_key - 寻找失落的钥匙
```

### 查看任务触发日志

玩家行动时:

```
[INFO] 激活任务: first_adventure
[INFO] 完成阶段: first_adventure/look_around
[INFO] 任务完成: first_adventure
```

### 常见问题

**问题**: 任务没有激活
- 检查 `triggers` 条件是否都满足
- 确认任务 `id` 唯一且未完成

**问题**: 阶段不推进
- 检查 `conditions` 是否正确
- 确认条件类型和参数拼写正确

**问题**: YAML 解析错误
- 检查缩进是否正确(使用空格,不要用Tab)
- 检查引号和特殊字符

---

## 📊 性能考虑

- **任务数量**: 支持数百个任务配置
- **检查开销**: 每回合O(N*M),N=任务数,M=条件数
- **优化建议**:
  - 已完成的任务自动跳过检查
  - 使用合理的触发条件减少无效检查

---

## 🎨 未来扩展

### 计划中的功能

- [ ] 任务依赖链(前置任务系统)
- [ ] 分支任务(多结局)
- [ ] 限时任务
- [ ] 重复任务/日常任务
- [ ] 任务失败惩罚
- [ ] 隐藏任务发现机制
- [ ] 任务难度等级
- [ ] 任务奖励选择

### DSL 脚本支持 (高级)

未来可能支持更复杂的脚本逻辑:

```python
# 任务脚本示例
if player.level >= 5 and has_completed("quest_001"):
    activate("quest_advanced")

if time.hour >= 22:
    spawn_enemy("night_creature")
```

---

**最后更新**: 2025-11-01
**当前版本**: Phase 3 - Quest System v1.0
**作者**: AI Agent System
