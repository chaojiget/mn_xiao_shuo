"""
世界脚手架数据模型
用于世界雏形管理与逐步细化
"""

from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# ============ 风格圣经 ============

class SyntaxPreferences(BaseModel):
    """句法偏好"""
    avg_sentence_len: int = 18
    prefer_active: bool = True
    paragraph_rhythm: str = "varied"  # varied/short/flowing


class StyleBible(BaseModel):
    """风格圣经"""
    tone: str  # 基调: "冷冽、压抑、写实"
    sensory: List[str]  # 感官词集: ["寒气", "盐霜", "铁锈味"]
    syntax: SyntaxPreferences
    imagery: Optional[List[str]] = None  # 意象词库
    metaphor_patterns: Optional[List[str]] = None  # 比喻模式


# ============ 世界脚手架 ============

class WorldScaffold(BaseModel):
    """世界脚手架"""
    id: str
    novel_id: str
    name: str

    # 主题与基调
    theme: str  # "dark survival", "epic cultivation"
    tone: str  # "冷冽压抑", "波澜壮阔"

    # 设定
    timeline: Optional[Dict[str, Any]] = None
    tech_magic_level: Optional[Dict[str, Any]] = None
    geography_climate: Optional[Dict[str, Any]] = None
    core_conflicts: Optional[List[str]] = None
    forbidden_rules: Optional[List[str]] = None

    # 风格圣经
    style_bible: StyleBible

    # 状态
    status: Literal["draft", "published", "locked"] = "draft"
    version: int = 1

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 区域 ============

class Region(BaseModel):
    """区域"""
    id: str
    world_id: str
    name: str

    # 地理
    biome: str  # "冻海海岸", "炎漠", "迷雾沼泽"
    climate: Optional[str] = None
    geography: Optional[str] = None

    # 资源与派系
    resources: Optional[List[str]] = None
    factions: Optional[List[str]] = None  # 派系IDs

    # 危险与可达性
    danger_level: int = Field(default=1, ge=1, le=10)
    travel_difficulty: Optional[str] = None
    travel_hints: Optional[List[str]] = None

    # 区域特性
    special_rules: Optional[List[str]] = None
    atmosphere: Optional[str] = None

    # 状态
    status: Literal["draft", "published", "locked"] = "draft"
    canon_locked: bool = False

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 地点 ============

class LocationSnapshot(BaseModel):
    """地点快照"""
    macro: Optional[str] = None  # 宏观描述
    geometry: Optional[List[str]] = None  # 几何特征
    interactables: Optional[List[str]] = None  # 可交互物
    sensory: Optional[List[str]] = None  # 感官节点
    affordances: Optional[List[str]] = None  # 可做之事


class Location(BaseModel):
    """地点"""
    id: str
    region_id: str
    name: str
    type: Literal["landmark", "settlement", "dungeon", "wilderness"]

    # 快照描述
    macro_description: Optional[str] = None

    # 几何与交互
    geometry: Optional[List[str]] = None
    interactables: Optional[List[str]] = None

    # 感官
    sensory: Optional[List[str]] = None

    # 可供性
    affordances: Optional[List[str]] = None

    # 派系与NPC
    controlling_faction: Optional[str] = None
    key_npcs: Optional[List[str]] = None

    # 状态
    status: Literal["draft", "published", "locked"] = "draft"
    canon_locked: bool = False
    detail_level: int = Field(default=0, ge=0, le=3)  # 0=轮廓, 3=完全细化

    # 访问记录
    visit_count: int = 0
    first_visited_turn: Optional[int] = None
    last_visited_turn: Optional[int] = None

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 兴趣点 ============

class POI(BaseModel):
    """兴趣点"""
    id: str
    location_id: str
    name: str
    type: Literal["object", "npc", "event", "hazard", "secret"]

    # 描述
    description: Optional[str] = None
    details: Optional[Dict[str, Any]] = None  # 细化信息

    # 交互
    interaction_type: Optional[str] = None  # examine/talk/use/combat/solve
    requirements: Optional[Dict[str, Any]] = None
    risks: Optional[List[str]] = None
    expected_outcomes: Optional[List[str]] = None

    # 状态
    state: Literal["active", "depleted", "destroyed", "hidden"] = "active"
    interacted: bool = False

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 派系 ============

