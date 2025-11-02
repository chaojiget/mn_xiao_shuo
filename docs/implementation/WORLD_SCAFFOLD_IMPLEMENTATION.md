# 世界脚手架系统实现总结

## 实现完成时间
2025-01-31

## 系统概述

我们实现了一套完整的**世界脚手架系统（World Scaffold System）**，用于解决AI长篇小说生成中的"世界一致性"和"叙事画面感"问题。

### 核心问题
1. ❌ **没有画面感**：AI生成的场景描写空洞、缺乏感官细节
2. ❌ **不知道做什么**：玩家进入场景后，不清楚有哪些可执行的行动
3. ❌ **世界不一致**：随机生成的内容容易自相矛盾，缺乏连贯性

### 解决方案
✅ **先搭脚手架，再逐步细化**
- 预生成世界框架（区域、地点、派系）
- 玩家探索时触发细化（结构→感官→可供性→镜头）
- 细化结果固化为Canon（正典），保证一致性

## 技术架构

### 后端（FastAPI + SQLite）

#### 1. 数据库Schema（`schema_world_scaffold.sql`）

**13张核心表**：

| 表名 | 用途 |
|------|------|
| `world_scaffolds` | 世界元数据、主题、风格圣经 |
| `regions` | 区域（生态、危险等级、旅行提示） |
| `locations` | 地点（几何、感官、可供性） |
| `pois` | 兴趣点（可交互对象） |
| `factions` | 派系（势力、关系矩阵） |
| `world_items` | 物品（稀有度、配方） |
| `creatures` | 生物（生态位、掉落） |
| `quest_hooks` | 任务钩子（随机遭遇表） |
| `detail_layers` | 细化层（存储多Pass生成结果） |
| `world_events` | 世界事件（派系变化、地点毁灭） |
| `style_vocabulary` | 风格词库（意象词、比喻模式） |
| `world_versions` | 版本控制（快照、差异） |
| `canon_conflicts` | 冲突检测（重名、关系矛盾） |

**关键设计**：
- `detail_level`（0-3）：记录地点细化等级，避免重复生成
- `canon_locked`：锁定已发布的设定，禁止修改
- `target_type + target_id`：细化层支持多类型目标（location/poi/creature）

#### 2. 数据模型（`world_models.py`）

使用 Pydantic 定义类型安全的数据模型：

```python
class WorldScaffold(BaseModel):
    id: str
    novel_id: str
    theme: str  # "dark survival"
    tone: str   # "冷冽压抑"
    style_bible: StyleBible  # 风格圣经
    status: Literal["draft", "published", "locked"]

class StyleBible(BaseModel):
    tone: str
    sensory: List[str]  # ["寒气", "盐霜", "铁锈味"]
    syntax: SyntaxPreferences
    imagery: List[str]  # 意象词库
```

#### 3. 世界生成器（`world_generator.py`）

**生成流程**：

```python
async def generate_world(request):
    # 1. 生成世界框架（主题、时间线、禁忌规则、风格圣经）
    world = await _generate_world_framework(request)

    # 2. 生成区域（biome、资源、危险等级）
    regions = await _generate_regions(world.id, count=5)

    # 3. 生成派系（目的、势力、关系矩阵）
    factions = await _generate_factions(world.id, regions)

    # 4. 生成风格词库（感官词、意象词、句式模式）
    style_vocab = await _generate_style_vocabulary(world)

    return {world, regions, factions, style_vocab}
```

**LLM Prompt策略**：
- 要求严格JSON输出（不包含markdown代码块）
- 使用风格约束（基调、感官词库）
- 保证差异性（区域危险等级梯度分布）

#### 4. 场景细化流水线（`scene_refinement.py`）

**多Pass生成**：

```
玩家进入地点
    ↓
Pass 1: 结构草稿
    - 环境总述
    - 构图层次（远景→中景→特写）
    - 主要可互动物
    - 危险/悬念
    ↓
Pass 2: 感官增益
    - 视觉节点
    - 听觉节点
    - 嗅觉/触觉/温度节点
    ↓
Pass 3: 可供性提取
    - verb + object（撬门、搜寻、攀爬）
    - requirement（前提条件）
    - risk（风险提示）
    - expected_outcome（预期结果）
    ↓
Pass 4: 镜头语言
    - 镜头切换序列
    - 节奏控制
    - 句长建议
    ↓
校验与固化
    - 写入 detail_layers 表
    - 更新 location.detail_level
    - 生成叙事文本
```

