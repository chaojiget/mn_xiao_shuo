"""
世界生成器
负责生成世界脚手架、区域、地点、POI等
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from models.world_models import (
    POI,
    Faction,
    Location,
    LocationGenerationRequest,
    PacingControl,
    POIGenerationRequest,
    Region,
    RegionGenerationRequest,
    StyleBible,
    SyntaxPreferences,
    WorldGenerationRequest,
    WorldScaffold,
    WritingStyle,
)


class WorldGenerator:
    """世界生成器"""

    def __init__(self, llm_client):
        """
        Args:
            llm_client: LiteLLM客户端实例
        """
        self.llm = llm_client
        # 使用统一配置（settings.world_gen_model），无可用配置时回退到 env
        try:
            from config.settings import settings
            self.default_model = settings.world_gen_model
        except Exception:
            self.default_model = os.getenv("DEFAULT_MODEL", "deepseek/deepseek-v3.1-terminus")

    # ============ 世界生成 ============

    async def generate_world(self, request: WorldGenerationRequest) -> Dict[str, Any]:
        """
        生成完整世界脚手架

        Returns:
            {
                "world": WorldScaffold,
                "regions": List[Region],
                "factions": List[Faction],
                "style_vocabulary": List[dict]
            }
        """

        # 1. 生成世界框架
        world = await self._generate_world_framework(request)

        # 2. 生成区域
        regions = await self._generate_regions(
            world.id, count=request.num_regions, theme=request.theme, novel_type=request.novel_type
        )

        # 3. 生成派系
        factions = await self._generate_factions(
            world.id, regions=regions, novel_type=request.novel_type
        )

        # 4. 生成风格词库
        style_vocab = await self._generate_style_vocabulary(world)

        return {
            "world": world,
            "regions": regions,
            "factions": factions,
            "style_vocabulary": style_vocab,
        }

    async def _generate_world_framework(self, request: WorldGenerationRequest) -> WorldScaffold:
        """生成世界框架"""

        # 获取或创建节奏配置
        pacing_config = request.pacing_config or PacingControl()

        # 获取或创建文风配置
        writing_style_config = request.writing_style_config or WritingStyle()

        # 根据节奏配置调整 prompt
        pacing_hints = self._get_pacing_hints(pacing_config)

        # 根据文风配置调整 prompt
        style_hints = self._get_writing_style_hints(writing_style_config)

        prompt = f"""你是世界设计专家。请生成一个{request.novel_type}类型的世界框架。

**主题**: {request.theme}
**基调**: {request.tone}

**节奏要求**:
{pacing_hints}

**文风要求**:
{style_hints}

请严格按照以下JSON格式输出（不要包含markdown代码块标记）：

{{
    "name": "世界名称",
    "timeline": {{
        "current_era": "当前纪元",
        "major_events": ["重大历史事件1", "重大历史事件2"]
    }},
    "tech_magic_level": {{
        "technology": "科技水平描述（仅科幻）",
        "cultivation_system": "修炼体系描述（仅玄幻）",
        "power_ceiling": "力量上限"
    }},
    "geography_climate": {{
        "overview": "地理气候总览",
        "distinctive_features": ["特色1", "特色2"]
    }},
    "core_conflicts": ["核心冲突1", "核心冲突2", "核心冲突3"],
    "forbidden_rules": ["禁忌规则1", "禁忌规则2"],
    "style_bible": {{
        "tone": "{request.tone}",
        "sensory": ["感官词1", "感官词2", "感官词3", "感官词4", "感官词5"],
        "syntax": {{
            "avg_sentence_len": {pacing_config.avg_sentence_len},
            "prefer_active": {str(pacing_config.prefer_active_voice).lower()},
            "paragraph_rhythm": "{pacing_config.paragraph_rhythm}"
        }},
        "imagery": ["意象词1", "意象词2", "意象词3"],
        "metaphor_patterns": ["比喻模式1", "比喻模式2"]
    }}
}}

