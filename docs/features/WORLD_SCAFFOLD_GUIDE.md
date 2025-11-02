# 世界脚手架系统使用指南

## 概述

世界脚手架系统是一个用于AI小说生成的完整世界管理解决方案。它允许你：

1. **预生成世界框架**：一次性生成世界、区域、地点、派系等
2. **逐步细化**：在运行时根据玩家探索逐步细化场景细节
3. **保持一致性**：所有细化的内容会固化为Canon（正典），确保世界状态一致
4. **丰富描写**：通过多Pass流水线生成具有画面感的叙事文本

## 核心概念

### 1. 世界层次结构

```
World（世界）
├── Regions（区域）
│   ├── Locations（地点）
│   │   ├── POIs（兴趣点）
│   │   └── Detail Layers（细化层）
│   └── ...
├── Factions（派系）
├── Items（物品）
└── Creatures（生物）
```

### 2. 细化等级（Detail Level）

- **Level 0**：轮廓（只有基本信息）
- **Level 1**：基础（添加几何、感官）
- **Level 2**：详细（添加可供性、镜头）
- **Level 3**：完全细化（包含所有细节）

### 3. 多Pass细化流水线

当玩家进入一个场景时，系统会依次执行：

1. **结构草稿（Structure Pass）**
   - 生成环境总述
   - 构图层次（远景→中景→特写）
   - 主要可互动物
   - 危险/悬念点

2. **感官增益（Sensory Pass）**
   - 视觉节点
   - 听觉节点
   - 嗅觉节点
   - 触觉节点
   - 温度节点

3. **可供性提取（Affordance Pass）**
   - 可执行动作列表
   - 每个动作的前提条件
   - 风险提示
   - 预期结果

4. **镜头语言（Cinematic Pass）**
   - 镜头切换序列
   - 节奏控制
   - 句长建议

## 快速开始

### 1. 生成世界

#### 方法A：通过前端UI

1. 访问 `http://localhost:3000/world`
2. 点击"创建新世界"
3. 填写表单：
   - 小说ID：`novel-001`
   - 主题：`dark survival`
   - 基调：`冷冽压抑`
   - 小说类型：`玄幻/仙侠`
4. 点击"生成世界"

#### 方法B：通过API

```bash
curl -X POST http://localhost:8000/api/world/generate \
  -H "Content-Type: application/json" \
  -d '{
    "novelId": "novel-001",
    "theme": "dark survival",
    "tone": "冷冽压抑",
    "novelType": "xianxia",
    "numRegions": 5,
    "locationsPerRegion": 8,
    "poisPerLocation": 5
  }'
```

### 2. 浏览世界

```bash
# 获取世界信息
curl http://localhost:8000/api/world/by-novel/novel-001

# 获取区域列表
curl http://localhost:8000/api/world/scaffold/{world_id}/regions

# 获取地点列表
curl http://localhost:8000/api/world/region/{region_id}/locations
```

### 3. 细化场景

当玩家进入某个地点时，触发细化：

```python
# 在游戏引擎中
async def enter_location(location_id: str, turn: int):
    # 调用细化接口
    result = await refine_location(
        location_id=location_id,
        turn=turn,
        target_detail_level=2,
        passes=["structure", "sensory", "affordance", "cinematic"]
    )

    # 使用结果
    narrative_text = result.narrative_text  # 叙事文本
    affordances = result.affordances  # 可做之事

    # 显示给玩家
    print(narrative_text)
    print("\n可执行动作:")
    for aff in affordances:
        print(f"- {aff['verb']}{aff['object']}")
```

### 4. 提取可供性（运行时）

```bash
curl -X POST http://localhost:8000/api/world/location/{location_id}/affordances \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "loc-001",
    "character_state": {
      "attributes": {"力量": 5, "察觉": 3},
      "inventory": ["撬棍", "火把"]
    }
  }'
```

响应：

```json
{
  "affordances": [
    {
      "verb": "撬",
      "object": "木门",
      "requirement": {"item": "撬棍"},
      "risk": "可能损坏门锁",
      "expected_outcome": "打开门，进入内部"
    }
  ],
  "suggested_actions": [
    "撬木门",
    "搜寻油罐",
    "攀爬破梯"
  ]
}
```

## 集成到游戏流程

### 游戏引擎集成示例

```python
# web/backend/game_engine.py

from scene_refinement import SceneRefinement
from world_db import WorldDatabase

class GameEngine:
    def __init__(self, llm_backend, world_db: WorldDatabase):
        self.llm = llm_backend
        self.world_db = world_db
        self.scene_refinement = SceneRefinement(llm_backend, world_db)

    async def enter_location(self, location_id: str, turn: int, character_state: dict):
        """玩家进入地点"""

        # 1. 获取地点信息
        location = self.world_db.get_location(location_id)

        # 2. 如果细化等级不足，触发细化
        if location.detail_level < 2:
            result = await self.scene_refinement.refine_location(
                request={
                    "location_id": location_id,
                    "turn": turn,
                    "target_detail_level": 2
                },
                world_style=self.get_world_style(location)
            )

            # 3. 更新访问记录
            location.visit_count += 1
            location.last_visited_turn = turn
            if location.first_visited_turn is None:
                location.first_visited_turn = turn
            self.world_db.update_location(location)

            # 4. 返回叙事文本和可供性
            return {
                "narrative": result.narrative_text,
                "affordances": result.affordances
            }
        else:
            # 5. 已细化过，直接读取
            layers = self.world_db.get_detail_layers("location", location_id)
            affordances = await self.scene_refinement.extract_affordances({
                "location_id": location_id,
                "character_state": character_state
            })

            return {
                "narrative": None,  # 可从layers重新生成
                "affordances": affordances.affordances
            }

    def get_world_style(self, location):
        """获取世界风格"""
        region = self.world_db.get_region(location.region_id)
        world = self.world_db.get_world(region.world_id)
        return world.style_bible.dict()
```