class Faction(BaseModel):
    """派系"""
    id: str
    world_id: str
    name: str

    # 定义
    purpose: str
    ideology: Optional[str] = None

    # 资源与势力
    resources: Optional[Dict[str, Any]] = None
    territory: Optional[List[str]] = None  # 区域IDs
    power_level: int = Field(default=5, ge=1, le=10)

    # 关系
    relationships: Optional[Dict[str, int]] = None  # {factionId: attitude(-10~10)}

    # 组织结构
    structure: Optional[str] = None
    key_members: Optional[List[str]] = None  # NPC IDs

    # 声望与行为
    voice_style: Optional[str] = None
    behavior_patterns: Optional[List[str]] = None

    # 状态
    status: Literal["active", "weakened", "destroyed"] = "active"

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 物品 ============

class WorldItem(BaseModel):
    """世界物品"""
    id: str
    world_id: str
    name: str
    type: Literal["weapon", "armor", "consumable", "material", "key_item"]

    # 描述
    description: Optional[str] = None
    sensory_details: Optional[List[str]] = None

    # 属性
    rarity: Literal["common", "uncommon", "rare", "legendary"] = "common"
    properties: Optional[Dict[str, Any]] = None

    # 制作与获取
    crafting_recipe: Optional[Dict[str, Any]] = None
    sources: Optional[List[str]] = None

    # 状态
    status: Literal["active", "deprecated"] = "active"

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 生物 ============

class Creature(BaseModel):
    """生物"""
    id: str
    world_id: str
    name: str
    type: Literal["beast", "humanoid", "undead", "construct", "spirit"]

    # 描述
    description: Optional[str] = None
    sensory_details: Optional[List[str]] = None

    # 生态位
    habitat: Optional[List[str]] = None  # region/location IDs
    behavior: Optional[str] = None

    # 战斗属性
    danger_rating: int = Field(default=1, ge=1, le=10)
    abilities: Optional[List[str]] = None
    weaknesses: Optional[List[str]] = None

    # 掉落
    loot_table: Optional[List[Dict[str, Any]]] = None

    # 状态
    status: Literal["active", "extinct"] = "active"

    # 元数据
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ============ 任务钩子 ============

class QuestHook(BaseModel):
    """任务钩子"""
    id: str
    world_id: str

    # 分类
    category: Literal["encounter", "quest", "secret", "danger"]
    context: Optional[str] = None  # 适用场景

    # 内容
    title: str
    description: str
    trigger_conditions: Optional[Dict[str, Any]] = None

    # 结果
    possible_outcomes: Optional[List[str]] = None

    # 权重
    weight: float = 1.0
    used_count: int = 0

    # 状态
    status: Literal["active", "exhausted"] = "active"

    # 元数据
    created_at: Optional[datetime] = None


# ============ 细化层 ============

class DetailLayer(BaseModel):
    """细化层"""
    id: str
    target_type: Literal["location", "poi", "region", "creature"]
    target_id: str

    # 细化类型
    layer_type: Literal["sensory", "geometry", "affordance", "cinematic", "narrative"]

    # 内容
    content: Dict[str, Any]

    # 来源
    source: Literal["generated", "manual", "player_action"] = "generated"
    generated_by_turn: Optional[int] = None
    player_id: Optional[str] = None

    # 状态
    status: Literal["draft", "approved", "canon"] = "draft"

    # 元数据
    created_at: Optional[datetime] = None


# ============ 世界事件 ============