要求：
1. 符合{request.novel_type}类型特点
2. 保持{request.tone}的基调
3. sensory词要具体、可感知（视觉/听觉/嗅觉/触觉/温度）
4. 禁忌规则要有游戏机制意义（如"无火把夜行-2感知"）
5. 世界设计要符合节奏要求
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.8, max_tokens=2000
        )

        # 解析JSON
        data = json.loads(response.strip())

        # 构建StyleBible（包含节奏配置和文风配置）
        style_bible = StyleBible(
            tone=data["style_bible"]["tone"],
            sensory=data["style_bible"]["sensory"],
            syntax=SyntaxPreferences(**data["style_bible"]["syntax"]),
            imagery=data["style_bible"].get("imagery"),
            metaphor_patterns=data["style_bible"].get("metaphor_patterns"),
            pacing=pacing_config,  # 添加节奏配置
            writing_style=writing_style_config,  # 添加文风配置
        )

        # 构建WorldScaffold
        world = WorldScaffold(
            id=f"world-{request.novel_id}",
            novel_id=request.novel_id,
            name=data["name"],
            theme=request.theme,
            tone=request.tone,
            timeline=data.get("timeline"),
            tech_magic_level=data.get("tech_magic_level"),
            geography_climate=data.get("geography_climate"),
            core_conflicts=data.get("core_conflicts"),
            forbidden_rules=data.get("forbidden_rules"),
            style_bible=style_bible,
            status="draft",
            version=1,
        )

        return world

    def _get_pacing_hints(self, pacing: PacingControl) -> str:
        """根据节奏配置生成提示文本"""

        hints = []

        # 全局节奏
        global_pace_hints = {
            "slow": "- 整体节奏舒缓，重视细节描写和氛围营造",
            "moderate": "- 整体节奏适中，描写和动作平衡",
            "fast": "- 整体节奏紧凑，聚焦关键事件和行动",
            "varied": "- 整体节奏富有变化，张弛有度",
        }
        hints.append(global_pace_hints[pacing.global_pace])

        # 句法节奏
        if pacing.avg_sentence_len < 15:
            hints.append("- 使用短句，简洁有力")
        elif pacing.avg_sentence_len > 25:
            hints.append("- 使用长句，营造流畅感")
        else:
            hints.append(f"- 平均句长{pacing.avg_sentence_len}字左右")

        # 段落节奏
        paragraph_hints = {
            "staccato": "- 段落短促有力，制造紧张感",
            "varied": "- 段落长短结合，富有节奏变化",
            "flowing": "- 段落流畅舒展，营造沉浸感",
            "mixed": "- 段落风格混合，根据场景灵活调整",
        }
        hints.append(paragraph_hints[pacing.paragraph_rhythm])

        # 场景节奏
        if pacing.description_ratio < 0.3:
            hints.append("- 描写简洁，聚焦动作")
        elif pacing.description_ratio > 0.6:
            hints.append("- 描写丰富，营造画面感")

        if pacing.action_density > 0.7:
            hints.append("- 动作密集，保持紧张感")
        elif pacing.action_density < 0.3:
            hints.append("- 动作舒缓，留出思考空间")

        # 事件节奏
        if pacing.event_frequency > 0.7:
            hints.append("- 事件频繁，情节密集")
        elif pacing.event_frequency < 0.3:
            hints.append("- 事件稀疏，注重日常")

        conflict_hints = {
            "steady": "- 冲突强度稳定",
            "escalating": "- 冲突逐步升级",
            "wave": "- 冲突呈波浪式起伏",
            "burst": "- 冲突突发爆发",
        }
        hints.append(conflict_hints[pacing.conflict_intensity_curve])

        return "\n".join(hints)

    def _get_writing_style_hints(self, style: WritingStyle) -> str:
        """根据文风配置生成提示文本"""

        hints = []

        # 文风类型
        style_type_hints = {
            "classical": "- 文风：古典文言，使用文言句式和雅词",
            "archaic": "- 文风：古风白话，具有古韵但易读",
            "modern": "- 文风：现代白话，简洁明快",
            "poetic": "- 文风：诗意优美，富有意境和美感",
            "vernacular": "- 文风：口语化，贴近日常对话",
            "literary": "- 文风：文学性，注重表达的艺术性",
            "cinematic": "- 文风：镜头感，画面感强烈",
        }
        hints.append(style_type_hints[style.style_type])

        # 词汇难度
        vocab_hints = {
            "simple": "- 用词简单易懂，避免生僻字",
            "moderate": "- 用词适中，兼顾表达力和可读性",
            "advanced": "- 用词高级，使用较为复杂的词汇",
            "archaic": "- 用词古雅，使用古典词汇和雅语",
        }
        hints.append(vocab_hints[style.vocabulary_level])

        # 修辞手法
        if style.use_metaphor:
            hints.append("- 使用比喻手法增强表现力")
        if style.use_personification:
            hints.append("- 使用拟人手法使描写生动")
        if style.use_parallelism:
            hints.append("- 使用排比句式增强气势")
        if style.use_allusion:
            hints.append("- 使用典故增加文化底蕴")

        # 句式特点
        if style.classical_syntax:
            hints.append("- 使用古典句式（倒装、省略等）")
        if style.four_character_phrases:
            hints.append("- 多用四字成语和词组")
        if style.poetic_language:
            hints.append("- 使用诗化语言，富有韵律感")

        # 叙事视角
        pov_hints = {
            "first": "- 叙事视角：第一人称（我）",
            "third_limited": "- 叙事视角：第三人称限知（他/她，只知主角所知）",
            "third_omniscient": "- 叙事视角：第三人称全知（可知所有角色内心）",
        }
        hints.append(pov_hints[style.narrative_pov])

        # 描写风格
        desc_hints = {
            "minimalist": "- 描写极简，只写关键",
            "balanced": "- 描写适度，详略得当",
            "lush": "- 描写丰富，细节充分",
            "ornate": "- 描写华丽，辞藻精美",
        }
        hints.append(desc_hints[style.description_style])

        # 文化背景
        if style.cultural_flavor:
            hints.append(f"- 文化背景：{style.cultural_flavor}")

        return "\n".join(hints)

    async def _generate_regions(
        self, world_id: str, count: int, theme: str, novel_type: str
    ) -> List[Region]:
        """生成区域"""

        prompt = f"""你是世界设计专家。请为{novel_type}世界生成{count}个不同的区域。

**主题**: {theme}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "区域名称",
        "biome": "生态群落（如：冻海海岸、炎漠、迷雾沼泽、云海仙山）",
        "climate": "气候描述",
        "geography": "地形地貌描述",
        "resources": ["资源1", "资源2", "资源3"],
        "danger_level": 3,
        "travel_difficulty": "旅行难度简述",
        "travel_hints": ["提示1", "提示2"],
        "special_rules": ["特殊规则1"],
        "atmosphere": "氛围描述（一句话）"
    }}
]

要求：
1. {count}个区域要有差异性（地形、气候、危险等级）
2. danger_level范围1-10，呈梯度分布
3. 资源要具体（矿物、植物、生物、能量等）
4. 特殊规则要有机制意义
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.9, max_tokens=3000
        )

        # 解析JSON
        data = json.loads(response.strip())

        regions = []
        for i, item in enumerate(data):
            region = Region(
                id=f"{world_id}-region-{i+1:02d}",
                world_id=world_id,
                name=item["name"],
                biome=item["biome"],
                climate=item.get("climate"),
                geography=item.get("geography"),
                resources=item.get("resources"),
                factions=[],  # 稍后关联
                danger_level=item.get("danger_level", 1),
                travel_difficulty=item.get("travel_difficulty"),
                travel_hints=item.get("travel_hints"),
                special_rules=item.get("special_rules"),
                atmosphere=item.get("atmosphere"),
                status="draft",
                canon_locked=False,
            )
            regions.append(region)

        return regions

    async def _generate_factions(
        self, world_id: str, regions: List[Region], novel_type: str
    ) -> List[Faction]:
        """生成派系"""

        region_names = [r.name for r in regions]

        prompt = f"""你是世界设计专家。请为{novel_type}世界生成3-5个主要派系。

