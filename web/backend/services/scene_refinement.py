"""
场景细化流水线
多Pass生成：结构 → 感官 → 可供性 → 镜头 → 校验
"""

import json
import os
from typing import Any, Dict, List, Optional

from database.world_db import WorldDatabase

from models.world_models import (
    AffordanceExtractionRequest,
    AffordanceResult,
    DetailLayer,
    Location,
    LocationRefinementRequest,
    RefinementResult,
)


class SceneRefinement:
    """场景细化引擎"""

    def __init__(self, llm_client, world_db: WorldDatabase):
        """
        Args:
            llm_client: LiteLLM客户端
            world_db: 世界数据库
        """
        self.llm = llm_client
        self.db = world_db
        # 使用统一配置（可从 .env / ENV 覆盖）
        try:
            from config.settings import settings

            self.default_model = settings.world_gen_model
        except Exception:
            # 兜底：保留旧逻辑
            self.default_model = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-v3.1-terminus")

    # ============ 主流程 ============

    async def refine_location(
        self, request: LocationRefinementRequest, world_style: Dict[str, Any]
    ) -> RefinementResult:
        """
        细化地点（多Pass流水线）

        Args:
            request: 细化请求
            world_style: 世界风格圣经

        Returns:
            RefinementResult
        """

        # 获取地点
        location = self.db.get_location(request.location_id)
        if not location:
            raise ValueError(f"Location not found: {request.location_id}")

        # 如果已达目标细化等级，跳过
        if location.detail_level >= request.target_detail_level:
            # 读取已有layers
            existing_layers = self.db.get_detail_layers("location", location.id)
            return RefinementResult(
                location_id=location.id,
                detail_level=location.detail_level,
                layers=existing_layers,
                affordances=self._extract_affordances_from_layers(existing_layers),
                narrative_text=None,
            )

        layers = []

        # Pass 1: 结构草稿
        if "structure" in request.passes:
            structure_layer = await self._structure_pass(location, world_style)
            layers.append(structure_layer)
            self.db.save_detail_layer(structure_layer)

        # Pass 2: 感官增益
        if "sensory" in request.passes:
            sensory_layer = await self._sensory_pass(location, world_style)
            layers.append(sensory_layer)
            self.db.save_detail_layer(sensory_layer)

        # Pass 3: 可供性提取
        if "affordance" in request.passes:
            affordance_layer = await self._affordance_pass(location, world_style)
            layers.append(affordance_layer)
            self.db.save_detail_layer(affordance_layer)

        # Pass 4: 镜头语言
        if "cinematic" in request.passes:
            cinematic_layer = await self._cinematic_pass(location, world_style, layers)
            layers.append(cinematic_layer)
            self.db.save_detail_layer(cinematic_layer)

        # 更新location的detail_level
        location.detail_level = request.target_detail_level
        self.db.update_location(location)

        # 提取affordances
        affordances = self._extract_affordances_from_layers(layers)

        # 生成叙事文本（可选）
        narrative_text = await self._generate_narrative_text(location, layers, world_style)

        return RefinementResult(
            location_id=location.id,
            detail_level=location.detail_level,
            layers=layers,
            affordances=affordances,
            narrative_text=narrative_text,
        )

    # ============ 各个Pass ============

    async def _structure_pass(self, location: Location, world_style: Dict[str, Any]) -> DetailLayer:
        """
        Pass 1: 结构草稿
        产出：环境总述、构图层次、主要可互动物、危险/悬念
        """

        prompt = f"""你是场景设计专家。请为以下地点生成结构草稿。

**地点**: {location.name}
**类型**: {location.type}
**宏观描述**: {location.macro_description or '无'}
**已有几何**: {', '.join(location.geometry or [])}
**已有可交互物**: {', '.join(location.interactables or [])}

**风格基调**: {world_style.get('tone', '写实')}

请生成以下结构信息（输出JSON，不要包含markdown代码块标记）：

{{
    "overview": "环境总述（2-3句）",
    "composition_layers": ["远景", "中景", "特写"],
    "key_interactables": ["主要可互动物1", "主要可互动物2"],
    "dangers_suspense": ["潜在危险1", "悬念点1"]
}}

要求：
1. composition_layers描述视觉层次（远→中→近）
2. key_interactables从已有可交互物中筛选或扩展
3. dangers_suspense制造紧张感或好奇心
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.75, max_tokens=800
        )

        content = json.loads(response.strip())

        return DetailLayer(
            id=f"{location.id}-structure",
            target_type="location",
            target_id=location.id,
            layer_type="structure",
            content=content,
            source="generated",
            generated_by_turn=None,
            status="canon",
        )

    async def _sensory_pass(self, location: Location, world_style: Dict[str, Any]) -> DetailLayer:
        """
        Pass 2: 感官增益
        产出：5-8个感官节点（视觉/听觉/嗅觉/触感/温度）
        """

        sensory_vocab = world_style.get("sensory", [])

        prompt = f"""你是场景描写专家。请为以下地点生成感官节点。