class WorldEvent(BaseModel):
    """世界事件"""
    id: int
    world_id: str
    novel_id: str
    turn: int

    # 事件内容
    event_type: str  # faction_change/location_destroyed/npc_death/resource_depleted
    description: str

    # 影响范围
    affected_entities: Optional[Dict[str, List[str]]] = None

    # 状态变化
    state_changes: Optional[Dict[str, Any]] = None

    # 可逆性
    reversible: bool = False

    # 元数据
    created_at: Optional[datetime] = None


# ============ 风格词库 ============

class StyleVocabulary(BaseModel):
    """风格词库"""
    id: int
    world_id: str

    # 分类
    category: Literal["imagery", "metaphor", "sensory", "syntax_pattern"]
    subcategory: Optional[str] = None

    # 内容
    content: str
    examples: Optional[List[str]] = None

    # 使用频率
    usage_weight: float = 1.0
    used_count: int = 0

    # 状态
    status: Literal["active", "deprecated"] = "active"

    # 元数据
    created_at: Optional[datetime] = None


# ============ 冲突检测 ============

class CanonConflict(BaseModel):
    """Canon冲突"""
    id: int
    world_id: str

    # 冲突类型
    conflict_type: str  # duplicate_name/relationship_conflict/resource_conflict/geography_conflict

    # 冲突实体
    entity_a: str  # {type}:{id}
    entity_b: str

    # 详情
    description: str
    severity: Literal["warning", "error", "critical"] = "warning"

    # 状态
    status: Literal["unresolved", "resolved", "ignored"] = "unresolved"
    resolution: Optional[str] = None

    # 元数据
    detected_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


# ============ 生成请求 ============

class WorldGenerationRequest(BaseModel):
    """世界生成请求"""
    novel_id: str
    theme: str
    tone: str
    novel_type: Literal["scifi", "xianxia"]

    # 可选参数
    num_regions: int = Field(default=5, ge=3, le=12)
    locations_per_region: int = Field(default=8, ge=5, le=15)
    pois_per_location: int = Field(default=5, ge=3, le=10)

    # 风格偏好
    style_preferences: Optional[Dict[str, Any]] = None


class RegionGenerationRequest(BaseModel):
    """区域生成请求"""
    world_id: str
    count: int = Field(default=1, ge=1, le=10)
    constraints: Optional[Dict[str, Any]] = None


class LocationGenerationRequest(BaseModel):
    """地点生成请求"""
    region_id: str
    count: int = Field(default=1, ge=1, le=15)
    types: Optional[List[str]] = None


class POIGenerationRequest(BaseModel):
    """POI生成请求"""
    location_id: str
    count: int = Field(default=1, ge=1, le=10)
    types: Optional[List[str]] = None


# ============ 细化请求 ============

class LocationRefinementRequest(BaseModel):
    """地点细化请求"""
    location_id: str
    turn: int
    target_detail_level: int = Field(default=2, ge=1, le=3)
    passes: List[Literal["structure", "sensory", "affordance", "cinematic"]] = [
        "structure", "sensory", "affordance", "cinematic"
    ]


class AffordanceExtractionRequest(BaseModel):
    """可供性提取请求"""
    location_id: str
    character_state: Optional[Dict[str, Any]] = None  # 角色状态
    context: Optional[Dict[str, Any]] = None  # 上下文


# ============ 响应模型 ============

class GenerationProgress(BaseModel):
    """生成进度"""
    stage: str
    progress: float  # 0.0-1.0
    message: str
    data: Optional[Dict[str, Any]] = None


class WorldGenerationResponse(BaseModel):
    """世界生成响应"""
    world: WorldScaffold
    regions: List[Region]
    summary: str


class RefinementResult(BaseModel):
    """细化结果"""
    location_id: str
    detail_level: int
    layers: List[DetailLayer]
    affordances: List[Dict[str, Any]]
    narrative_text: Optional[str] = None


class AffordanceResult(BaseModel):
    """可供性结果"""
    affordances: List[Dict[str, Any]]  # [{verb, object, requirement?, risk?, expectedOutcome?}]
    suggested_actions: List[str]  # 简短的动宾短语 (UI chips)