**区域**: {', '.join(region_names)}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "派系名称",
        "purpose": "派系目的",
        "ideology": "意识形态/信条",
        "resources": {{
            "wealth": 8,
            "military": 6,
            "influence": 7
        }},
        "territory": ["区域名1", "区域名2"],
        "power_level": 7,
        "relationships": {{}},
        "structure": "组织结构简述",
        "voice_style": "说话风格（如：简短冷淡、华丽正式）",
        "behavior_patterns": ["行为模式1", "行为模式2"]
    }}
]

要求：
1. 3-5个派系，power_level差异化
2. territory填写上面提供的区域名（可重叠）
3. resources的数值1-10
4. 派系之间要有潜在冲突点
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.85, max_tokens=2500
        )

        # 解析JSON
        data = json.loads(response.strip())

        factions = []
        for i, item in enumerate(data):
            faction = Faction(
                id=f"{world_id}-faction-{i+1:02d}",
                world_id=world_id,
                name=item["name"],
                purpose=item["purpose"],
                ideology=item.get("ideology"),
                resources=item.get("resources"),
                territory=item.get("territory"),
                power_level=item.get("power_level", 5),
                relationships=item.get("relationships", {}),
                structure=item.get("structure"),
                key_members=[],  # 稍后生成NPC
                voice_style=item.get("voice_style"),
                behavior_patterns=item.get("behavior_patterns"),
                status="active",
            )
            factions.append(faction)

        # 生成关系矩阵
        await self._generate_faction_relationships(factions)

        return factions

    async def _generate_faction_relationships(self, factions: List[Faction]):
        """生成派系关系"""

        faction_summaries = [f"{f.name}: {f.purpose}" for f in factions]

        prompt = f"""以下是各个派系的信息：

{chr(10).join(faction_summaries)}

请为每个派系生成对其他派系的态度（-10到10，负数敌对，正数友好）。

输出JSON格式（不要包含markdown代码块标记）：

{{
    "派系A名称": {{
        "派系B名称": -5,
        "派系C名称": 3
    }},
    "派系B名称": {{
        "派系A名称": -5,
        "派系C名称": 0
    }}
}}

要求：关系要对称或有合理差异。
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.7, max_tokens=1000
        )

        relationships = json.loads(response.strip())

        # 应用到factions
        for faction in factions:
            if faction.name in relationships:
                faction.relationships = relationships[faction.name]

    async def _generate_style_vocabulary(self, world: WorldScaffold) -> List[Dict[str, Any]]:
        """生成风格词库"""

        prompt = f"""你是文学风格专家。请为以下世界生成风格词库：