**地点**: {location.name}
**宏观**: {location.macro_description or '无'}
**已有感官**: {', '.join(location.sensory or [])}

**风格感官词库**: {', '.join(sensory_vocab)}

请生成5-8个感官节点（输出JSON，不要包含markdown代码块标记）：

{{
    "sensory_nodes": [
        {{
            "sense": "visual",
            "content": "具体视觉细节"
        }},
        {{
            "sense": "auditory",
            "content": "具体听觉细节"
        }},
        {{
            "sense": "olfactory",
            "content": "嗅觉细节"
        }},
        {{
            "sense": "tactile",
            "content": "触感细节"
        }},
        {{
            "sense": "temperature",
            "content": "温度感知"
        }}
    ]
}}

要求：
1. 每个sense至少1个节点
2. 尽量使用风格感官词库的词汇
3. 细节要具体、可感知
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.8, max_tokens=1000
        )

        content = json.loads(response.strip())

        return DetailLayer(
            id=f"{location.id}-sensory",
            target_type="location",
            target_id=location.id,
            layer_type="sensory",
            content=content,
            source="generated",
            status="canon",
        )

    async def _affordance_pass(
        self, location: Location, world_style: Dict[str, Any]
    ) -> DetailLayer:
        """
        Pass 3: 可供性提取
        产出：5-8个可操作项（verb + object + requirement? + risk? + expectedOutcome?）
        """

        geometry = location.geometry or []
        interactables = location.interactables or []

        prompt = f"""你是游戏设计专家。请从以下地点中提取可供性（affordances）。

**地点**: {location.name}
**几何特征**: {', '.join(geometry)}
**可交互物**: {', '.join(interactables)}

请提取5-8个可操作项（输出JSON，不要包含markdown代码块标记）：

{{
    "affordances": [
        {{
            "verb": "撬",
            "object": "木门",
            "requirement": {{"item": "撬棍", "or_skill": "力量≥5"}},
            "risk": "可能损坏门锁",
            "expected_outcome": "打开门，进入内部"
        }},
        {{
            "verb": "搜寻",
            "object": "铜油罐",
            "requirement": null,
            "risk": "油罐可能已空",
            "expected_outcome": "获得灯油或线索"
        }}
    ]
}}

要求：
1. verb要具体（撬/撬开、搜/翻找、聆听、嗅闻、攀爬、查看）
2. object从几何/可交互物中提取
3. requirement可为null或包含skill/item/attribute
4. risk和expected_outcome要合理
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.75, max_tokens=1200
        )

        content = json.loads(response.strip())

        return DetailLayer(
            id=f"{location.id}-affordance",
            target_type="location",
            target_id=location.id,
            layer_type="affordance",
            content=content,
            source="generated",
            status="canon",
        )

    async def _cinematic_pass(
        self, location: Location, world_style: Dict[str, Any], previous_layers: List[DetailLayer]
    ) -> DetailLayer:
        """
        Pass 4: 镜头语言
        产出：镜头切换序列、节奏控制
        """

        # 收集前面的信息
        structure_info = ""
        sensory_info = ""

        for layer in previous_layers:
            if layer.layer_type == "structure":
                structure_info = json.dumps(layer.content, ensure_ascii=False)
            elif layer.layer_type == "sensory":
                sensory_info = json.dumps(layer.content, ensure_ascii=False)

        prompt = f"""你是电影摄影专家。请为以下场景设计镜头语言。

**地点**: {location.name}
**结构信息**: {structure_info}
**感官信息**: {sensory_info}

请设计镜头序列（输出JSON，不要包含markdown代码块标记）：

{{
    "shots": [
        {{
            "type": "establishing",
            "description": "远景：建立空间感",
            "duration": "long"
        }},
        {{
            "type": "medium",
            "description": "中景：展示关键元素",
            "duration": "medium"
        }},
        {{
            "type": "close_up",
            "description": "特写：细节或情绪",
            "duration": "short"
        }}
    ],
    "pacing": {{
        "rhythm": "varied",
        "sentence_lengths": [18, 12, 25, 10],
        "paragraph_breaks": [2, 4]
    }}
}}

