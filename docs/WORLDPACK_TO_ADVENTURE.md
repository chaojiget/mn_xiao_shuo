# 从WorldPack到冒险 - 完整流程指南

> 如何使用预生成的世界开始你的冒险
> 更新时间: 2025-11-06

## 🎯 概述

现在你可以：
1. 生成一个完整的WorldPack世界
2. 点击按钮直接在这个世界中开始冒险
3. 享受预设的地点、NPC、任务！

## 📝 完整流程

### 步骤1: 生成世界

1. 访问 **http://localhost:3000/worlds**
2. 点击 **"生成新世界"** 按钮
3. 填写表单：
   ```
   标题: 暗影森林
   基调: dark
   难度: normal
   地点: 10
   NPC: 15
   任务: 8
   ```
4. 点击 **"开始生成"**
5. 等待进度条完成（约60秒）
6. 自动跳转到世界详情页

### 步骤2: 查看世界详情

在世界详情页面，你可以看到：

**概览Tab:**
- 统计数据：10个地点，15个NPC，8个任务
- 世界信息：基调、难度、种子
- 任务分布：主线/支线统计

**地点Tab:**
```
迷雾森林 [forest]
坐标: (15, 23) | 3个POI | 2个NPC

古老神殿 [ruins]
坐标: (42, 18) | 5个POI | 1个NPC
```

**NPC Tab:**
```
神秘商人
角色: merchant
位置: 迷雾森林
欲望: 收集稀有物品
秘密: 曾是盗贼头目
```

**任务Tab:**
```
【主线】寻找遗物
 ○ 探索古老神殿
 ○ 解开谜题
 ○ 击败守护者
奖励: 100 exp, 50金币
```

### 步骤3: 开始冒险 ⭐

1. 在世界详情页右上角，点击 **"开始冒险"** 按钮

2. **智能进度检测**：
   - 如果检测到该世界已有游戏进度，会弹出确认对话框：
     ```
     检测到该世界的游戏进度（第 X 回合）。

     点击"确定"继续游戏
     点击"取消"重新开始
     ```
   - 选择"确定"：继续之前的进度
   - 选择"取消"：放弃进度，从头开始新游戏

3. 系统会：
   - 跳转到 `/game/play?worldId=your-world-id` （继续）
   - 或 `/game/play?worldId=your-world-id&reset=true` （重新开始）
   - 游戏页面读取URL参数
   - 根据情况恢复进度或重新初始化
   - 加载地图、任务、NPC

4. 显示"正在初始化游戏..."加载界面，几秒后进入游戏

### 步骤4: 在世界中游玩

游戏页面会显示：

**开场白（根据基调定制）:**
```
黑暗笼罩着暗影森林...
你发现自己身处迷雾森林，周围弥漫着不祥的气息...
```

**左侧边栏 - 角色状态:**
```
❤️ HP: 100/100
⚡ 体力: 100/100
📍 位置: 迷雾森林
💰 金币: 50
```

**右侧边栏 - 任务:**
```
【主线】寻找遗物
└─ 探索古老神殿 (未完成)
```

**中间区域 - 对话:**
```
[旁白] 叙事引擎
黑暗笼罩着暗影森林...你发现自己身处迷雾森林...

建议行动:
- 环顾四周
- 查看背包
- 查看任务
- 探索迷雾森林

输入框: [你的行动...]
```

### 步骤5: 开始探索

输入你的行动，例如：
```
我环顾四周，寻找线索
```

叙事引擎会根据WorldPack的内容回应：
```
[旁白] 叙事引擎
你环顾四周，发现森林中弥漫着浓雾...
不远处，你看到一个破旧的告示牌，上面写着：
"小心前方的古老神殿..."

你还注意到附近有一个人影，似乎是一位商人...
```

## 💾 进度管理机制

### 自动保存与恢复

系统会自动管理游戏进度，避免意外丢失：