**世界**: {world.name}
**主题**: {world.theme}
**基调**: {world.tone}
**已有感官词**: {', '.join(world.style_bible.sensory)}

请生成以下类别的词库（输出JSON数组，不要包含markdown代码块标记）：

[
    {{
        "category": "sensory",
        "subcategory": "visual",
        "content": "具体视觉词",
        "examples": ["使用示例1", "使用示例2"]
    }},
    {{
        "category": "imagery",
        "subcategory": null,
        "content": "意象词",
        "examples": ["使用示例"]
    }},
    {{
        "category": "metaphor",
        "subcategory": null,
        "content": "比喻模式",
        "examples": ["示例"]
    }},
    {{
        "category": "syntax_pattern",
        "subcategory": "opening",
        "content": "开头句式模式",
        "examples": ["示例"]
    }}
]

要求：
1. sensory细分为visual/auditory/olfactory/tactile/temperature
2. 每类生成5-10个词/模式
3. examples要展示具体用法
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.8, max_tokens=2000
        )

        vocab = json.loads(response.strip())
        return vocab

    # ============ 地点生成 ============

    async def generate_locations(
        self, request: LocationGenerationRequest, region: Region, world: WorldScaffold
    ) -> List[Location]:
        """生成地点"""

        types_str = (
            ", ".join(request.types)
            if request.types
            else "landmark, settlement, dungeon, wilderness"
        )

        prompt = f"""你是世界设计专家。请为以下区域生成{request.count}个地点。

**区域**: {region.name}
**生态**: {region.biome}
**危险等级**: {region.danger_level}
**氛围**: {region.atmosphere}

**地点类型**: {types_str}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "地点名称",
        "type": "landmark",
        "macro_description": "宏观描述（1-2句）",
        "geometry": ["几何特征1", "几何特征2"],
        "interactables": ["可交互物1", "可交互物2"],
        "sensory": ["感官节点1", "感官节点2", "感官节点3"],
        "affordances": ["撬门", "搜寻油罐", "攀爬破梯"],
        "controlling_faction": null
    }}
]

要求：
1. geometry描述结构、布局、材质
2. interactables要具体、可互动
3. sensory用五感描写（视听嗅触温）
4. affordances是"动词+对象"形式
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.85, max_tokens=2500
        )

        data = json.loads(response.strip())

        locations = []
        for i, item in enumerate(data):
            location = Location(
                id=f"{region.id}-loc-{i+1:02d}",
                region_id=region.id,
                name=item["name"],
                type=item["type"],
                macro_description=item.get("macro_description"),
                geometry=item.get("geometry"),
                interactables=item.get("interactables"),
                sensory=item.get("sensory"),
                affordances=item.get("affordances"),
                controlling_faction=item.get("controlling_faction"),
                key_npcs=[],
                status="draft",
                canon_locked=False,
                detail_level=0,  # 初始为轮廓
                visit_count=0,
            )
            locations.append(location)

        return locations

    # ============ POI生成 ============

    async def generate_pois(self, request: POIGenerationRequest, location: Location) -> List[POI]:
        """生成POI"""

        types_str = (
            ", ".join(request.types) if request.types else "object, npc, event, hazard, secret"
        )

        prompt = f"""你是世界设计专家。请为以下地点生成{request.count}个兴趣点（POI）。

