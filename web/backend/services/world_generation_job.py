"""
世界生成任务管理
负责管理世界生成的完整流水线，支持断点恢复和进度跟踪
"""

import asyncio
import gzip
import json
import random
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from llm.base import LLMMessage
from utils.logger import get_logger

logger = get_logger(__name__)
from models.world_pack import (
    NPC,
    POI,
    Coord,
    EncounterEntry,
    EncounterTable,
    Location,
    LootEntry,
    LootTable,
    Quest,
    QuestObjective,
    WorldGenerationRequest,
    WorldMeta,
    WorldPack,
)


class WorldGenerationJob:
    """世界生成任务"""

    PHASES = [
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
    ]

    def __init__(
        self,
        job_id: str,
        world_id: str,
        request: WorldGenerationRequest,
        llm_client,
        db_path: str,
        progress_callback: Optional[Callable] = None
    ):
        """
        初始化世界生成任务

        Args:
            job_id: 任务ID
            world_id: 世界ID
            request: 生成请求
            llm_client: LLM 客户端
            db_path: 数据库路径
            progress_callback: 进度回调函数 (phase, progress, message)
        """
        self.job_id = job_id
        self.world_id = world_id
        self.request = request
        self.llm = llm_client
        self.db_path = db_path
        self.progress_callback = progress_callback

        # 生成种子
        if not request.seed:
            request.seed = random.randint(1, 1000000)

        # 初始化状态
        self.current_phase = "QUEUED"
        self.progress = 0.0
        self.error: Optional[str] = None

        # 生成的数据（分阶段累积）
        self.world_meta: Optional[WorldMeta] = None
        self.locations: list[Location] = []
        self.npcs: list[NPC] = []
        self.quests: list[Quest] = []
        self.loot_tables: list[LootTable] = []
        self.encounter_tables: list[EncounterTable] = []
        self.lore: Dict[str, str] = {}

    async def run(self) -> WorldPack:
        """
        执行完整的世界生成流程

        Returns:
            WorldPack: 生成的世界包

        Raises:
            Exception: 生成失败时抛出异常
        """
        try:
            # 1. Outline
            await self._update_phase("OUTLINE", 0.1, "生成世界框架...")
            await self._generate_outline()

            # 2. Locations
            await self._update_phase("LOCATIONS", 0.3, "生成地点...")
            await self._generate_locations()

            # 3. NPCs
            await self._update_phase("NPCS", 0.5, "生成 NPC...")
            await self._generate_npcs()

            # 4. Quests
            await self._update_phase("QUESTS", 0.65, "生成任务...")
            await self._generate_quests()

            # 5. Loot Tables
            await self._update_phase("LOOT_TABLES", 0.75, "生成掉落表...")
            await self._generate_loot_tables()

            # 6. Encounter Tables
            await self._update_phase("ENCOUNTER_TABLES", 0.85, "生成遭遇表...")
            await self._generate_encounter_tables()

            # 7. 构建 WorldPack
            world_pack = WorldPack(
                meta=self.world_meta,
                locations=self.locations,
                npcs=self.npcs,
                quests=self.quests,
                loot_tables=self.loot_tables,
                encounter_tables=self.encounter_tables,
                lore=self.lore,
                index_version=1
            )

            # 8. 校验
            await self._update_phase("INDEXING", 0.9, "校验与索引...")
            problems = world_pack.validate_references()
            if problems:
                raise ValueError(f"世界校验失败:\n" + "\n".join(problems))

            quest_problems = world_pack.validate_quest_dag()
            if quest_problems:
                raise ValueError(f"任务依赖校验失败:\n" + "\n".join(quest_problems))

            # 9. 构建向量索引
            await self._build_index(world_pack)

            # 10. 保存到数据库
            await self._save_world_pack(world_pack)

            # 10. 完成
            await self._update_phase("READY", 1.0, "世界生成完成！")

            return world_pack

        except Exception as e:
            await self._update_phase("FAILED", self.progress, f"生成失败: {str(e)}")
            raise

    async def _generate_outline(self):
        """生成世界框架"""
        prompt = f"""你是世界设计专家。请生成一个跑团游戏的世界框架。

**标题**: {self.request.title}
**基调**: {self.request.tone}
**难度**: {self.request.difficulty}
**种子**: {self.request.seed}

请严格按照以下JSON格式输出（不要包含markdown代码块标记）：

{{
    "name": "世界名称",
    "description": "世界简介（2-3句话）",
    "theme": "主题（如：末日废土、魔法学院、星际探险）",
    "lore_entries": {{
        "history": "历史背景",
        "magic_system": "魔法/科技体系",
        "factions_overview": "主要势力概览"
    }}
}}

要求：
1. 基调与 {self.request.tone} 相符
2. 适合跑团游戏
3. 有足够的探索空间
"""

        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.llm.generate(
            messages=messages,
            temperature=0.8,
            max_tokens=1500
        )

        data = json.loads(response.content.strip())

        # 创建 WorldMeta
        self.world_meta = WorldMeta(
            id=self.world_id,
            title=data["name"],
            seed=self.request.seed,
            tone=self.request.tone,
            difficulty=self.request.difficulty,
            created_at=datetime.now()
        )

        # 保存 lore
        self.lore = data.get("lore_entries", {})

        logger.info(f"[WorldGen] ✅ 世界框架生成完成: {data['name']}")

    async def _generate_locations(self):
        """生成地点"""
        num_locations = self.request.num_locations
        biomes = ["forest", "desert", "swamp", "mountain", "plains", "sea", "city"]

        prompt = f"""你是世界设计专家。请为以下世界生成 {num_locations} 个地点。

**世界**: {self.world_meta.title}
**基调**: {self.request.tone}
**可用生态**: {', '.join(biomes)}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "地点名称",
        "biome": "forest",
        "coord": {{"x": 10, "y": 20}},
        "description": "地点描述",
        "poi_count": 3
    }}
]

要求：
1. 生成 {num_locations} 个地点
2. 坐标范围: x(0-63), y(0-63)
3. biome 必须从可用生态中选择
4. poi_count 范围 2-5
5. 地点要有多样性
"""

        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.llm.generate(
            messages=messages,
            temperature=0.9,
            max_tokens=3000
        )

        data = json.loads(response.content.strip())

        for i, loc_data in enumerate(data[:num_locations]):
            # 创建 Location
            location = Location(
                id=f"{self.world_id}-loc-{i+1:03d}",
                name=loc_data["name"],
                biome=loc_data["biome"],
                coord=Coord(**loc_data["coord"]),
                description=loc_data.get("description"),
                pois=[],
                npcs=[]
            )

            # 生成 POIs
            poi_count = loc_data.get("poi_count", 3)
            for j in range(poi_count):
                poi = POI(
                    id=f"{location.id}-poi-{j+1:02d}",
                    name=f"兴趣点 {j+1}",
                    kind=random.choice(["dungeon", "town", "ruin", "cave", "camp", "landmark"]),
                    coord=Coord(
                        x=loc_data["coord"]["x"] + random.randint(-2, 2),
                        y=loc_data["coord"]["y"] + random.randint(-2, 2)
                    ),
                    hooks=[],
                    discovered=False
                )
                location.pois.append(poi)

            self.locations.append(location)

        logger.info(f"[WorldGen] ✅ 生成了 {len(self.locations)} 个地点")

    async def _generate_npcs(self):
        """生成 NPC"""
        num_npcs = self.request.num_npcs

        # 为每个地点分配 NPC
        location_names = [loc.name for loc in self.locations[:5]]  # 前5个地点

        prompt = f"""你是世界设计专家。请为以下世界生成 {num_npcs} 个 NPC。

**世界**: {self.world_meta.title}
**地点**: {', '.join(location_names)}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "name": "NPC名字",
        "role": "角色（如：商人、守卫、学者）",
        "persona": "性格与说话风格",
        "desires": ["欲望1", "欲望2"],
        "secrets": ["秘密1"],
        "home_location": "地点名称"
    }}
]

要求：
1. 生成 {num_npcs} 个 NPC
2. 角色多样化
3. persona 要具体（包含说话风格）
4. home_location 从提供的地点中选择
"""

        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.llm.generate(
            messages=messages,
            temperature=0.85,
            max_tokens=2500
        )

        data = json.loads(response.content.strip())

        # 创建地点名称到ID的映射
        location_map = {loc.name: loc.id for loc in self.locations}

        for i, npc_data in enumerate(data[:num_npcs]):
            home_name = npc_data.get("home_location")
            home_id = location_map.get(home_name)

            npc = NPC(
                id=f"{self.world_id}-npc-{i+1:03d}",
                name=npc_data["name"],
                role=npc_data["role"],
                persona=npc_data["persona"],
                desires=npc_data.get("desires", []),
                secrets=npc_data.get("secrets", []),
                home_location_id=home_id,
                relationship={},
                memory=[]
            )

            self.npcs.append(npc)

            # 添加 NPC 到地点
            if home_id:
                for loc in self.locations:
                    if loc.id == home_id:
                        loc.npcs.append(npc.id)
                        break

        logger.info(f"[WorldGen] ✅ 生成了 {len(self.npcs)} 个 NPC")

    async def _generate_quests(self):
        """生成任务"""
        num_quests = self.request.num_quests

        prompt = f"""你是世界设计专家。请为以下世界生成 {num_quests} 个任务。

**世界**: {self.world_meta.title}

请严格按照以下JSON数组格式输出（不要包含markdown代码块标记）：

[
    {{
        "title": "任务标题",
        "line": "main",
        "summary": "任务简介",
        "objectives": [
            {{"id": "obj1", "text": "目标描述", "require": []}}
        ],
        "rewards": {{"gold": 100}}
    }}
]

要求：
1. 生成 {num_quests} 个任务
2. line 为 "main" 或 "side"（主线任务 3-4 个）
3. 每个任务 2-4 个目标
4. objectives[].require 可引用同任务其他目标的 id
5. 不要有循环依赖
"""

        messages = [LLMMessage(role="user", content=prompt)]
        response = await self.llm.generate(
            messages=messages,
            temperature=0.8,
            max_tokens=2500
        )

        data = json.loads(response.content.strip())

        for i, quest_data in enumerate(data[:num_quests]):
            objectives = [
                QuestObjective(
                    id=obj["id"],
                    text=obj["text"],
                    done=False,
                    require=obj.get("require", [])
                )
                for obj in quest_data["objectives"]
            ]

            quest = Quest(
                id=f"{self.world_id}-quest-{i+1:03d}",
                title=quest_data["title"],
                line=quest_data["line"],
                summary=quest_data["summary"],
                prereq_quest_ids=[],
                objectives=objectives,
                rewards=quest_data.get("rewards", {}),
                status="available"
            )

            self.quests.append(quest)

        logger.info(f"[WorldGen] ✅ 生成了 {len(self.quests)} 个任务")

    async def _generate_loot_tables(self):
        """生成掉落表"""
        # 简单生成几个通用掉落表
        common_items = ["gold", "potion", "torch", "rope", "ration"]

        for i in range(3):
            entries = [
                LootEntry(
                    item_id=item,
                    weight=random.randint(1, 10),
                    quantity_min=1,
                    quantity_max=random.randint(1, 5)
                )
                for item in random.sample(common_items, 3)
            ]

            table = LootTable(
                id=f"{self.world_id}-loot-{i+1:02d}",
                entries=entries
            )

            self.loot_tables.append(table)

        logger.info(f"[WorldGen] ✅ 生成了 {len(self.loot_tables)} 个掉落表")

    async def _generate_encounter_tables(self):
        """生成遭遇表"""
        biomes = list(set(loc.biome for loc in self.locations))

        for biome in biomes:
            entries = [
                EncounterEntry(
                    encounter_id=f"{biome}_enemy_{i}",
                    weight=random.randint(1, 10),
                    difficulty_modifier=random.uniform(0.8, 1.5)
                )
                for i in range(1, 4)
            ]

            table = EncounterTable(
                id=f"{self.world_id}-enc-{biome}",
                biome=biome,
                time_of_day=None,
                weather=None,
                entries=entries
            )

            self.encounter_tables.append(table)

        logger.info(f"[WorldGen] ✅ 生成了 {len(self.encounter_tables)} 个遭遇表")

    async def _build_index(self, world_pack: WorldPack):
        """构建向量索引"""
        from .world_indexer import create_world_indexer

        indexer = create_world_indexer(self.db_path, self.llm)
        stats = await indexer.build_index(world_pack)

        logger.info(f"[WorldGen] ✅ 索引构建完成: {stats['total_embeddings']} 条记录")

    async def _save_world_pack(self, world_pack: WorldPack):
        """保存 WorldPack 到数据库"""
        # 序列化并压缩
        json_str = world_pack.model_dump_json(indent=2)
        json_gz = gzip.compress(json_str.encode('utf-8'))

        # 保存到数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO worlds (id, title, seed, json_gz, status, updated_at)
                VALUES (?, ?, ?, ?, 'draft', CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    json_gz = excluded.json_gz,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                self.world_id,
                world_pack.meta.title,
                world_pack.meta.seed,
                json_gz
            ))

            conn.commit()
            logger.info(f"[WorldGen] ✅ 世界已保存到数据库: {self.world_id}")

        finally:
            conn.close()

    async def _update_phase(self, phase: str, progress: float, message: str):
        """更新任务阶段"""
        self.current_phase = phase
        self.progress = progress

        # 更新数据库
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO world_generation_jobs (id, world_id, phase, progress, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(id) DO UPDATE SET
                    phase = excluded.phase,
                    progress = excluded.progress,
                    updated_at = CURRENT_TIMESTAMP
            """, (self.job_id, self.world_id, phase, progress))

            conn.commit()

        finally:
            conn.close()

        # 回调
        if self.progress_callback:
            await self.progress_callback(phase, progress, message)

        logger.info(f"[WorldGen] {phase} ({progress*100:.0f}%): {message}")


async def create_world_generation_job(
    request: WorldGenerationRequest,
    llm_client,
    db_path: str,
    progress_callback: Optional[Callable] = None
) -> WorldGenerationJob:
    """
    创建并启动世界生成任务

    Args:
        request: 生成请求
        llm_client: LLM 客户端
        db_path: 数据库路径
        progress_callback: 进度回调

    Returns:
        WorldGenerationJob: 任务实例
    """
    job_id = f"job-{uuid.uuid4().hex[:16]}"
    world_id = f"world-{uuid.uuid4().hex[:16]}"

    job = WorldGenerationJob(
        job_id=job_id,
        world_id=world_id,
        request=request,
        llm_client=llm_client,
        db_path=db_path,
        progress_callback=progress_callback
    )

    return job