要求：
1. 镜头顺序合理（远→中→近，或其他有意图的顺序）
2. duration控制节奏（long/medium/short）
3. pacing的sentence_lengths是建议值
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.7, max_tokens=1000
        )

        content = json.loads(response.strip())

        return DetailLayer(
            id=f"{location.id}-cinematic",
            target_type="location",
            target_id=location.id,
            layer_type="cinematic",
            content=content,
            source="generated",
            status="canon",
        )

    # ============ 可供性提取（单独接口） ============

    async def extract_affordances(self, request: AffordanceExtractionRequest) -> AffordanceResult:
        """
        提取可供性（用于运行时）

        Args:
            request: 包含location_id和character_state

        Returns:
            AffordanceResult
        """

        # 获取地点
        location = self.db.get_location(request.location_id)
        if not location:
            raise ValueError(f"Location not found: {request.location_id}")

        # 获取已有affordance layer
        layers = self.db.get_detail_layers("location", location.id, "affordance")

        if layers:
            # 使用已有的
            affordances = layers[0].content.get("affordances", [])
        else:
            # 动态生成
            affordances = await self._extract_affordances_dynamic(location, request.character_state)

        # 生成suggested_actions（UI chips）
        suggested_actions = self._generate_suggested_actions(
            affordances, request.character_state, request.context
        )

        return AffordanceResult(affordances=affordances, suggested_actions=suggested_actions)

    async def _extract_affordances_dynamic(
        self, location: Location, character_state: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """动态提取可供性"""

        geometry = location.geometry or []
        interactables = location.interactables or []

        char_info = ""
        if character_state:
            char_info = f"\n**角色状态**: {json.dumps(character_state, ensure_ascii=False)}"

        prompt = f"""从以下地点中提取当前可执行的行动：

**地点**: {location.name}
**几何**: {', '.join(geometry)}
**可交互物**: {', '.join(interactables)}{char_info}

输出JSON（不要包含markdown代码块标记）：

{{
    "affordances": [
        {{
            "verb": "动词",
            "object": "对象",
            "requirement": {{"条件"}},
            "risk": "风险",
            "expected_outcome": "结果"
        }}
    ]
}}
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.7, max_tokens=800
        )

        data = json.loads(response.strip())
        return data.get("affordances", [])

    def _generate_suggested_actions(
        self,
        affordances: List[Dict[str, Any]],
        character_state: Optional[Dict[str, Any]],
        context: Optional[Dict[str, Any]],
    ) -> List[str]:
        """
        生成建议行动chips

        Args:
            affordances: 可供性列表
            character_state: 角色状态
            context: 上下文

        Returns:
            简短的动宾短语列表（用于UI chips）
        """

        suggestions = []

        for aff in affordances:
            # 检查requirement
            if self._check_requirement(aff.get("requirement"), character_state):
                # 生成chip文本
                verb = aff.get("verb", "")
                obj = aff.get("object", "")
                chip = f"{verb}{obj}"

                # 添加风险提示
                if aff.get("risk"):
                    chip += f" (⚠️)"

                suggestions.append(chip)

        # 限制数量（3-5个）
        return suggestions[:5]

    def _check_requirement(
        self, requirement: Optional[Dict[str, Any]], character_state: Optional[Dict[str, Any]]
    ) -> bool:
        """检查是否满足前置条件（简化版）"""

        if not requirement:
            return True

        if not character_state:
            return True  # 不确定时允许

        # 简单检查（可扩展）
        # 示例: {"skill": "察觉", "min_value": 3}
        if "skill" in requirement:
            skill_name = requirement["skill"]
            min_value = requirement.get("min_value", 0)
            char_skill = character_state.get("attributes", {}).get(skill_name, 0)
            return char_skill >= min_value

        # 示例: {"item": "撬棍"}
        if "item" in requirement:
            item_name = requirement["item"]
            inventory = character_state.get("inventory", [])
            return item_name in inventory

        return True

    # ============ 辅助方法 ============

    def _extract_affordances_from_layers(self, layers: List[DetailLayer]) -> List[Dict[str, Any]]:
        """从layers中提取affordances"""

        for layer in layers:
            if layer.layer_type == "affordance":
                return layer.content.get("affordances", [])

        return []

    async def _generate_narrative_text(
        self, location: Location, layers: List[DetailLayer], world_style: Dict[str, Any]
    ) -> Optional[str]:
        """
        生成叙事文本（可选）

        根据各个layer生成一段完整的场景描写
        """

        # 收集所有信息
        structure_info = {}
        sensory_info = {}
        cinematic_info = {}

        for layer in layers:
            if layer.layer_type == "structure":
                structure_info = layer.content
            elif layer.layer_type == "sensory":
                sensory_info = layer.content
            elif layer.layer_type == "cinematic":
                cinematic_info = layer.content

        if not structure_info:
            return None

        prompt = f"""你是严谨的叙事引擎。请根据以下信息生成场景描写。

**地点**: {location.name}
**结构**: {json.dumps(structure_info, ensure_ascii=False)}
**感官**: {json.dumps(sensory_info, ensure_ascii=False)}
**镜头**: {json.dumps(cinematic_info, ensure_ascii=False)}

**风格要求**:
- 基调: {world_style.get('tone', '写实')}
- 句长: {world_style.get('syntax', {}).get('avg_sentence_len', 18)}
- 使用感官词: {', '.join(world_style.get('sensory', [])[:5])}

请输出2-3段场景描写（200-300字），遵循「远景→中景→特写」。
禁止发明未授权的物体/事实。避免华丽堆砌。

直接输出文本，不要包含JSON或markdown标记。
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.75, max_tokens=600
        )

        return response.strip()