**核心代码**：

```python
async def refine_location(request, world_style):
    location = db.get_location(request.location_id)

    # 跳过已细化的
    if location.detail_level >= request.target_detail_level:
        return existing_layers

    # 执行各个Pass
    structure_layer = await _structure_pass(location, world_style)
    sensory_layer = await _sensory_pass(location, world_style)
    affordance_layer = await _affordance_pass(location, world_style)
    cinematic_layer = await _cinematic_pass(location, world_style, layers)

    # 固化
    for layer in layers:
        db.save_detail_layer(layer)

    location.detail_level = request.target_detail_level
    db.update_location(location)

    # 生成叙事文本
    narrative_text = await _generate_narrative_text(location, layers, world_style)

    return RefinementResult(...)
```

#### 5. REST API（`world_api.py`）

**主要接口**：

| 路由 | 方法 | 功能 |
|------|------|------|
| `/api/world/generate` | POST | 生成完整世界 |
| `/api/world/scaffold/{world_id}` | GET | 获取世界 |
| `/api/world/scaffold/{world_id}/regions` | GET | 获取区域列表 |
| `/api/world/region/{region_id}/locations` | GET | 获取地点列表 |
| `/api/world/location/generate` | POST | 生成地点 |
| `/api/world/location/{id}/refine` | POST | **细化地点** |
| `/api/world/location/{id}/affordances` | POST | **提取可供性** |
| `/api/world/scaffold/{world_id}/factions` | GET | 获取派系 |

**依赖注入**：

```python
# main.py
world_db = WorldDatabase(db_path)
init_world_services(world_db, llm_backend)

# world_api.py
def get_world_db() -> WorldDatabase:
    return _world_db  # 全局单例
```

### 前端（Next.js 14 + shadcn/ui）

#### 1. 世界管理页面（`app/world/page.tsx`）

**三列布局**：
- 左列：世界树（World → Regions → Locations）
- 中列：内容区（生成表单 / 地点详情）
- 右列：派系、物品、生物

#### 2. 核心组件

| 组件 | 文件 | 功能 |
|------|------|------|
| `WorldManager` | `world-manager.tsx` | 主容器，管理状态 |
| `WorldTree` | `world-tree.tsx` | 树状导航（可折叠） |
| `LocationCard` | `location-card.tsx` | 地点详情卡片 |
| `useWorld` | `use-world.ts` | 状态管理Hook |

#### 3. 关键功能

**生成世界表单**：

```tsx
<Input
  value={worldForm.theme}
  onChange={(e) => setWorldForm({...worldForm, theme: e.target.value})}
  placeholder="dark survival"
/>

<Button onClick={handleGenerateWorld}>
  {isGenerating ? "生成中..." : "生成世界"}
</Button>
```

**地点细化按钮**：

```tsx
<Button onClick={handleRefine}>
  <Zap className="mr-2 h-4 w-4" />
  细化场景
</Button>
```

**可供性chips显示**：

```tsx
{refinedData?.affordances.map(aff => (
  <Badge variant="outline">
    {aff.verb} {aff.object}
    {aff.risk && " ⚠️"}
  </Badge>
))}
```

#### 4. 状态管理（`use-world.ts`）

```typescript
export function useWorld() {
  const [currentWorld, setCurrentWorld] = useState(null)
  const [regions, setRegions] = useState([])
  const [locations, setLocations] = useState([])

  const generateWorld = async (request) => {
    const response = await fetch("/api/world/generate", {
      method: "POST",
      body: JSON.stringify(request)
    })
    const result = await response.json()
    setCurrentWorld(result.world)
    setRegions(result.regions)
  }

  const selectRegion = async (regionId) => {
    const response = await fetch(`/api/world/region/${regionId}/locations`)
    const locations = await response.json()
    setLocations(locations)
  }

  return {currentWorld, regions, locations, generateWorld, selectRegion}
}
```