**地点**: {location.name}
**类型**: {location.type}
**宏观描述**: {location.macro_description}
**可交互物**: {', '.join(location.interactables or [])}

**POI类型**: {types_str}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "POI名称",
        "type": "object",
        "description": "基础描述",
        "details": {{
            "appearance": "外观",
            "condition": "状态"
        }},
        "interaction_type": "examine",
        "requirements": {{"skill": "察觉", "min_value": 3}},
        "risks": ["风险提示"],
        "expected_outcomes": ["可能结果1", "可能结果2"],
        "state": "active"
    }}
]

要求：
1. 类型多样化（object/npc/hazard/secret）
2. requirements可包含skill/item/attribute
3. risks要具体（如"可能触发陷阱"）
"""

        response = await self.llm.generate(
            prompt=prompt, model=self.default_model, temperature=0.85, max_tokens=2000
        )

        data = json.loads(response.strip())

        pois = []
        for i, item in enumerate(data):
            poi = POI(
                id=f"{location.id}-poi-{i+1:02d}",
                location_id=location.id,
                name=item["name"],
                type=item["type"],
                description=item.get("description"),
                details=item.get("details"),
                interaction_type=item.get("interaction_type"),
                requirements=item.get("requirements"),
                risks=item.get("risks"),
                expected_outcomes=item.get("expected_outcomes"),
                state=item.get("state", "active"),
                interacted=False,
            )
            pois.append(poi)

        return pois