**自动保存**:
- 每回合自动保存到槽位0
- 保存包含完整的GameState
- 记录worldPackId用于识别世界

**智能恢复逻辑**:
```
访问 /game/play?worldId=world-abc
    ↓
检查自动保存
    ↓
保存的worldId == URL的worldId ?
    ├─ 是 → 恢复进度（继续游戏）
    └─ 否 → 使用新WorldPack初始化
```

### 四种启动场景

**场景1: 首次进入世界**
- URL: `/game/play?worldId=world-abc`
- 无自动保存
- **行为**: 使用WorldPack初始化新游戏

**场景2: 继续同一世界**
- URL: `/game/play?worldId=world-abc`
- 自动保存的worldId = `world-abc`
- **行为**: 恢复进度，继续第N回合

**场景3: 切换到不同世界**
- URL: `/game/play?worldId=world-xyz`
- 自动保存的worldId = `world-abc` (不同)
- **行为**: 使用新WorldPack初始化

**场景4: 强制重新开始**
- URL: `/game/play?worldId=world-abc&reset=true`
- 自动保存的worldId = `world-abc`
- **行为**: 忽略保存，重新初始化

### 进度确认对话框

点击"开始冒险"时，如果检测到进度：

```javascript
// 伪代码
if (已有该世界的保存) {
  const choice = confirm(
    "检测到该世界的游戏进度（第 5 回合）。\n\n" +
    "点击"确定"继续游戏\n" +
    "点击"取消"重新开始"
  )

  if (choice) {
    // 继续: /game/play?worldId=xxx
  } else {
    // 重置: /game/play?worldId=xxx&reset=true
  }
}
```

## 🎮 游戏机制

### WorldPack转换规则

**地图生成:**
- 所有地点转换为地图节点
- 第一个地点自动设为起点（已发现）
- 其他地点初始状态：未发现
- 根据坐标自动生成地点之间的连接

**玩家初始化:**
- HP和体力根据难度设置：
  - Story模式: 150/150
  - Normal模式: 100/100
  - Hard模式: 80/80
- 初始金币同样根据难度变化
- 起始位置：第一个地点

**任务加载:**
- 所有任务初始为"未激活"状态
- 自动激活第一个主线任务
- 目标、奖励完整保留

**NPC系统:**
- 所有NPC加载到游戏中
- 保留性格、欲望、秘密
- DM可以根据这些信息生成对话

### 开场白定制

根据世界基调，开场白会有不同风格：

**Epic（史诗）:**
```
欢迎来到{世界名}！史诗般的冒险即将开始。
你站在{起点}，感受到命运的召唤...
```

**Dark（黑暗）:**
```
黑暗笼罩着{世界名}...
你发现自己身处{起点}，周围弥漫着不祥的气息...
```

**Cozy（温馨）:**
```
欢迎来到温馨的{世界名}！
你站在{起点}，阳光洒在身上，冒险即将开始！
```

**Mystery（神秘）:**
```
神秘的{世界名}向你敞开大门...
你站在{起点}，感觉这里隐藏着许多秘密...
```

**Whimsical（奇幻）:**
```
进入奇幻的{世界名}！
你出现在{起点}，周围充满了魔法和惊喜...
```

## 🔧 技术细节

### API调用流程

**1. 点击"开始冒险"按钮:**
```typescript
// 前端 - worlds/[id]/page.tsx
const handleStartAdventure = async () => {
  // 通过URL传递worldId
  router.push(`/game/play?worldId=${worldId}`)
}
```

**2. 游戏页面初始化:**
```typescript
// 前端 - game/play/page.tsx
const [worldId, setWorldId] = useState<string | null>(null)

useEffect(() => {
  // 从URL解析worldId
  const params = new URLSearchParams(window.location.search)
  const wid = params.get('worldId')
  setWorldId(wid)
}, [])

useEffect(() => {
  if (worldId !== null) {
    loadOrInitGame()  // worldId存在时，用它初始化
  }
}, [worldId])

const initGame = async (worldIdParam?: string) => {
  const response = await fetch("/api/game/init", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ worldId: worldIdParam || null }),
  })
  const data = await response.json()
  setGameState(data.state)  // 加载WorldPack转换的状态
}
```

