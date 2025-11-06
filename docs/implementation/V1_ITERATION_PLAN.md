# AI跑团游戏 - v1.1-v1.3 迭代规划

> 基于优化方案的完整实施计划
> 创建时间：2025-11-05
> 当前版本：v1.0 (LangChain 1.0 架构)

## 📋 目录

- [北极星目标](#北极星目标)
- [v1.1 世界预生成与编辑器](#v11-世界预生成与编辑器)
- [v1.2 DM可配置与玩法扩展](#v12-dm可配置与玩法扩展)
- [v1.3 叙事质量与评测](#v13-叙事质量与评测)
- [技术债务清理](#技术债务清理)
- [时间估算](#时间估算)

---

## 北极星目标

### 玩家体验核心

1. **紧张-缓和-爆点** 的叙事节奏（每 3–5 回合形成一个微循环）
2. **可探索的预生成世界**（Fog of War + 动态遭遇表 + 可持续推进的主支线）
3. **可视化掌控感**（状态、任务、地图、关系网、回放）与**可配置的 DM 个性**
4. **稳定可复盘**（事件溯源 + 分支存档 + 回放/战报 + Golden Tests）

---

## v1.1 世界预生成与编辑器

**目标**: 把"世界"作为独立产物（WorldPack）预生成并可在 UI 中编辑、校验、快照与热更新。

**开始时间**: 2025-11-05
**预计完成**: 2025-11-20 (15天)

### 1.1 WorldPack v1 数据模型扩展

#### 当前状态
✅ 已有基础模型：
- `WorldScaffold` - 世界脚手架
- `Region` - 区域
- `Location` - 地点
- `POI` - 兴趣点
- `Faction` - 派系
- `StyleBible` - 风格圣经

#### 需要添加
```python
# web/backend/models/world_models.py

# 新增模型
class Coord(BaseModel):
    x: int
    y: int

class Quest(BaseModel):
    id: str
    title: str
    line: Literal["main","side"]
    summary: str
    prereq_quest_ids: List[str] = []
    objectives: List[QuestObjective] = []
    rewards: Dict[str, int] = {}

class QuestObjective(BaseModel):
    id: str
    text: str
    done: bool = False
    require: List[str] = []

class NPC(BaseModel):
    id: str
    name: str
    role: str
    faction: Optional[str] = None
    persona: str
    desires: List[str] = []
    secrets: List[str] = []
    home_location_id: Optional[str] = None
    relationship: Dict[str, int] = {}

class LootTable(BaseModel):
    id: str
    entries: List[Dict[str, int]]

class EncounterTable(BaseModel):
    id: str
    entries: List[Dict[str, int]]

class WorldMeta(BaseModel):
    id: str
    title: str
    seed: int
    tone: Literal["dark","epic","cozy","mystery","whimsical"] = "epic"
    difficulty: Literal["story","normal","hard"] = "normal"
    map_size: Dict[str, int] = {"w": 64, "h": 64}

class WorldPack(BaseModel):
    meta: WorldMeta
    locations: List[Location]
    npcs: List[NPC]
    quests: List[Quest]
    loot_tables: List[LootTable] = []
    encounter_tables: List[EncounterTable] = []
    lore: Dict[str, str] = {}
    index_version: int = 1
```

**验收标准**:
- [ ] 所有新模型通过 Pydantic 校验
- [ ] 模型序列化/反序列化测试通过
- [ ] 添加业务校验（引用完整性、DAG 无环等）

---

### 1.2 世界生成流水线

#### 当前状态
✅ 已有生成器：
- `WorldGenerator` - 基础世界生成
- 已实现：世界框架、区域、派系、风格词库生成

#### 需要扩展

**1. Job 状态管理**
```python
# web/backend/services/world_generation_job.py

class WorldGenerationJob:
    STATES = [
        "QUEUED",
        "OUTLINE",
        "REGIONS",
        "LOCATIONS",
        "NPCS",
        "QUESTS",
        "INDEXING",
        "READY",
        "FAILED"
    ]

    async def run(self, seed: int, title: str):
        try:
            # 1. Outline
            self.update_state("OUTLINE", 0.1)
            outline = await self.generate_outline(seed, title)

            # 2. Regions
            self.update_state("REGIONS", 0.2)
            regions = await self.generate_regions(outline)

            # 3. Locations
            self.update_state("LOCATIONS", 0.4)
            locations = await self.generate_locations(regions)

            # 4. NPCs
            self.update_state("NPCS", 0.6)
            npcs = await self.generate_npcs(locations)

            # 5. Quests
            self.update_state("QUESTS", 0.8)
            quests = await self.generate_quests(npcs, locations)

            # 6. Indexing
            self.update_state("INDEXING", 0.9)
            await self.build_index(npcs, lore)

            # 7. Ready
            self.update_state("READY", 1.0)

        except Exception as e:
            self.update_state("FAILED", error=str(e))
```

**2. 分阶段校验**
```python
# web/backend/services/world_validator.py

class WorldValidator:
    def validate_references(self, pack: WorldPack) -> List[str]:
        """检查引用完整性"""
        problems = []

        # 检查任务目标引用
        for quest in pack.quests:
            for obj in quest.objectives:
                if obj.require:
                    for req_id in obj.require:
                        if not self._objective_exists(pack, req_id):
                            problems.append(f"任务 {quest.id} 引用不存在的目标 {req_id}")

        # 检查 NPC home_location 引用
        for npc in pack.npcs:
            if npc.home_location_id:
                if not self._location_exists(pack, npc.home_location_id):
                    problems.append(f"NPC {npc.id} 引用不存在的地点 {npc.home_location_id}")

        return problems

    def validate_quest_dag(self, quests: List[Quest]) -> List[str]:
        """检查任务依赖 DAG 无环"""
        # 使用拓扑排序检测环
        pass
```

**3. 向量索引构建**
```python
# web/backend/services/world_indexer.py

class WorldIndexer:
    def __init__(self, db_path: str):
        # 使用 sqlite-vec 或 faiss-local
        self.db = sqlite3.connect(db_path)

    async def build_index(self, pack: WorldPack):
        """构建向量索引（仅 NPC + Lore）"""
        embeddings = []

        # NPC 记忆
        for npc in pack.npcs:
            text = f"{npc.persona}\n{' '.join(npc.desires)}\n{' '.join(npc.secrets)}"
            emb = await self.get_embedding(text)
            embeddings.append({
                "id": npc.id,
                "kind": "npc",
                "text": text,
                "embedding": emb
            })

        # Lore 文档
        for key, text in pack.lore.items():
            emb = await self.get_embedding(text)
            embeddings.append({
                "id": key,
                "kind": "lore",
                "text": text,
                "embedding": emb
            })

        # 批量插入
        self._batch_insert(embeddings)
```

**验收标准**:
- [ ] 生成流水线可从任意阶段恢复
- [ ] 失败自动重试（最多 3 次）
- [ ] 每个阶段产物落盘并校验
- [ ] 1000 行 WorldPack JSON 加载 < 200ms

---

### 1.3 数据库扩展

#### 新增表

```sql
-- database/schema/world_generation.sql

-- 世界表
CREATE TABLE worlds (
  id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  seed INTEGER NOT NULL,
  json_gz BLOB NOT NULL,          -- gzip 压缩的 WorldPack JSON
  index_version INTEGER DEFAULT 1,
  status TEXT NOT NULL,            -- draft/published/locked
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 世界快照
CREATE TABLE world_snapshots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  world_id TEXT NOT NULL,
  tag TEXT NOT NULL,              -- 用户自定义标签
  json_gz BLOB NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (world_id) REFERENCES worlds(id)
);

-- 生成任务
CREATE TABLE world_generation_jobs (
  id TEXT PRIMARY KEY,
  world_id TEXT NOT NULL,
  phase TEXT NOT NULL,            -- QUEUED/OUTLINE/.../READY/FAILED
  progress REAL DEFAULT 0.0,      -- 0.0-1.0
  error TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (world_id) REFERENCES worlds(id)
);

-- 向量知识库
CREATE TABLE world_kb (
  id TEXT PRIMARY KEY,
  world_id TEXT NOT NULL,
  kind TEXT NOT NULL,             -- npc/lore
  ref_id TEXT NOT NULL,           -- npc.id 或 lore key
  content TEXT NOT NULL,
  embedding BLOB NOT NULL,        -- 向量嵌入
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (world_id) REFERENCES worlds(id)
);

-- 世界发现（Fog of War）
CREATE TABLE world_discovery (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  world_id TEXT NOT NULL,
  chunk_x INTEGER NOT NULL,       -- 地图格子坐标
  chunk_y INTEGER NOT NULL,
  discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  UNIQUE(session_id, world_id, chunk_x, chunk_y)
);

-- 游戏事件溯源
CREATE TABLE game_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  session_id TEXT NOT NULL,
  turn INTEGER NOT NULL,
  action TEXT NOT NULL,           -- 工具名称
  payload TEXT NOT NULL,          -- JSON 参数
  result TEXT NOT NULL,           -- JSON 结果
  latency_ms INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_world_kb_world ON world_kb(world_id, kind);
CREATE INDEX idx_world_discovery ON world_discovery(session_id, world_id);
CREATE INDEX idx_game_events ON game_events(session_id, turn);
```

**验收标准**:
- [ ] 所有表创建成功
- [ ] 迁移脚本无错误
- [ ] 索引覆盖常用查询

---

### 1.4 API 端点

```python
# web/backend/api/world_api.py

@router.post("/api/worlds/generate")
async def generate_world(request: WorldGenerationRequest):
    """触发世界生成"""
    job = WorldGenerationJob(request.title, request.seed)
    asyncio.create_task(job.run())

    return {
        "job_id": job.id,
        "world_id": job.world_id,
        "status": "QUEUED"
    }

@router.get("/api/worlds/{world_id}/status")
async def get_generation_status(world_id: str):
    """查询生成进度"""
    job = await db.get_job(world_id)
    return {
        "phase": job.phase,
        "progress": job.progress,
        "error": job.error
    }

@router.get("/api/worlds/{world_id}")
async def get_world(world_id: str):
    """获取 WorldPack（压缩）"""
    world = await db.get_world(world_id)

    # 解压
    import gzip
    json_data = gzip.decompress(world.json_gz)
    pack = json.loads(json_data)

    return pack

@router.post("/api/worlds/{world_id}/validate")
async def validate_world(world_id: str, pack: WorldPack):
    """校验世界"""
    validator = WorldValidator()
    problems = validator.validate_all(pack)

    return {
        "ok": len(problems) == 0,
        "problems": problems
    }

@router.post("/api/worlds/{world_id}/snapshot")
async def create_snapshot(world_id: str, tag: str):
    """创建快照"""
    world = await db.get_world(world_id)
    snapshot_id = await db.create_snapshot(world_id, tag, world.json_gz)

    return {"snapshot_id": snapshot_id, "tag": tag}

@router.get("/api/worlds/{world_id}/snapshots")
async def list_snapshots(world_id: str):
    """列出快照"""
    snapshots = await db.get_snapshots(world_id)
    return {"snapshots": snapshots}

@router.post("/api/worlds/{world_id}/publish")
async def publish_world(world_id: str):
    """发布为当前默认世界"""
    await db.update_world_status(world_id, "published")
    await db.set_default_world(world_id)

    return {"status": "published"}

@router.post("/api/game/init")
async def init_game(world_id: Optional[str] = None):
    """初始化游戏（指定世界）"""
    if not world_id:
        # 使用默认世界
        world_id = await db.get_default_world_id()

    world = await db.get_world(world_id)
    # ... 初始化游戏状态
```

**验收标准**:
- [ ] 所有端点返回正确的数据结构
- [ ] 错误处理齐全
- [ ] API 文档（OpenAPI）更新

---

### 1.5 前端 /world 编辑器

#### 路由结构
```
/world
  ├─ /overview         # 世界卡片、生成状态
  ├─ /map              # 地图画布
  ├─ /locations        # 地点列表与编辑
  ├─ /npcs             # NPC 列表与关系网
  ├─ /quests           # 任务图编辑器
  ├─ /tables           # 掉落/遭遇表
  ├─ /lore             # 百科
  ├─ /dm               # DM 预设
  ├─ /player           # 玩家构建
  └─ /snapshots        # 快照管理
```

#### 页面组件

**1. Overview 页面**
```tsx
// web/frontend/app/world/page.tsx

export default function WorldOverviewPage() {
  const [worlds, setWorlds] = useState<WorldPack[]>([]);
  const [generating, setGenerating] = useState(false);

  const handleGenerate = async (params) => {
    setGenerating(true);
    const res = await apiClient.generateWorld(params);

    // SSE 监听进度
    const eventSource = new EventSource(`/api/worlds/${res.world_id}/stream`);
    eventSource.onmessage = (e) => {
      const data = JSON.parse(e.data);
      setProgress(data.progress);
    };
  };

  return (
    <div className="p-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">世界管理</h1>
        <Button onClick={() => setShowGenerateDialog(true)}>
          生成新世界
        </Button>
      </div>

      {/* 世界卡片网格 */}
      <div className="grid grid-cols-3 gap-4">
        {worlds.map(world => (
          <WorldCard key={world.meta.id} world={world} />
        ))}
      </div>

      {/* 生成对话框 */}
      <GenerateWorldDialog
        open={showGenerateDialog}
        onGenerate={handleGenerate}
      />
    </div>
  );
}
```

**2. Map 画布**
```tsx
// web/frontend/components/world/WorldCanvas.tsx

export function WorldCanvas({ worldPack }: { worldPack: WorldPack }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [viewport, setViewport] = useState({ x: 0, y: 0, scale: 1 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // 虚拟化：只绘制可视区域
    const visible = getVisibleChunks(viewport, worldPack.meta.map_size);

    for (const chunk of visible) {
      drawChunk(ctx, chunk, worldPack.locations);
    }
  }, [viewport, worldPack]);

  return (
    <div className="relative">
      <canvas
        ref={canvasRef}
        width={1200}
        height={800}
        onMouseDown={handlePan}
        onWheel={handleZoom}
      />

      {/* 右键菜单 */}
      <ContextMenu items={[
        { label: "创建地点", onClick: handleCreateLocation },
        { label: "关联任务", onClick: handleLinkQuest }
      ]} />
    </div>
  );
}
```

**3. Location 编辑器**
```tsx
// web/frontend/components/world/LocationEditor.tsx

export function LocationEditor({ locationId }: { locationId: string }) {
  const [location, setLocation] = useState<Location | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  const handleSave = async () => {
    // 校验
    const validator = new LocationValidator();
    const problems = validator.validate(location);

    if (problems.length > 0) {
      setErrors(problems);
      return;
    }

    // 保存
    await apiClient.updateLocation(locationId, location);
    toast({ title: "✅ 保存成功" });
  };

  return (
    <div className="grid grid-cols-3 gap-4">
      {/* 左侧：树状导航 */}
      <div className="col-span-1">
        <LocationTree worldPack={worldPack} />
      </div>

      {/* 中间：表单 */}
      <div className="col-span-1">
        <Form>
          <Input label="名称" value={location?.name} />
          <Select label="类型" options={["landmark", "settlement", "dungeon"]} />
          <Textarea label="宏观描述" />
          <ArrayInput label="几何特征" />
          <ArrayInput label="可交互物" />
        </Form>
      </div>

      {/* 右侧：Inspector */}
      <div className="col-span-1">
        <Inspector location={location} errors={errors} />
      </div>
    </div>
  );
}
```

**验收标准**:
- [ ] 所有页面路由正常
- [ ] 地图画布支持平移/缩放/点击
- [ ] 表单校验实时反馈
- [ ] 快捷键支持（Ctrl+S 保存、Cmd+K 指令面板）

---

### 1.6 Fog of War 机制

```python
# web/backend/game/fog_of_war.py

class FogOfWar:
    CHUNK_SIZE = 16  # 格子大小

    def __init__(self, db: Database):
        self.db = db

    def discover_area(self, session_id: str, world_id: str, x: int, y: int):
        """发现区域"""
        chunk_x = x // self.CHUNK_SIZE
        chunk_y = y // self.CHUNK_SIZE

        # 记录发现
        self.db.execute("""
            INSERT OR IGNORE INTO world_discovery
            (session_id, world_id, chunk_x, chunk_y)
            VALUES (?, ?, ?, ?)
        """, (session_id, world_id, chunk_x, chunk_y))

    def get_discovered_chunks(self, session_id: str, world_id: str) -> List[Tuple[int, int]]:
        """获取已发现的格子"""
        rows = self.db.query("""
            SELECT chunk_x, chunk_y FROM world_discovery
            WHERE session_id = ? AND world_id = ?
        """, (session_id, world_id))

        return [(r[0], r[1]) for r in rows]

    def get_visible_locations(
        self,
        session_id: str,
        world_id: str,
        all_locations: List[Location]
    ) -> List[Location]:
        """获取可见地点"""
        discovered = self.get_discovered_chunks(session_id, world_id)

        visible = []
        for loc in all_locations:
            if not hasattr(loc, 'coord'):
                continue

            chunk = (loc.coord.x // self.CHUNK_SIZE, loc.coord.y // self.CHUNK_SIZE)
            if chunk in discovered:
                visible.append(loc)

        return visible
```

**验收标准**:
- [ ] 玩家移动自动发现新区域
- [ ] 前端地图正确显示迷雾
- [ ] 未发现区域不可交互

---

### 1.7 遭遇表系统

```python
# web/backend/game/encounter_system.py

class EncounterSystem:
    def __init__(self, world_pack: WorldPack):
        self.tables = {t.id: t for t in world_pack.encounter_tables}

    def roll_encounter(
        self,
        location: Location,
        time_of_day: str,  # "day"/"night"
        weather: str,      # "clear"/"rain"/"storm"
        threat_level: int
    ) -> Optional[Dict[str, Any]]:
        """根据环境条件随机遭遇"""

        # 找到适用的遭遇表
        table_id = self._find_table(location.region_id, time_of_day, weather)
        if not table_id:
            return None

        table = self.tables[table_id]

        # 加权随机
        total_weight = sum(e["weight"] for e in table.entries)
        roll = random.randint(1, total_weight)

        current = 0
        for entry in table.entries:
            current += entry["weight"]
            if roll <= current:
                return {
                    "encounter_id": entry["encounter_id"],
                    "difficulty": self._scale_difficulty(entry, threat_level)
                }

        return None
```

**验收标准**:
- [ ] 遭遇表按生态/时间/天气正确触发
- [ ] 权重可在 /world/tables 编辑
- [ ] 遭遇结果记录到事件日志

---

## v1.2 DM可配置与玩法扩展

**预计开始**: 2025-11-21
**预计完成**: 2025-12-10 (20天)

### 2.1 DM 预设系统

```yaml
# config/dm_presets/epic_balanced.yaml

id: "dm_epic_balanced"
name: "史诗平衡"
tone: "epic"

pacing:
  scene_beats: [setup, rising, twist, climax, fallout]
  max_tokens_per_turn: 300
  tension_cycle_length: 5  # 每5回合一个紧张周期

rules:
  roll_strictness: "medium"     # low/medium/high
  failure_is_content: true
  critical_threshold: 0.95      # 95%以上为大成功

combat:
  frequency: "balanced"          # rare/balanced/frequent
  difficulty_curve: "gentle"     # gentle/steep

safety:
  violence: "pg13"
  content_filters: ["sexual_content", "extreme_gore"]

narration_style:
  sentence_length: "varied"
  show_vs_tell_ratio: 0.6
  sensory_detail_level: "high"
```

**前端配置页面**:
```tsx
// web/frontend/app/world/dm/page.tsx

export function DMConfigPage() {
  const [preset, setPreset] = useState<DMPreset | null>(null);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">DM 配置</h1>

      {/* 预设选择 */}
      <Select
        label="预设"
        options={["epic_balanced", "dark_punishing", "cozy_narrative"]}
        value={preset?.id}
        onChange={loadPreset}
      />

      {/* 配置表单 */}
      <Form>
        <Slider label="检定严苛度" min={0} max={100} value={preset?.rules.roll_strictness} />
        <Slider label="战斗频率" min={0} max={100} value={preset?.combat.frequency} />
        <Slider label="叙事风格比（Show/Tell）" min={0} max={1} step={0.1} />

        <MultiSelect label="内容过滤" options={contentFilterOptions} />
      </Form>
    </div>
  );
}
```

---

### 2.2 扩展游戏工具到 25+

#### 新增工具

**时间与移动**:
```python
@tool
def advance_time(minutes: int) -> dict:
    """推进时间"""
    state = get_state()
    state.world.game_time += minutes

    # 触发天气变化
    if minutes >= 360:  # 6小时
        state.world.weather = roll_weather()

    return {"success": True, "new_time": state.world.game_time}

@tool
def travel_to(location_id: str) -> dict:
    """移动到地点"""
    state = get_state()

    # 计算旅行时间
    travel_time = calculate_travel_time(state.player.location, location_id)

    # 随机遭遇
    encounter = encounter_system.roll_encounter(
        location_id,
        state.world.time_of_day,
        state.world.weather
    )

    state.player.location = location_id
    advance_time(travel_time)

    return {
        "success": True,
        "travel_time": travel_time,
        "encounter": encounter
    }
```

**战斗与状态**:
```python
@tool
def apply_status(effect_id: str, duration: int = 3) -> dict:
    """施加状态效果"""
    state = get_state()

    effect = {
        "id": effect_id,
        "duration": duration,
        "applied_turn": state.turn_number
    }

    state.player.status_effects.append(effect)

    return {"success": True, "effect": effect}

@tool
def cast_spell(spell_id: str, target: str = "self") -> dict:
    """施放法术"""
    state = get_state()

    # 检查资源
    spell = get_spell(spell_id)
    if state.player.mana < spell.cost:
        return {"success": False, "error": "魔力不足"}

    # 扣除资源
    state.player.mana -= spell.cost

    # 应用效果
    result = apply_spell_effect(spell, target, state)

    return {"success": True, "result": result}
```

**交互与检查**:
```python
@tool
def inspect(entity_id: str) -> dict:
    """检查实体"""
    state = get_state()

    # 从世界中查找
    entity = find_entity(state.world, entity_id)
    if not entity:
        return {"success": False, "error": "未找到实体"}

    # 察觉检定
    perception_check = roll_check("perception", state.player.attributes.perception)

    # 根据成功度返回信息
    details = get_details_by_check(entity, perception_check)

    return {"success": True, "details": details}

@tool
def rest(kind: Literal["short", "long"] = "short") -> dict:
    """休息"""
    state = get_state()

    if kind == "short":
        # 短休：恢复部分HP和体力
        state.player.hp = min(state.player.max_hp, state.player.hp + 20)
        advance_time(60)
    else:
        # 长休：完全恢复
        state.player.hp = state.player.max_hp
        state.player.stamina = state.player.max_stamina
        state.player.status_effects = []
        advance_time(480)  # 8小时

    return {"success": True, "kind": kind}
```

**验收标准**:
- [ ] 所有新工具通过单元测试
- [ ] 工具调用日志完整
- [ ] System Prompt 更新工具说明

---

### 2.3 任务系统增强

```python
# web/backend/game/quest_system_v2.py

class QuestSystemV2:
    def create_quest_graph(self, quests: List[Quest]) -> nx.DiGraph:
        """构建任务依赖图"""
        G = nx.DiGraph()

        for q in quests:
            G.add_node(q.id, data=q)
            for prereq in q.prereq_quest_ids:
                G.add_edge(prereq, q.id)

        return G

    def get_available_quests(self, completed_ids: List[str]) -> List[Quest]:
        """获取可接任务"""
        available = []

        for q in self.quests:
            # 检查前置完成
            if all(prereq in completed_ids for prereq in q.prereq_quest_ids):
                if q.id not in completed_ids:
                    available.append(q)

        return available

    def update_objective_with_events(self, quest_id: str, events: List[str]):
        """根据事件更新任务目标"""
        quest = self.get_quest(quest_id)

        for obj in quest.objectives:
            if obj.done:
                continue

            # 检查事件是否满足目标
            if self._event_satisfies_objective(events, obj):
                obj.done = True

        # 检查任务完成
        if all(obj.done for obj in quest.objectives):
            self.complete_quest(quest_id)
```

**前端任务图**:
```tsx
// web/frontend/components/world/QuestGraph.tsx

export function QuestGraph({ quests }: { quests: Quest[] }) {
  const { nodes, edges } = useMemo(() => {
    return buildGraphLayout(quests);
  }, [quests]);

  return (
    <ForceGraph
      nodes={nodes}
      edges={edges}
      nodeComponent={QuestNode}
      edgeComponent={DependencyEdge}
    />
  );
}
```

---

## v1.3 叙事质量与评测

**预计开始**: 2025-12-11
**预计完成**: 2025-12-25 (15天)

### 3.1 结构化输出与自检

```python
# web/backend/agents/narration_pipeline.py

class NarrationPipeline:
    async def generate_with_beats(self, context: dict) -> dict:
        """生成带节奏的叙事"""

        # 1. Generator - 生成初稿
        draft = await self.generator_llm.generate_structured(
            prompt=self._build_prompt(context),
            schema={
                "type": "object",
                "properties": {
                    "beats": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "beat_type": {"enum": ["setup", "action", "consequence", "hook"]},
                                "content": {"type": "string"}
                            }
                        }
                    },
                    "word_count": {"type": "integer"}
                }
            }
        )

        # 2. Critic - 自检
        critique = await self.critic_llm.generate(
            prompt=f"""评价以下叙事：

            {json.dumps(draft, ensure_ascii=False)}

            检查：
            1. 风格一致性（与风格圣经对比）
            2. 代词指代清晰
            3. 信息增量（是否推进剧情）
            4. 避免空话（"你感到害怕"这种）

            输出JSON：{{"ok": bool, "problems": [...]}}
            """
        )

        critique_data = json.loads(critique)

        # 3. Refiner - 修订（如需要）
        if not critique_data["ok"]:
            refined = await self.refiner_llm.generate_structured(
                prompt=f"""修订叙事，解决以下问题：

                原文：{draft}
                问题：{critique_data['problems']}
                """,
                schema=...
            )
            return refined

        return draft
```

---

### 3.2 Golden Tests

```python
# tests/golden/test_narrative_quality.py

class TestNarrativeQuality:
    def test_same_seed_reproducible(self):
        """同一种子应产生可复现结果"""
        state1 = run_turn(seed=42, action="向北走")
        state2 = run_turn(seed=42, action="向北走")

        assert state1.world.current_location == state2.world.current_location
        # 叙事可能不同，但关键状态应一致

    def test_narrative_quality_benchmark(self):
        """叙事质量基准测试"""
        results = []

        for turn in golden_turns:
            output = run_turn(turn.seed, turn.action)

            # 评分
            score = evaluate_narrative(
                output.narration,
                criteria=["coherence", "sensory_detail", "progression"]
            )

            results.append(score)

        avg_score = sum(results) / len(results)
        assert avg_score >= 0.7, f"平均质量分 {avg_score} 低于基准线 0.7"
```

---

## 技术债务清理

### 移除 LiteLLM Proxy（已完成✅）
- ✅ 已迁移到 LangChain 1.0 + OpenRouter
- ✅ 已移除 LiteLLM 依赖

### 待优化

1. **真正的流式 LLM 调用**
   - 当前：先完整生成再分句
   - 目标：实时 token 流式输出

2. **工具调用并发控制**
   - 当前：串行执行
   - 目标：支持工具依赖分析与并发执行

3. **向量检索优化**
   - 当前：无向量检索
   - 目标：使用 sqlite-vec 本地检索

---

## 时间估算

| 阶段 | 工作日 | 日历天 |
|------|--------|--------|
| v1.1 WorldPack 模型 | 2 | 3 |
| v1.1 生成流水线 | 3 | 5 |
| v1.1 数据库扩展 | 1 | 2 |
| v1.1 API 端点 | 2 | 3 |
| v1.1 前端编辑器 | 5 | 8 |
| v1.1 Fog of War | 1 | 2 |
| v1.1 遭遇表 | 1 | 2 |
| **v1.1 合计** | **15** | **25** |
| v1.2 DM 预设 | 2 | 3 |
| v1.2 工具扩展 | 3 | 5 |
| v1.2 任务增强 | 2 | 3 |
| v1.2 测试与调优 | 3 | 5 |
| **v1.2 合计** | **10** | **16** |
| v1.3 叙事管线 | 3 | 5 |
| v1.3 Golden Tests | 2 | 3 |
| **v1.3 合计** | **5** | **8** |
| **总计** | **30** | **49** |

**预计总时长**: 约 7 周（2025-11-05 至 2025-12-25）

---

## 下一步行动

1. ✅ 创建迭代规划文档（本文档）
2. ⏭️ 扩展 WorldPack 数据模型
3. ⏭️ 创建数据库迁移脚本
4. ⏭️ 实现世界生成 Job 系统
5. ⏭️ 开发前端 /world/overview 页面

---

**文档维护者**: Claude Code
**创建时间**: 2025-11-05
**版本**: 1.0