### 前端UI集成

在聊天界面显示可供性chips：

```tsx
// components/chat/message-list.tsx

import { Badge } from "@/components/ui/badge"

function ChatMessage({ message }) {
  return (
    <div>
      {/* 叙事文本 */}
      <p>{message.narrative}</p>

      {/* 可供性chips */}
      {message.affordances && (
        <div className="mt-4 flex flex-wrap gap-2">
          {message.affordances.map((aff, i) => (
            <Badge
              key={i}
              variant="outline"
              className="cursor-pointer hover:bg-accent"
              onClick={() => handleAction(aff)}
            >
              {aff.verb}{aff.object}
              {aff.risk && " ⚠️"}
            </Badge>
          ))}
        </div>
      )}
    </div>
  )
}
```

## 数据库Schema

### 核心表

1. **world_scaffolds**：世界元数据
2. **regions**：区域
3. **locations**：地点
4. **pois**：兴趣点
5. **detail_layers**：细化层（存储细化结果）
6. **factions**：派系
7. **world_items**：物品
8. **creatures**：生物

### 初始化数据库

```bash
# 执行Schema
sqlite3 data/sqlite/novel.db < schema_world_scaffold.sql
```

## API参考

### 世界管理

- `POST /api/world/generate`：生成世界
- `GET /api/world/scaffold/{world_id}`：获取世界
- `GET /api/world/by-novel/{novel_id}`：根据小说ID获取世界
- `PUT /api/world/scaffold/{world_id}`：更新世界

### 区域管理

- `GET /api/world/scaffold/{world_id}/regions`：获取区域列表
- `GET /api/world/region/{region_id}`：获取单个区域
- `POST /api/world/region/generate`：生成区域

### 地点管理

- `GET /api/world/region/{region_id}/locations`：获取地点列表
- `GET /api/world/location/{location_id}`：获取单个地点
- `POST /api/world/location/generate`：生成地点
- `PUT /api/world/location/{location_id}`：更新地点

### 场景细化

- `POST /api/world/location/{location_id}/refine`：细化地点
- `POST /api/world/location/{location_id}/affordances`：提取可供性

### 派系管理

- `GET /api/world/scaffold/{world_id}/factions`：获取派系列表

## 最佳实践

### 1. 预生成策略

- **起始区域**：详细生成（包含地点和POI）
- **远处区域**：只生成轮廓，留待探索时细化
- **关键地点**：提前细化到Level 2-3
- **普通地点**：保持Level 0，按需细化

### 2. 细化时机

- **首次进入**：触发完整细化（4个Pass）
- **再次访问**：只重新生成可供性（基于角色状态）
- **重要节点**：手动提升细化等级到Level 3

### 3. Canon锁定策略

- **发布前**：status=draft，允许修改
- **发布后**：status=published，锁定关键设定
- **关键剧情点**：canon_locked=true，禁止修改

### 4. 性能优化

- 使用`detail_level`避免重复细化
- 细化结果写入`detail_layers`表，支持快速检索
- 批量生成时使用`/api/world/scaffold/{world_id}/generate-all`

## 故障排查

### 问题1：生成的内容与设定不符

**原因**：模型没有正确读取世界风格圣经

**解决**：
1. 检查`world_scaffolds.style_bible`字段是否正确
2. 在细化时确保传入了`world_style`参数
3. 调整prompt，强化风格约束

### 问题2：细化后内容重复

**原因**：没有检查`detail_level`

**解决**：
```python
if location.detail_level >= target_detail_level:
    # 跳过细化，直接读取已有layers
    return existing_layers
```

### 问题3：可供性不合理

**原因**：没有根据角色状态过滤

**解决**：
```python
# 提取可供性时传入角色状态
result = await extract_affordances({
    "location_id": location_id,
    "character_state": {
        "attributes": {"力量": 5},
        "inventory": ["撬棍"]
    }
})
```

## 下一步

1. **向量检索**：将细化层存入向量数据库，支持语义检索
2. **冲突检测**：自动检测Canon冲突（如重名、关系矛盾）
3. **版本控制**：支持回滚、差异对比
4. **协作编辑**：多人同时编辑世界，冲突合并
5. **导出功能**：导出为Markdown/JSON/Wiki格式

## 相关文档

- `schema_world_scaffold.sql`：完整数据库Schema
- `web/backend/world_models.py`：数据模型定义
- `web/backend/world_generator.py`：世界生成逻辑
- `web/backend/scene_refinement.py`：场景细化流水线
- `web/backend/world_api.py`：REST API接口
- `web/frontend/app/world/page.tsx`：前端世界管理页面