**2. 后端处理:**
```python
# game_api.py
@router.post("/init")
async def init_game(request: InitGameRequest):
    if request.worldId:
        # 加载WorldPack
        loader = WorldLoader(db_path)
        state = loader.load_and_convert(request.worldId)

        # 定制开场白
        narration = generate_narration(world_tone, world_title)

        return {
            "success": True,
            "state": state.model_dump(),
            "narration": narration,
            "suggestions": [...]
        }
```

**3. WorldPack转换:**
```python
# world_loader.py
class WorldLoader:
    def world_pack_to_game_state(self, world_pack):
        # 转换地图
        game_map = self._convert_map(world_pack)

        # 创建玩家
        player = self._create_initial_player(world_pack)

        # 转换世界状态
        world = self._convert_world_state(world_pack)

        # 转换任务
        quests = self._convert_quests(world_pack)

        return GameState(...)
```

### 数据流转

```
WorldPack (gzip压缩JSON)
    ↓ 解压缩
WorldPack对象 (Pydantic模型)
    ↓ 转换
GameState对象
    ↓ 序列化
前端游戏状态
    ↓ 游戏进行
存档保存
```

## 💡 使用技巧

### 技巧1: 校验世界后再冒险

在点击"开始冒险"之前，先点击"校验世界"：
```
✅ 世界校验通过！无错误。
```
这确保世界数据没有问题。

### 技巧2: 创建快照备份

在开始冒险前创建快照：
```
标签: v1.0-ready-to-play
```
如果游戏中发现问题，可以回滚并重新生成。

### 技巧3: 查看任务Tab

在"任务"Tab中查看所有主线和支线：
- 主线任务有紫色标识
- 支线任务有蓝色标识
- 查看目标数量和奖励

### 技巧4: 研究NPC

在"NPC"Tab中研究角色：
- 查看NPC的欲望（可能成为任务线索）
- 查看NPC的秘密（可能触发剧情）
- 记住NPC的位置（知道去哪里找他们）

### 技巧5: 探索地图

在"地点"Tab中查看所有地点：
- 记住POI数量（探索目标）
- 查看生态类型（准备对应装备）
- 规划探索路线

## ⚠️ 注意事项

### 1. 世界状态独立

- 每次点击"开始冒险"都会创建**新的游戏状态**
- 之前的游戏进度不会保留（除非手动保存）
- 建议：使用游戏内的"保存到槽位"功能保存进度

### 2. 世界包不会被修改

- 游戏中的行动不会修改WorldPack
- WorldPack是只读的模板
- 所有变更都在GameState中

### 3. NPC和任务动态触发

- 虽然NPC和任务已预生成
- 但DM会根据情况动态触发它们
- 不是所有内容都会立即可见

### 4. 存档系统

游戏有独立的存档系统：
- 每回合自动保存（槽位0）
- 手动保存到槽位1-10
- 存档包含完整GameState

### 5. 地图探索

- 初始只发现第一个地点
- 其他地点需要通过探索发现
- DM会根据你的行动触发地点发现

## 🎯 完整示例

### 示例1: 快速开始

```bash
1. 访问 /worlds
2. 点击 "生成新世界"
   - 标题: 测试冒险
   - 基调: epic
   - 地点: 5
   - NPC: 8
   - 任务: 3
3. 等待生成（约40秒）
4. 点击 "开始冒险"
5. 在游戏中输入: "我环顾四周"
6. 开始探索！
```

### 示例2: 完整准备流程

