"""
可编辑的小说设定系统
Editable Novel Setting System

支持：
1. 动态增删改查世界观、主角、路线等设定
2. 主角知识层与真实世界层分离（探索发现机制）
3. 设定版本管理
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from uuid import uuid4


# ============================================================================
# 核心设定类型
# ============================================================================

class NovelTypeConfig(BaseModel):
    """小说类型配置（科幻 vs 玄幻）"""
    novel_type: Literal["scifi", "xianxia"]

    # 类型特征
    drive_force: str  # 驱动力：设定推演 vs 成长升级
    red_line: List[str]  # 红线规则
    pacing: str  # 节奏描述
    reader_expectation: str  # 读者预期

    # 评分权重（可玩性:叙事）
    playability_weight: float = 0.6
    narrative_weight: float = 0.4

    # 推荐参数
    chapter_per_arc: int = Field(default=15, description="每条事件线的章节数")
    tension_check_interval: int = Field(default=5, description="张力检查间隔")

    @classmethod
    def scifi_default(cls) -> "NovelTypeConfig":
        """科幻默认配置"""
        return cls(
            novel_type="scifi",
            drive_force="设定推演（技术/社会系统→问题→后果）",
            red_line=[
                "因果自洽",
                "证据链可验证",
                "禁止'万能补丁'",
                "技术推演符合基本物理规律"
            ],
            pacing="按'卷'推进（每卷一个技术/社会议题），每10-15章给一次可检验进展",
            reader_expectation="反直觉但不反常识、反转有证据、议题回响",
            playability_weight=0.5,
            narrative_weight=0.5,
            chapter_per_arc=12,
            tension_check_interval=5
        )

    @classmethod
    def xianxia_default(cls) -> "NovelTypeConfig":
        """玄幻/仙侠默认配置"""
        return cls(
            novel_type="xianxia",
            drive_force="成长与升级（境界/功法/资源/宗门）",
            red_line=[
                "突破要代价",
                "资源守恒",
                "因果/业力可追溯",
                "境界压制符合设定"
            ],
            pacing="2-3章一个爽点或小战果，20-40章一次阶段跃迁",
            reader_expectation="短反馈闭环、越级/逆袭爽感、势力扩张",
            playability_weight=0.7,
            narrative_weight=0.3,
            chapter_per_arc=25,
            tension_check_interval=3
        )


class WorldKnowledge(BaseModel):
    """世界知识层（真实 vs 主角已知）"""
    element_id: str
    element_type: Literal["location", "faction", "character", "rule", "secret", "resource"]

    # 真实信息（系统持有的完整真相）
    true_data: Dict[str, Any]

    # 主角已知信息（玩家/主角当前的认知）
    protagonist_knowledge: Dict[str, Any] = Field(default_factory=dict)

    # 发现条件
    discovery_conditions: Optional[List[str]] = None
    discovery_status: Literal["unknown", "partial", "full"] = "unknown"

    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    discovered_at: Optional[datetime] = None

    def discover(self, level: Literal["partial", "full"], revealed_keys: Optional[List[str]] = None):
        """主角发现此元素"""
        self.discovery_status = level
        self.discovered_at = datetime.now()

        if level == "full":
            self.protagonist_knowledge = self.true_data.copy()
        elif level == "partial" and revealed_keys:
            for key in revealed_keys:
                if key in self.true_data:
                    self.protagonist_knowledge[key] = self.true_data[key]

    def get_protagonist_view(self) -> Dict[str, Any]:
        """获取主角视角的信息"""
        if self.discovery_status == "unknown":
            return {"status": "未知", "element_type": self.element_type}
        elif self.discovery_status == "partial":
            return {"status": "部分已知", **self.protagonist_knowledge}
        else:
            return {"status": "完全了解", **self.true_data}


class ProtagonistSetting(BaseModel):
    """主角设定（可编辑）"""
    name: str
    role: str  # 职业/境界
    description: str

    # 属性（根据类型不同而变化）
    attributes: Dict[str, Any] = Field(default_factory=dict)

    # 初始资源
    resources: Dict[str, float] = Field(default_factory=dict)

    # 初始装备/物品
    inventory: List[str] = Field(default_factory=list)

    # 性格特质
    personality: List[str] = Field(default_factory=list)

    # 背景故事
    background: str = ""

    # 目标（短期/长期）
    goals: Dict[str, str] = Field(default_factory=lambda: {"short_term": "", "long_term": ""})

    # 是否可修改
    editable: bool = True


class WorldSetting(BaseModel):
    """世界观设定（可编辑）"""

    # 基础信息
    title: str
    setting_text: str  # 300-500字的世界背景

    # 时间线
    timeline: str = ""

    # 地点（真实层）
    locations: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # 势力（真实层）
    factions: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # 规则/法则（真实层）
    rules: Dict[str, Dict[str, Any]] = Field(default_factory=dict)

    # 技术水平/境界体系
    power_system: Dict[str, Any] = Field(default_factory=dict)

    # 秘密/谜题（完全隐藏，需要探索发现）
    secrets: List[Dict[str, Any]] = Field(default_factory=list)

    # 世界知识层（管理主角的认知）
    knowledge_layer: Dict[str, WorldKnowledge] = Field(default_factory=dict)

    def add_knowledge_element(
        self,
        element_type: str,
        element_id: str,
        true_data: Dict[str, Any],
        discovery_conditions: Optional[List[str]] = None
    ) -> WorldKnowledge:
        """添加世界知识元素"""
        knowledge = WorldKnowledge(
            element_id=element_id,
            element_type=element_type,
            true_data=true_data,
            discovery_conditions=discovery_conditions
        )
        self.knowledge_layer[element_id] = knowledge
        return knowledge

    def protagonist_discovers(
        self,
        element_id: str,
        level: Literal["partial", "full"],
        revealed_keys: Optional[List[str]] = None
    ):
        """主角发现某个元素"""
        if element_id in self.knowledge_layer:
            self.knowledge_layer[element_id].discover(level, revealed_keys)

    def get_protagonist_worldview(self) -> Dict[str, Any]:
        """获取主角当前的世界观（已知部分）"""
        return {
            "title": self.title,
            "setting_text": self.setting_text,
            "known_locations": {
                k: v.get_protagonist_view()
                for k, v in self.knowledge_layer.items()
                if v.element_type == "location" and v.discovery_status != "unknown"
            },
            "known_factions": {
                k: v.get_protagonist_view()
                for k, v in self.knowledge_layer.items()
                if v.element_type == "faction" and v.discovery_status != "unknown"
            },
            "known_rules": {
                k: v.get_protagonist_view()
                for k, v in self.knowledge_layer.items()
                if v.element_type == "rule" and v.discovery_status != "unknown"
            }
        }


class EventArcTemplate(BaseModel):
    """事件线模板"""
    arc_id: str
    arc_name: str
    arc_type: Literal["main", "side", "hidden"]

    # 事件线描述
    description: str

    # 事件节点（简化版本）
    nodes: List[Dict[str, Any]] = Field(default_factory=list)

    # 前置条件
    prerequisites: List[str] = Field(default_factory=list)

    # 预期章节数
    estimated_chapters: int = 10

    # 主题标签
    themes: List[str] = Field(default_factory=list)


class RouteOverview(BaseModel):
    """路线总览（两大类型的差异化呈现）"""
    route_id: str
    route_name: str
    novel_type: Literal["scifi", "xianxia"]

    # 核心差异点
    key_differences: List[str] = Field(default_factory=list)

    # 主事件线
    main_arcs: List[EventArcTemplate] = Field(default_factory=list)

    # 可选支线
    side_arcs: List[EventArcTemplate] = Field(default_factory=list)

    # 路线特色标签
    tags: List[str] = Field(default_factory=list)


# ============================================================================
# 可编辑设定（完整配置）
# ============================================================================

class EditableNovelSetting(BaseModel):
    """可编辑的完整小说设定"""

    # 元信息
    setting_id: str = Field(default_factory=lambda: str(uuid4()))
    version: int = 1
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # 小说类型配置
    novel_type_config: NovelTypeConfig

    # 世界观设定
    world_setting: WorldSetting

    # 主角设定
    protagonist: ProtagonistSetting

    # 路线总览
    routes: List[RouteOverview] = Field(default_factory=list)

    # 体验目标
    experience_goal: str = ""

    # 偏好模式
    preference: Literal["playability", "narrative", "hybrid"] = "hybrid"

    # 约束条件
    constraints: Dict[str, List[str]] = Field(default_factory=lambda: {
        "hard_rules": [],
        "soft_rules": [],
        "content_guard": []
    })

    # 提示策略
    hint_policy: Dict[str, Any] = Field(default_factory=lambda: {
        "hint_latency": 2,
        "explicit_ratio": 0.3,
        "red_herring_cap": 1
    })

    # 起始事件
    starting_event: Optional[Dict[str, Any]] = None

    # 是否已初始化（生成了首章）
    initialized: bool = False

    # ========================================================================
    # 增删改查方法
    # ========================================================================

    def update_protagonist(self, **kwargs):
        """更新主角设定"""
        for key, value in kwargs.items():
            if hasattr(self.protagonist, key):
                setattr(self.protagonist, key, value)
        self._mark_updated()

    def add_location(self, location_id: str, location_data: Dict[str, Any]):
        """添加地点"""
        self.world_setting.locations[location_id] = location_data
        # 同时添加到知识层（默认未知）
        self.world_setting.add_knowledge_element(
            element_type="location",
            element_id=location_id,
            true_data=location_data
        )
        self._mark_updated()

    def add_faction(self, faction_id: str, faction_data: Dict[str, Any]):
        """添加势力"""
        self.world_setting.factions[faction_id] = faction_data
        self.world_setting.add_knowledge_element(
            element_type="faction",
            element_id=faction_id,
            true_data=faction_data
        )
        self._mark_updated()

    def add_rule(self, rule_id: str, rule_data: Dict[str, Any]):
        """添加规则/法则"""
        self.world_setting.rules[rule_id] = rule_data
        self.world_setting.add_knowledge_element(
            element_type="rule",
            element_id=rule_id,
            true_data=rule_data
        )
        self._mark_updated()

    def add_secret(self, secret_data: Dict[str, Any]):
        """添加秘密/谜题"""
        self.world_setting.secrets.append(secret_data)
        self._mark_updated()

    def add_route(self, route: RouteOverview):
        """添加路线"""
        self.routes.append(route)
        self._mark_updated()

    def remove_location(self, location_id: str):
        """删除地点"""
        self.world_setting.locations.pop(location_id, None)
        self.world_setting.knowledge_layer.pop(location_id, None)
        self._mark_updated()

    def remove_faction(self, faction_id: str):
        """删除势力"""
        self.world_setting.factions.pop(faction_id, None)
        self.world_setting.knowledge_layer.pop(faction_id, None)
        self._mark_updated()

    def protagonist_discovers(
        self,
        element_id: str,
        level: Literal["partial", "full"],
        revealed_keys: Optional[List[str]] = None
    ):
        """主角发现世界元素"""
        self.world_setting.protagonist_discovers(element_id, level, revealed_keys)
        self._mark_updated()

    def get_protagonist_view(self) -> Dict[str, Any]:
        """获取主角视角（用于生成提示词）"""
        return {
            "protagonist": self.protagonist.model_dump(),
            "worldview": self.world_setting.get_protagonist_worldview(),
            "known_goals": self.protagonist.goals
        }

    def get_full_setting(self) -> Dict[str, Any]:
        """获取完整设定（用于导演系统）"""
        return self.model_dump()

    def _mark_updated(self):
        """标记更新时间和版本"""
        self.updated_at = datetime.now()
        self.version += 1

    # ========================================================================
    # 工厂方法
    # ========================================================================

    @classmethod
    def from_json_config(cls, config: Dict[str, Any]) -> "EditableNovelSetting":
        """从传统JSON配置创建（兼容旧格式）"""
        novel_type = config.get("novel_type", "scifi")

        # 创建类型配置
        if novel_type == "scifi":
            type_config = NovelTypeConfig.scifi_default()
        else:
            type_config = NovelTypeConfig.xianxia_default()

        # 解析主角
        protagonist_data = config.get("主角设定", {})
        protagonist = ProtagonistSetting(
            name=protagonist_data.get("姓名", "未命名"),
            role=protagonist_data.get("职业/境界", "未知"),
            description=protagonist_data.get("描述", ""),
            attributes=protagonist_data.get("能力", {}),
            resources=protagonist_data.get("初始资源", {}),
            personality=protagonist_data.get("性格", []),
            background=protagonist_data.get("背景", "")
        )

        # 解析世界观
        world_data = config.get("world_state", {})
        world_setting = WorldSetting(
            title=config.get("title", "未命名小说"),
            setting_text=config.get("setting_text", ""),
            timeline=world_data.get("时间线", ""),
            power_system=world_data.get("技术水平/境界体系", {})
        )

        # 添加地点到知识层
        for loc_id, loc_data in world_data.get("主要地点", {}).items():
            world_setting.locations[loc_id] = loc_data
            world_setting.add_knowledge_element(
                element_type="location",
                element_id=loc_id,
                true_data=loc_data
            )

        # 添加势力到知识层
        for faction_id, faction_data in world_data.get("势力", {}).items():
            world_setting.factions[faction_id] = faction_data
            world_setting.add_knowledge_element(
                element_type="faction",
                element_id=faction_id,
                true_data=faction_data
            )

        return cls(
            novel_type_config=type_config,
            world_setting=world_setting,
            protagonist=protagonist,
            experience_goal=config.get("experience_goal", ""),
            preference=config.get("preference", "hybrid"),
            constraints=config.get("constraints", {}),
            hint_policy=config.get("hint_policy", {}),
            starting_event=config.get("起始事件")
        )

    @classmethod
    def create_empty(cls, novel_type: Literal["scifi", "xianxia"]) -> "EditableNovelSetting":
        """创建空白设定（用于从头开始）"""
        if novel_type == "scifi":
            type_config = NovelTypeConfig.scifi_default()
        else:
            type_config = NovelTypeConfig.xianxia_default()

        return cls(
            novel_type_config=type_config,
            world_setting=WorldSetting(
                title="未命名小说",
                setting_text="请填写世界背景..."
            ),
            protagonist=ProtagonistSetting(
                name="主角",
                role="未定义",
                description="请填写主角描述..."
            )
        )