## 集成到游戏流程

### 游戏引擎扩展（伪代码）

```python
class GameEngine:
    def __init__(self, llm_backend, world_db):
        self.scene_refinement = SceneRefinement(llm_backend, world_db)

    async def enter_location(self, location_id, turn, character_state):
        location = self.world_db.get_location(location_id)

        # 如果未细化，触发细化
        if location.detail_level < 2:
            result = await self.scene_refinement.refine_location({
                "location_id": location_id,
                "turn": turn,
                "target_detail_level": 2
            }, world_style)

            # 更新访问记录
            location.visit_count += 1
            location.last_visited_turn = turn
            self.world_db.update_location(location)

            return {
                "narrative": result.narrative_text,
                "affordances": result.affordances
            }

        # 已细化，直接提取可供性
        else:
            affordances = await self.scene_refinement.extract_affordances({
                "location_id": location_id,
                "character_state": character_state
            })

            return {
                "narrative": None,
                "affordances": affordances.affordances
            }
```

### 前端聊天界面集成

```tsx
function ChatMessage({message}) {
  return (
    <div>
      {/* 叙事文本 */}
      <p className="leading-relaxed">{message.narrative}</p>

      {/* 可供性chips（点击执行动作） */}
      {message.affordances && (
        <div className="mt-4 flex flex-wrap gap-2">
          {message.affordances.map(aff => (
            <Badge
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

## 实现成果

### ✅ 已完成功能

1. **数据层**
   - ✅ 13张数据库表（完整Schema）
   - ✅ Pydantic数据模型
   - ✅ WorldDatabase CRUD操作

2. **生成层**
   - ✅ 世界框架生成（主题、风格圣经）
   - ✅ 区域生成（biome、危险等级）
   - ✅ 地点生成（几何、感官、可供性）
   - ✅ POI生成
   - ✅ 派系生成（势力、关系矩阵）
   - ✅ 风格词库生成

3. **细化层**
   - ✅ 结构草稿Pass
   - ✅ 感官增益Pass
   - ✅ 可供性提取Pass
   - ✅ 镜头语言Pass
   - ✅ 叙事文本生成
   - ✅ 细化结果固化

4. **API层**
   - ✅ 世界管理API（CRUD）
   - ✅ 区域/地点/POI管理API
   - ✅ 场景细化API
   - ✅ 可供性提取API
   - ✅ 派系管理API

5. **前端层**
   - ✅ 世界管理页面
   - ✅ 世界树导航
   - ✅ 地点详情卡片
   - ✅ 生成表单
   - ✅ 细化触发按钮
   - ✅ 可供性chips显示
   - ✅ useWorld状态管理Hook

6. **文档**
   - ✅ 完整使用指南（`WORLD_SCAFFOLD_GUIDE.md`）
   - ✅ 实现总结（本文档）

### ⚠️ 待完善功能

1. **冲突检测**
   - ❌ Canon冲突自动检测
   - ❌ 重名检测
   - ❌ 关系矩阵一致性验证

2. **版本控制**
   - ❌ 快照与回滚
   - ❌ 差异对比
   - ❌ 多人协作合并

3. **向量检索**
   - ❌ 细化层存入向量数据库
   - ❌ 语义检索相似场景
   - ❌ 上下文自动注入

4. **高级生成**
   - ❌ NPC按需生成（seed→instantiate→engage）
   - ❌ 任务钩子随机抽取
   - ❌ 动态事件生成

5. **UI增强**
   - ❌ 可视化世界地图
   - ❌ 关系图谱（派系、NPC）
   - ❌ 实时预览（风格词库效果）

## 使用示例

### 示例1：生成世界

```bash
curl -X POST http://localhost:8000/api/world/generate \
  -H "Content-Type: application/json" \
  -d '{
    "novelId": "novel-dark-ocean",
    "theme": "deep sea survival",
    "tone": "压抑、未知、孤独",
    "novelType": "scifi",
    "numRegions": 6,
    "locationsPerRegion": 10
  }'