```bash
1. 生成世界（参数见上）
2. 查看"概览"Tab - 确认世界规模
3. 查看"地点"Tab - 记住起点名称
4. 查看"NPC"Tab - 了解可能遇到的角色
5. 查看"任务"Tab - 规划主线路线
6. 点击"校验世界" - 确保无错误
7. 点击"创建快照" - 备份原始世界
8. 点击"开始冒险" - 进入游戏
9. 在游戏中输入第一个行动
10. 享受冒险！
```

## 🚀 下一步

现在你已经了解了完整流程，开始你的第一次冒险吧！

**推荐设置（第一次尝试）:**
```
标题: 我的第一个世界
基调: epic
难度: story  (更容易)
地点: 5
NPC: 8
任务: 3
```

点击"开始冒险"，输入：
```
我环顾四周，准备开始我的冒险
```

DM会引导你进入这个精彩的世界！🎮

---

## ⚠️ 故障排除

### 问题1: 500错误 - "cannot import name 'NPC'"

**症状**: 点击"开始冒险"后返回500错误

**原因**: `game_tools.py` 中缺少必要的数据模型字段

**解决方案**: 已修复以下问题：
- ✅ 添加了 `Quest.quest_id` 字段
- ✅ 添加了 `Quest.rewards` 字段
- ✅ 添加了 `GameState.turn_number` 字段
- ✅ 添加了 `GameState.metadata` 字段
- ✅ 添加了 `WorldState.theme` 字段
- ✅ 添加了 `MapNode.metadata` 字段
- ✅ 移除了对不存在的 `NPC` 类的引用

### 问题2: "'MapNode' object is not subscriptable"

**症状**: 初始化时报错 `'MapNode' object is not subscriptable`

**原因**: 代码试图用字典方式访问 Pydantic 对象

**解决方案**:
- ✅ 修改 `world_loader.py` 创建 `MapNode` 和 `MapEdge` 对象而非字典
- ✅ 修改 `game_api.py` 使用 `.name` 而非 `['name']` 访问属性

### 问题3: 游戏中显示的不是我构建的世界

**症状**: 点击"开始冒险"后，游戏显示的是默认世界，而不是WorldPack

**原因**:
1. URL中没有传递 `worldId` 参数
2. 游戏页面没有读取 `worldId` 参数
3. 加载了自动保存而不是WorldPack

**解决方案**:
- ✅ 修改世界详情页，通过URL传递worldId
- ✅ 修改游戏页面，从URL读取worldId
- ✅ 有worldId时优先使用WorldPack（忽略自动保存）

**验证方法**:
1. 检查URL是否包含 `?worldId=world-xxx`
2. 打开浏览器控制台，查看日志：
   ```
   [GamePlay] 使用WorldPack初始化: world-xxx
   ```
3. 检查Toast通知中的开场白是否包含世界标题

### 测试脚本

**后端集成测试**:
```bash
uv run python tests/integration/test_world_to_adventure.py
```

**前端端到端测试**:
参考 `tests/e2e/test_world_to_game_ui.md`

---

### 问题4: 每次刷新都重新初始化，丢失进度

**症状**: 刷新页面或重新进入游戏后，进度丢失，从第0回合开始

**原因**:
1. 旧版本的逻辑：有worldId就总是重新初始化
2. 没有检查保存的worldId是否与当前worldId相同

**解决方案** (已修复):
- ✅ 添加智能进度检测逻辑
- ✅ 比对保存的worldId与URL中的worldId
- ✅ 相同世界优先恢复进度
- ✅ 添加 `?reset=true` 参数支持强制重置

**验证方法**:
1. 在世界中游玩几个回合
2. 刷新页面
3. 应该看到 `[GamePlay] 恢复游戏进度` 而不是 `使用WorldPack初始化`
4. Toast显示"进度已恢复，继续第X回合的冒险"

---

**文档版本**: 1.2
**更新时间**: 2025-11-06
**作者**: Claude Code
