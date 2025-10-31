"""
NPC生命周期管理
NPC Lifecycle Management

实现: seed → instantiate → engage → adapt → retire

核心思想:
- NPC不预先生成，而是在剧情需要时才实例化
- 使用种子(seed)描述NPC的潜在存在
- 根据剧情进度动态创建和更新NPC
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal, Any
from datetime import datetime
from uuid import uuid4


class NPCSeed(BaseModel):
    """NPC种子（潜在存在的NPC）"""
    seed_id: str = Field(default_factory=lambda: str(uuid4()))

    # 基本定义
    archetype: str  # 原型：mentor/companion/opponent/neutral/merchant/quest_giver
    role_in_story: str  # 在故事中的角色：例如"神秘导师"、"竞争对手"

    # 触发条件（什么情况下需要实例化）
    spawn_conditions: List[str] = Field(default_factory=list)  # 例如 ["主角到达XX地点", "完成XX任务"]

    # 生成约束
    generation_constraints: Dict[str, Any] = Field(default_factory=dict)
    # 例如: {"faction": "科学院", "power_level_range": [3, 5]}

    # 种子描述（用于生成时的提示）
    seed_description: str = ""

    # 优先级（多个种子竞争时的优先级）
    priority: int = 5

    # 状态
    status: Literal["dormant", "ready", "instantiated"] = "dormant"
    instantiated_npc_id: Optional[str] = None


class NPCInstance(BaseModel):
    """NPC实例（已实例化的NPC）"""
    npc_id: str = Field(default_factory=lambda: str(uuid4()))
    seed_id: Optional[str] = None  # 来源种子

    # 基本信息
    name: str
    role: str  # 职业/身份
    archetype: str  # mentor/companion/opponent/neutral

    # 详细信息
    description: str
    personality: List[str] = Field(default_factory=list)
    background: str = ""

    # 属性（与Character类似但更简化）
    attributes: Dict[str, Any] = Field(default_factory=dict)

    # 关系网
    relationships: Dict[str, float] = Field(default_factory=dict)
    # key: character_id, value: 关系值 (-100 to 100)

    # 所属势力
    faction: Optional[str] = None

    # 当前位置
    current_location: Optional[str] = None

    # 目标与动机
    goals: List[str] = Field(default_factory=list)
    motivations: List[str] = Field(default_factory=list)

    # 知识（NPC知道的秘密/线索）
    known_secrets: List[str] = Field(default_factory=list)
    can_provide_clues: List[str] = Field(default_factory=list)

    # 生命周期状态
    lifecycle_stage: Literal["instantiated", "engaged", "adapted", "retired"] = "instantiated"

    # 互动历史
    interaction_count: int = 0
    last_interaction: Optional[datetime] = None
    interaction_summary: List[str] = Field(default_factory=list)

    # 元信息
    created_at: datetime = Field(default_factory=datetime.now)
    retired_at: Optional[datetime] = None
    retirement_reason: Optional[str] = None

    def engage(self, interaction_summary: str):
        """与主角互动"""
        self.interaction_count += 1
        self.last_interaction = datetime.now()
        self.interaction_summary.append(interaction_summary)

        if self.lifecycle_stage == "instantiated":
            self.lifecycle_stage = "engaged"

    def adapt(self, changes: Dict[str, Any]):
        """根据剧情适应改变"""
        # 更新属性
        if "attributes" in changes:
            self.attributes.update(changes["attributes"])

        # 更新关系
        if "relationships" in changes:
            self.relationships.update(changes["relationships"])

        # 更新目标
        if "goals" in changes:
            self.goals.extend(changes["goals"])

        # 更新阶段
        if self.lifecycle_stage == "engaged":
            self.lifecycle_stage = "adapted"

    def retire(self, reason: str):
        """退出剧情"""
        self.lifecycle_stage = "retired"
        self.retired_at = datetime.now()
        self.retirement_reason = reason


class NPCPool(BaseModel):
    """NPC池（管理所有NPC种子和实例）"""

    # 种子池
    seeds: Dict[str, NPCSeed] = Field(default_factory=dict)

    # 实例池
    instances: Dict[str, NPCInstance] = Field(default_factory=dict)

    # 活跃NPC（未退出的）
    active_npc_ids: List[str] = Field(default_factory=list)

    def add_seed(
        self,
        archetype: str,
        role_in_story: str,
        spawn_conditions: List[str],
        seed_description: str = "",
        generation_constraints: Optional[Dict[str, Any]] = None,
        priority: int = 5
    ) -> NPCSeed:
        """添加NPC种子"""
        seed = NPCSeed(
            archetype=archetype,
            role_in_story=role_in_story,
            spawn_conditions=spawn_conditions,
            seed_description=seed_description,
            generation_constraints=generation_constraints or {},
            priority=priority
        )
        self.seeds[seed.seed_id] = seed
        return seed

    def check_spawn_conditions(self, world_state: Dict[str, Any]) -> List[NPCSeed]:
        """检查哪些种子的生成条件已满足"""
        ready_seeds = []

        for seed in self.seeds.values():
            if seed.status != "dormant":
                continue

            # 简单检查：所有条件都满足
            # TODO: 实现更复杂的条件评估逻辑
            conditions_met = True
            for condition in seed.spawn_conditions:
                # 这里需要实现条件评估器
                # 暂时标记为ready，实际需要根据world_state检查
                pass

            if conditions_met:
                seed.status = "ready"
                ready_seeds.append(seed)

        # 按优先级排序
        ready_seeds.sort(key=lambda s: s.priority, reverse=True)
        return ready_seeds

    def instantiate_npc(
        self,
        seed: NPCSeed,
        generated_data: Dict[str, Any]
    ) -> NPCInstance:
        """实例化NPC（从种子生成实例）"""
        instance = NPCInstance(
            seed_id=seed.seed_id,
            name=generated_data.get("name", "未命名NPC"),
            role=generated_data.get("role", seed.role_in_story),
            archetype=seed.archetype,
            description=generated_data.get("description", ""),
            personality=generated_data.get("personality", []),
            background=generated_data.get("background", ""),
            attributes=generated_data.get("attributes", {}),
            faction=generated_data.get("faction"),
            current_location=generated_data.get("location"),
            goals=generated_data.get("goals", []),
            motivations=generated_data.get("motivations", [])
        )

        # 保存实例
        self.instances[instance.npc_id] = instance
        self.active_npc_ids.append(instance.npc_id)

        # 更新种子状态
        seed.status = "instantiated"
        seed.instantiated_npc_id = instance.npc_id

        return instance

    def get_npc(self, npc_id: str) -> Optional[NPCInstance]:
        """获取NPC实例"""
        return self.instances.get(npc_id)

    def get_active_npcs(self) -> List[NPCInstance]:
        """获取所有活跃NPC"""
        return [
            self.instances[npc_id]
            for npc_id in self.active_npc_ids
            if npc_id in self.instances
        ]

    def get_npcs_at_location(self, location: str) -> List[NPCInstance]:
        """获取某地点的所有NPC"""
        return [
            npc for npc in self.get_active_npcs()
            if npc.current_location == location
        ]

    def get_npcs_by_faction(self, faction: str) -> List[NPCInstance]:
        """获取某势力的所有NPC"""
        return [
            npc for npc in self.get_active_npcs()
            if npc.faction == faction
        ]

    def retire_npc(self, npc_id: str, reason: str):
        """让NPC退出"""
        if npc_id in self.instances:
            npc = self.instances[npc_id]
            npc.retire(reason)

            # 从活跃列表移除
            if npc_id in self.active_npc_ids:
                self.active_npc_ids.remove(npc_id)

    def get_pool_stats(self) -> Dict[str, Any]:
        """获取NPC池统计"""
        return {
            "total_seeds": len(self.seeds),
            "dormant_seeds": len([s for s in self.seeds.values() if s.status == "dormant"]),
            "ready_seeds": len([s for s in self.seeds.values() if s.status == "ready"]),
            "total_instances": len(self.instances),
            "active_npcs": len(self.active_npc_ids),
            "retired_npcs": len([n for n in self.instances.values() if n.lifecycle_stage == "retired"])
        }


class NPCGenerator:
    """NPC生成器（使用LLM生成NPC详细信息）"""

    def __init__(self, llm_client):
        self.llm_client = llm_client

    async def generate_npc_from_seed(
        self,
        seed: NPCSeed,
        world_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """从种子生成完整的NPC数据"""

        prompt = f"""你是一个小说NPC生成器。根据以下信息生成一个详细的NPC角色：