```

**生成结果**：
- 世界名称："深渊之海"
- 6个区域：浅海残骸区、黑暗深渊、热液喷口、冰封深沟、生物禁区、古代废墟
- 5个派系：深潜者联盟、废墟拾荒者、生物狂热者、机械教派、中立贸易站
- 风格词库：["水压", "生物磷光", "金属撞击声", "冰冷刺痛", "硫磺味"]

### 示例2：细化场景

玩家进入"浅海残骸区 → 沉没的研究站"：

```python
result = await refine_location(
    location_id="loc-research-station",
    turn=5,
    target_detail_level=2
)
```

**细化输出**：

**叙事文本**：
> 远处，研究站的破碎穹顶在微弱的生物磷光中隐约可见，金属框架如巨兽的肋骨刺向黑暗的水体。靠近时，耳边传来水流冲击破损舱壁的低鸣，夹杂着松动的电缆在洋流中摆动的金属撞击声。空气中弥漫着海水的咸腥味和锈蚀铁器的涩味。舱门半掩，门缝间渗出浑浊的光——或许是应急灯的余晖，或许是某种发光生物的巢穴。

**可供性chips**：
- 撬开舱门 ⚠️（需要撬棍，可能触发结构坍塌）
- 检查电缆（可能修复部分照明）
- 聆听内部声音（察觉≥3）
- 搜寻漂浮残骸（可能获得补给）
- 查看铭牌（了解研究站历史）

### 示例3：玩家执行动作

玩家点击"撬开舱门"chip：

```python
# 检查前提条件
if "撬棍" in character.inventory:
    # 执行动作
    result = await execute_action({
        "action": "撬开舱门",
        "location_id": "loc-research-station",
        "character_state": character.to_dict()
    })

    # 判定结果
    if random.random() < 0.3:  # 30%概率触发风险
        return "你撬开了舱门,但结构开始坍塌!失去5生命值,但发现了内部的医疗储藏室。"
    else:
        return "你成功撬开了舱门,进入了研究站的主走廊。墙上的紧急指示灯仍在闪烁。"
else:
    return "你需要撬棍才能撬开这扇已经锈蚀的舱门。"
```

## 技术亮点

### 1. 分层细化策略

- **Level 0**（轮廓）：只有名称和类型，适合远处未探索的地点
- **Level 2**（详细）：包含感官和可供性，适合当前探索的地点
- **Level 3**（完全）：包含所有细节和叙事文本，适合关键剧情点

**优势**：避免一次性生成所有内容，节省token和时间。

### 2. 多Pass流水线

将场景细化拆分为4个独立的Pass，每个Pass专注于一个维度：

- **结构Pass**：解决"空间感"
- **感官Pass**：解决"画面感"
- **可供性Pass**：解决"可玩性"
- **镜头Pass**：解决"节奏感"

**优势**：模型输出更可控，每个Pass可独立重试或替换。

### 3. Canon固化机制

细化结果写入`detail_layers`表，标记为`status=canon`：

```python
db.save_detail_layer(DetailLayer(
    id=f"{location_id}-sensory",
    target_type="location",
    target_id=location_id,
    layer_type="sensory",
    content={"sensory_nodes": [...]},
    status="canon"  # 锁定为正典
))
```

**优势**：保证世界一致性，避免同一地点多次访问时描述不一致。

### 4. 风格圣经约束

在生成任何内容时，都注入世界的`style_bible`：

```python
prompt = f"""
请生成场景描写。

**风格要求**:
- 基调: {world_style['tone']}
- 使用感官词: {', '.join(world_style['sensory'])}
- 句长: {world_style['syntax']['avg_sentence_len']}
"""
```

**优势**：保证全书风格统一，符合预设基调。

### 5. 可供性chips交互

将"可做之事"提取为结构化数据，前端渲染为可点击的chips：

```tsx
<Badge onClick={() => handleAction(aff)}>
  {aff.verb}{aff.object}
  {aff.risk && " ⚠️"}
