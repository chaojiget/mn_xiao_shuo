"""
WorldPack v1 - 完整的预生成世界数据模型
包含世界、区域、地点、NPC、任务、掉落表、遭遇表等
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 基础组件 ============

class Coord(BaseModel):
    """坐标"""
    x: int
    y: int


# ============ 任务系统 ============

class QuestObjective(BaseModel):
    """任务目标"""
    id: str
    text: str
    done: bool = False
    require: List[str] = []  # 依赖的 objective_id


class Quest(BaseModel):
    """任务"""
    id: str
    title: str
    line: Literal["main", "side"]
    summary: str
    prereq_quest_ids: List[str] = []
    objectives: List[QuestObjective] = []
    rewards: Dict[str, int] = {}  # item_id->qty 或 gold->int
    status: Literal["available", "active", "completed", "failed"] = "available"


# ============ NPC 系统 ============

class NPC(BaseModel):
    """NPC"""
    id: str
    name: str
    role: str
    faction: Optional[str] = None
    persona: str  # 人格/说话风格
    desires: List[str] = []
    secrets: List[str] = []
    home_location_id: Optional[str] = None
    relationship: Dict[str, int] = {}  # npc_id -> -100..100
    memory: List[str] = []  # 记忆片段


# ============ 掉落与遭遇 ============

class LootEntry(BaseModel):
    """掉落条目"""
    item_id: str
    weight: int
    quantity_min: int = 1
    quantity_max: int = 1


class LootTable(BaseModel):
    """掉落表"""
    id: str
    entries: List[LootEntry]


class EncounterEntry(BaseModel):
    """遭遇条目"""
    encounter_id: str
    weight: int
    difficulty_modifier: float = 1.0


class EncounterTable(BaseModel):
    """遭遇表"""
    id: str
    biome: Optional[str] = None  # 适用的生态
    time_of_day: Optional[str] = None  # "day"/"night"
    weather: Optional[str] = None  # "clear"/"rain"/"storm"
    entries: List[EncounterEntry]


# ============ 地点系统 ============

class POI(BaseModel):
    """兴趣点"""
    id: str
    name: str
    kind: Literal["dungeon", "town", "ruin", "cave", "camp", "landmark"]
    coord: Coord
    hooks: List[str] = []  # 叙事钩子
    loot_table_id: Optional[str] = None
    encounter_table_id: Optional[str] = None
    discovered: bool = False


class Location(BaseModel):
    """地点"""
    id: str
    name: str
    biome: Literal["forest", "desert", "swamp", "mountain", "plains", "sea", "city"]
    coord: Coord
    pois: List[POI] = []
    description: Optional[str] = None
    npcs: List[str] = []  # npc_id 列表


# ============ 世界元数据 ============

class WorldMeta(BaseModel):
    """世界元数据"""
    id: str
    title: str
    seed: int
    tone: Literal["dark", "epic", "cozy", "mystery", "whimsical"] = "epic"
    difficulty: Literal["story", "normal", "hard"] = "normal"
    map_size: Dict[str, int] = {"w": 64, "h": 64}
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ WorldPack ============

class WorldPack(BaseModel):
    """世界包 - 完整的预生成世界数据"""
    meta: WorldMeta
    locations: List[Location]
    npcs: List[NPC]
    quests: List[Quest]
    loot_tables: List[LootTable] = []
    encounter_tables: List[EncounterTable] = []
    lore: Dict[str, str] = {}  # 百科条目 (key -> content)
    index_version: int = 1

    def validate_references(self) -> List[str]:
        """校验引用完整性"""
        problems = []

        # 检查任务目标依赖
        for quest in self.quests:
            for obj in quest.objectives:
                for req_id in obj.require:
                    # 检查依赖的目标是否存在
                    if not any(o.id == req_id for o in quest.objectives):
                        problems.append(
                            f"任务 {quest.id} 的目标 {obj.id} 引用不存在的依赖 {req_id}"
                        )

        # 检查 NPC home_location
        location_ids = {loc.id for loc in self.locations}
        for npc in self.npcs:
            if npc.home_location_id and npc.home_location_id not in location_ids:
                problems.append(
                    f"NPC {npc.id} 引用不存在的地点 {npc.home_location_id}"
                )

        # 检查 Location 的 NPCs
        npc_ids = {npc.id for npc in self.npcs}
        for loc in self.locations:
            for npc_id in loc.npcs:
                if npc_id not in npc_ids:
                    problems.append(
                        f"地点 {loc.id} 引用不存在的 NPC {npc_id}"
                    )

        # 检查 POI 的掉落表和遭遇表
        loot_table_ids = {t.id for t in self.loot_tables}
        encounter_table_ids = {t.id for t in self.encounter_tables}

        for loc in self.locations:
            for poi in loc.pois:
                if poi.loot_table_id and poi.loot_table_id not in loot_table_ids:
                    problems.append(
                        f"POI {poi.id} 引用不存在的掉落表 {poi.loot_table_id}"
                    )
                if poi.encounter_table_id and poi.encounter_table_id not in encounter_table_ids:
                    problems.append(
                        f"POI {poi.id} 引用不存在的遭遇表 {poi.encounter_table_id}"
                    )

        return problems

    def validate_quest_dag(self) -> List[str]:
        """校验任务依赖 DAG 无环"""
        problems = []

        # 构建依赖图
        graph: Dict[str, List[str]] = {}
        for quest in self.quests:
            graph[quest.id] = quest.prereq_quest_ids

        # 拓扑排序检测环
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for quest_id in graph:
            if quest_id not in visited:
                if has_cycle(quest_id):
                    problems.append(f"任务依赖存在环路，涉及任务: {quest_id}")

        return problems


# ============ 生成请求 ============

class WorldGenerationRequest(BaseModel):
    """世界生成请求"""
    title: str
    seed: Optional[int] = None
    tone: Literal["dark", "epic", "cozy", "mystery", "whimsical"] = "epic"
    difficulty: Literal["story", "normal", "hard"] = "normal"
    num_locations: int = Field(default=20, ge=5, le=50)
    num_npcs: int = Field(default=15, ge=3, le=30)
    num_quests: int = Field(default=10, ge=3, le=20)


# ============ 生成进度 ============

class WorldGenerationJob(BaseModel):
    """世界生成任务"""
    id: str
    world_id: str
    phase: Literal[
        "QUEUED",
        "OUTLINE",
        "LOCATIONS",
        "NPCS",
        "QUESTS",
        "LOOT_TABLES",
        "ENCOUNTER_TABLES",
        "INDEXING",
        "READY",
        "FAILED"
    ] = "QUEUED"
    progress: float = Field(default=0.0, ge=0.0, le=1.0)
    error: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GenerationProgress(BaseModel):
    """生成进度"""
    phase: str
    progress: float  # 0.0-1.0
    message: str
    data: Optional[Dict[str, Any]] = None


# ============ 快照系统 ============

class WorldSnapshot(BaseModel):
    """世界快照"""
    id: int
    world_id: str
    tag: str
    created_at: datetime


# ============ Fog of War ============

class WorldDiscovery(BaseModel):
    """世界发现记录"""
    session_id: str
    world_id: str
    chunk_x: int
    chunk_y: int
    discovered_at: datetime