## NPC原型
- 角色类型: {seed.archetype}
- 故事角色: {seed.role_in_story}
- 种子描述: {seed.seed_description}

## 世界背景
{world_context.get('setting_text', '')}

## 生成约束
{seed.generation_constraints}

请生成以下内容（JSON格式）：
1. name: NPC姓名（符合世界观）
2. role: 具体职业/身份
3. description: 外貌和第一印象（100-150字）
4. personality: 性格特质（3-5个关键词）
5. background: 背景故事（150-200字）
6. attributes: 相关属性（根据世界观）
7. goals: 当前目标（2-3个）
8. motivations: 核心动机（2-3个）
9. faction: 所属势力（如果有）
10. location: 当前位置

确保：
- 角色与世界观融合
- 性格鲜明，有记忆点
- 背景与{seed.role_in_story}角色相符
- 不要与主角冲突或重复
"""

        try:
            # 使用LLM生成
            response = await self.llm_client.generate_structured(
                prompt=prompt,
                response_schema={
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "role": {"type": "string"},
                        "description": {"type": "string"},
                        "personality": {"type": "array", "items": {"type": "string"}},
                        "background": {"type": "string"},
                        "attributes": {"type": "object"},
                        "goals": {"type": "array", "items": {"type": "string"}},
                        "motivations": {"type": "array", "items": {"type": "string"}},
                        "faction": {"type": "string"},
                        "location": {"type": "string"}
                    },
                    "required": ["name", "role", "description", "personality", "background"]
                }
            )

            return response

        except Exception as e:
            # 降级：生成基本NPC
            return {
                "name": f"{seed.role_in_story}（未命名）",
                "role": seed.role_in_story,
                "description": seed.seed_description or "一个神秘的角色",
                "personality": ["神秘"],
                "background": "背景未知",
                "attributes": {},
                "goals": [],
                "motivations": [],
                "faction": seed.generation_constraints.get("faction"),
                "location": None
            }