</Badge>
```

**优势**：解决"不知道做什么"的问题，提升交互体验。

## 性能数据（估算）

| 操作 | 耗时 | Token消耗 |
|------|------|-----------|
| 生成世界框架 | ~10s | ~2000 tokens |
| 生成单个区域 | ~5s | ~800 tokens |
| 生成单个地点 | ~3s | ~500 tokens |
| 细化地点（4 Pass） | ~15s | ~3000 tokens |
| 提取可供性 | ~2s | ~300 tokens |

**批量生成（完整世界）**：
- 5个区域 × 8个地点 = 40个地点
- 耗时：~5分钟
- Token：~30k tokens
- 成本（DeepSeek V3）：~$0.04

## 下一步计划

### 短期（1-2周）

1. **集成到聊天界面**
   - 在`chat_api.py`中调用`scene_refinement`
   - 返回可供性chips给前端
   - 支持点击chips执行动作

2. **完善细化逻辑**
   - 添加"按需细化"开关（避免每次都重新生成）
   - 实现细化缓存（基于location.detail_level）
   - 添加细化进度提示（WebSocket推送）

3. **UI优化**
   - 世界地图可视化（使用react-flow或d3.js）
   - 派系关系图谱
   - 细化层diff对比

### 中期（1-2月）

1. **向量检索**
   - 将细化层存入ChromaDB/FAISS
   - 语义检索相似场景（"找到类似废墟的地点"）
   - 自动注入相关上下文

2. **冲突检测**
   - Canon一致性验证
   - 重名检测与去重
   - 关系矩阵对称性检查

3. **NPC生成**
   - 按需生成NPC（seed→instantiate）
   - NPC状态管理（engage→adapt→retire）
   - 对话生成（基于persona和voice_style）

### 长期（3-6月）

1. **完整游戏引擎**
   - 事件线调度（Global Director）
   - 伏笔债务SLA检查
   - 一致性审计系统

2. **多人协作**
   - 世界编辑权限管理
   - 冲突合并策略
   - 实时协作编辑

3. **导出与发布**
   - 导出为Markdown/JSON
   - 生成Wiki站点
   - 与其他工具集成（Obsidian/Notion）

## 相关文件清单

### 后端

| 文件 | 说明 |
|------|------|
| `schema_world_scaffold.sql` | 数据库Schema（13张表） |
| `web/backend/world_models.py` | Pydantic数据模型 |
| `web/backend/world_db.py` | 数据库CRUD操作 |
| `web/backend/world_generator.py` | 世界生成器 |
| `web/backend/scene_refinement.py` | 场景细化流水线 |
| `web/backend/world_api.py` | REST API路由 |
| `web/backend/main.py` | FastAPI主入口（集成） |

### 前端

| 文件 | 说明 |
|------|------|
| `web/frontend/app/world/page.tsx` | 世界管理页面 |
| `web/frontend/components/world/world-manager.tsx` | 主容器组件 |
| `web/frontend/components/world/world-tree.tsx` | 世界树导航 |
| `web/frontend/components/world/location-card.tsx` | 地点详情卡片 |
| `web/frontend/hooks/use-world.ts` | 状态管理Hook |

### 文档

| 文件 | 说明 |
|------|------|
| `docs/WORLD_SCAFFOLD_GUIDE.md` | 完整使用指南 |
| `docs/WORLD_SCAFFOLD_IMPLEMENTATION.md` | 实现总结（本文档） |

## 总结

我们成功实现了一套完整的世界脚手架系统，包括：

1. ✅ **数据层**：13张数据库表，完整Schema
2. ✅ **生成层**：世界、区域、地点、派系、风格词库生成
3. ✅ **细化层**：多Pass流水线（结构→感官→可供性→镜头）
4. ✅ **API层**：REST API接口（15+个endpoint）
5. ✅ **前端层**：世界管理页面、树状导航、地点卡片
6. ✅ **文档层**：完整使用指南、实现总结

这套系统能够有效解决AI长篇小说生成中的"世界一致性"和"叙事画面感"问题，为后续的游戏引擎集成打下了坚实的基础。

---

**实现者**: Claude Code
**日期**: 2025-01-31
**版本**: v1.0
