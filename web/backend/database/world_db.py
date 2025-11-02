"""
世界脚手架数据库操作
"""

import sqlite3
import json
from typing import Optional, List, Dict, Any
from pathlib import Path
from datetime import datetime

from ..models.world_models import (
    WorldScaffold, Region, Location, POI, Faction,
    WorldItem, Creature, QuestHook, DetailLayer,
    WorldEvent, StyleVocabulary, CanonConflict
)


class WorldDatabase:
    """世界数据库管理"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_schema()

    def _ensure_schema(self):
        """确保Schema存在"""
        with sqlite3.connect(self.db_path) as conn:
            # 检查主表是否已存在
            cursor = conn.execute("""
                SELECT name FROM sqlite_master
                WHERE type='table' AND name='world_scaffolds'
            """)
            if cursor.fetchone():
                # 表已存在，跳过schema初始化
                return

            # 表不存在，执行schema
            schema_path = Path(__file__).parent.parent.parent / "schema_world_scaffold.sql"
            if not schema_path.exists():
                raise FileNotFoundError(f"Schema文件不存在: {schema_path}")

            with open(schema_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.commit()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ============ 世界脚手架 ============

    def create_world(self, world: WorldScaffold) -> str:
        """创建世界"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO world_scaffolds
                (id, novel_id, name, theme, tone, timeline, tech_magic_level,
                 geography_climate, core_conflicts, forbidden_rules, style_bible, status, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                world.id, world.novel_id, world.name, world.theme, world.tone,
                json.dumps(world.timeline) if world.timeline else None,
                json.dumps(world.tech_magic_level) if world.tech_magic_level else None,
                json.dumps(world.geography_climate) if world.geography_climate else None,
                json.dumps(world.core_conflicts) if world.core_conflicts else None,
                json.dumps(world.forbidden_rules) if world.forbidden_rules else None,
                json.dumps(world.style_bible.dict()),
                world.status, world.version
            ))
            conn.commit()
        return world.id

    def get_world(self, world_id: str) -> Optional[WorldScaffold]:
        """获取世界"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM world_scaffolds WHERE id = ?", (world_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_world(row)

    def get_world_by_novel(self, novel_id: str) -> Optional[WorldScaffold]:
        """根据小说ID获取世界"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM world_scaffolds WHERE novel_id = ? ORDER BY created_at DESC LIMIT 1",
                (novel_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_world(row)

    def update_world(self, world: WorldScaffold):
        """更新世界"""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE world_scaffolds SET
                    name = ?, theme = ?, tone = ?, timeline = ?, tech_magic_level = ?,
                    geography_climate = ?, core_conflicts = ?, forbidden_rules = ?,
                    style_bible = ?, status = ?, version = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                world.name, world.theme, world.tone,
                json.dumps(world.timeline) if world.timeline else None,
                json.dumps(world.tech_magic_level) if world.tech_magic_level else None,
                json.dumps(world.geography_climate) if world.geography_climate else None,
                json.dumps(world.core_conflicts) if world.core_conflicts else None,
                json.dumps(world.forbidden_rules) if world.forbidden_rules else None,
                json.dumps(world.style_bible.dict()),
                world.status, world.version,
                world.id
            ))
            conn.commit()

    def _row_to_world(self, row: sqlite3.Row) -> WorldScaffold:
        """转换行到WorldScaffold"""
        return WorldScaffold(
            id=row['id'],
            novel_id=row['novel_id'],
            name=row['name'],
            theme=row['theme'],
            tone=row['tone'],
            timeline=json.loads(row['timeline']) if row['timeline'] else None,
            tech_magic_level=json.loads(row['tech_magic_level']) if row['tech_magic_level'] else None,
            geography_climate=json.loads(row['geography_climate']) if row['geography_climate'] else None,
            core_conflicts=json.loads(row['core_conflicts']) if row['core_conflicts'] else None,
            forbidden_rules=json.loads(row['forbidden_rules']) if row['forbidden_rules'] else None,
            style_bible=json.loads(row['style_bible']),
            status=row['status'],
            version=row['version'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ============ 区域 ============

    def create_region(self, region: Region) -> str:
        """创建区域"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO regions
                (id, world_id, name, biome, climate, geography, resources, factions,
                 danger_level, travel_difficulty, travel_hints, special_rules, atmosphere,
                 status, canon_locked)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                region.id, region.world_id, region.name, region.biome,
                region.climate, region.geography,
                json.dumps(region.resources) if region.resources else None,
                json.dumps(region.factions) if region.factions else None,
                region.danger_level, region.travel_difficulty,
                json.dumps(region.travel_hints) if region.travel_hints else None,
                json.dumps(region.special_rules) if region.special_rules else None,
                region.atmosphere, region.status, 1 if region.canon_locked else 0
            ))
            conn.commit()
        return region.id

    def get_regions_by_world(self, world_id: str) -> List[Region]:
        """获取世界的所有区域"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM regions WHERE world_id = ? ORDER BY created_at",
                (world_id,)
            ).fetchall()

            return [self._row_to_region(row) for row in rows]

    def get_region(self, region_id: str) -> Optional[Region]:
        """获取区域"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM regions WHERE id = ?", (region_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_region(row)

    def _row_to_region(self, row: sqlite3.Row) -> Region:
        """转换行到Region"""
        return Region(
            id=row['id'],
            world_id=row['world_id'],
            name=row['name'],
            biome=row['biome'],
            climate=row['climate'],
            geography=row['geography'],
            resources=json.loads(row['resources']) if row['resources'] else None,
            factions=json.loads(row['factions']) if row['factions'] else None,
            danger_level=row['danger_level'],
            travel_difficulty=row['travel_difficulty'],
            travel_hints=json.loads(row['travel_hints']) if row['travel_hints'] else None,
            special_rules=json.loads(row['special_rules']) if row['special_rules'] else None,
            atmosphere=row['atmosphere'],
            status=row['status'],
            canon_locked=bool(row['canon_locked']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ============ 地点 ============

    def create_location(self, location: Location) -> str:
        """创建地点"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO locations
                (id, region_id, name, type, macro_description, geometry, interactables,
                 sensory, affordances, controlling_faction, key_npcs, status,
                 canon_locked, detail_level, visit_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                location.id, location.region_id, location.name, location.type,
                location.macro_description,
                json.dumps(location.geometry) if location.geometry else None,
                json.dumps(location.interactables) if location.interactables else None,
                json.dumps(location.sensory) if location.sensory else None,
                json.dumps(location.affordances) if location.affordances else None,
                location.controlling_faction,
                json.dumps(location.key_npcs) if location.key_npcs else None,
                location.status, 1 if location.canon_locked else 0,
                location.detail_level, location.visit_count
            ))
            conn.commit()
        return location.id

    def get_locations_by_region(self, region_id: str) -> List[Location]:
        """获取区域的所有地点"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM locations WHERE region_id = ? ORDER BY created_at",
                (region_id,)
            ).fetchall()

            return [self._row_to_location(row) for row in rows]

    def get_location(self, location_id: str) -> Optional[Location]:
        """获取地点"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT * FROM locations WHERE id = ?", (location_id,)
            ).fetchone()

            if not row:
                return None

            return self._row_to_location(row)

    def update_location(self, location: Location):
        """更新地点"""
        with self._get_conn() as conn:
            conn.execute("""
                UPDATE locations SET
                    name = ?, type = ?, macro_description = ?, geometry = ?,
                    interactables = ?, sensory = ?, affordances = ?,
                    controlling_faction = ?, key_npcs = ?, status = ?,
                    canon_locked = ?, detail_level = ?, visit_count = ?,
                    first_visited_turn = ?, last_visited_turn = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (
                location.name, location.type, location.macro_description,
                json.dumps(location.geometry) if location.geometry else None,
                json.dumps(location.interactables) if location.interactables else None,
                json.dumps(location.sensory) if location.sensory else None,
                json.dumps(location.affordances) if location.affordances else None,
                location.controlling_faction,
                json.dumps(location.key_npcs) if location.key_npcs else None,
                location.status, 1 if location.canon_locked else 0,
                location.detail_level, location.visit_count,
                location.first_visited_turn, location.last_visited_turn,
                location.id
            ))
            conn.commit()

    def _row_to_location(self, row: sqlite3.Row) -> Location:
        """转换行到Location"""
        return Location(
            id=row['id'],
            region_id=row['region_id'],
            name=row['name'],
            type=row['type'],
            macro_description=row['macro_description'],
            geometry=json.loads(row['geometry']) if row['geometry'] else None,
            interactables=json.loads(row['interactables']) if row['interactables'] else None,
            sensory=json.loads(row['sensory']) if row['sensory'] else None,
            affordances=json.loads(row['affordances']) if row['affordances'] else None,
            controlling_faction=row['controlling_faction'],
            key_npcs=json.loads(row['key_npcs']) if row['key_npcs'] else None,
            status=row['status'],
            canon_locked=bool(row['canon_locked']),
            detail_level=row['detail_level'],
            visit_count=row['visit_count'],
            first_visited_turn=row['first_visited_turn'],
            last_visited_turn=row['last_visited_turn'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ============ POI ============

    def create_poi(self, poi: POI) -> str:
        """创建POI"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO pois
                (id, location_id, name, type, description, details, interaction_type,
                 requirements, risks, expected_outcomes, state, interacted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                poi.id, poi.location_id, poi.name, poi.type,
                poi.description,
                json.dumps(poi.details) if poi.details else None,
                poi.interaction_type,
                json.dumps(poi.requirements) if poi.requirements else None,
                json.dumps(poi.risks) if poi.risks else None,
                json.dumps(poi.expected_outcomes) if poi.expected_outcomes else None,
                poi.state, 1 if poi.interacted else 0
            ))
            conn.commit()
        return poi.id

    def get_pois_by_location(self, location_id: str) -> List[POI]:
        """获取地点的所有POI"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM pois WHERE location_id = ? ORDER BY created_at",
                (location_id,)
            ).fetchall()

            return [self._row_to_poi(row) for row in rows]

    def _row_to_poi(self, row: sqlite3.Row) -> POI:
        """转换行到POI"""
        return POI(
            id=row['id'],
            location_id=row['location_id'],
            name=row['name'],
            type=row['type'],
            description=row['description'],
            details=json.loads(row['details']) if row['details'] else None,
            interaction_type=row['interaction_type'],
            requirements=json.loads(row['requirements']) if row['requirements'] else None,
            risks=json.loads(row['risks']) if row['risks'] else None,
            expected_outcomes=json.loads(row['expected_outcomes']) if row['expected_outcomes'] else None,
            state=row['state'],
            interacted=bool(row['interacted']),
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )

    # ============ 细化层 ============

    def save_detail_layer(self, layer: DetailLayer) -> str:
        """保存细化层"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO detail_layers
                (id, target_type, target_id, layer_type, content, source,
                 generated_by_turn, player_id, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                layer.id, layer.target_type, layer.target_id, layer.layer_type,
                json.dumps(layer.content), layer.source,
                layer.generated_by_turn, layer.player_id, layer.status
            ))
            conn.commit()
        return layer.id

    def get_detail_layers(
        self,
        target_type: str,
        target_id: str,
        layer_type: Optional[str] = None
    ) -> List[DetailLayer]:
        """获取细化层"""
        with self._get_conn() as conn:
            if layer_type:
                rows = conn.execute(
                    """SELECT * FROM detail_layers
                       WHERE target_type = ? AND target_id = ? AND layer_type = ?
                       ORDER BY created_at""",
                    (target_type, target_id, layer_type)
                ).fetchall()
            else:
                rows = conn.execute(
                    """SELECT * FROM detail_layers
                       WHERE target_type = ? AND target_id = ?
                       ORDER BY created_at""",
                    (target_type, target_id)
                ).fetchall()

            return [self._row_to_detail_layer(row) for row in rows]

    def _row_to_detail_layer(self, row: sqlite3.Row) -> DetailLayer:
        """转换行到DetailLayer"""
        return DetailLayer(
            id=row['id'],
            target_type=row['target_type'],
            target_id=row['target_id'],
            layer_type=row['layer_type'],
            content=json.loads(row['content']),
            source=row['source'],
            generated_by_turn=row['generated_by_turn'],
            player_id=row['player_id'],
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
        )

    # ============ 派系 ============

    def create_faction(self, faction: Faction) -> str:
        """创建派系"""
        with self._get_conn() as conn:
            conn.execute("""
                INSERT INTO factions
                (id, world_id, name, purpose, ideology, resources, territory,
                 power_level, relationships, structure, key_members, voice_style,
                 behavior_patterns, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                faction.id, faction.world_id, faction.name, faction.purpose,
                faction.ideology,
                json.dumps(faction.resources) if faction.resources else None,
                json.dumps(faction.territory) if faction.territory else None,
                faction.power_level,
                json.dumps(faction.relationships) if faction.relationships else None,
                faction.structure,
                json.dumps(faction.key_members) if faction.key_members else None,
                faction.voice_style,
                json.dumps(faction.behavior_patterns) if faction.behavior_patterns else None,
                faction.status
            ))
            conn.commit()
        return faction.id

    def get_factions_by_world(self, world_id: str) -> List[Faction]:
        """获取世界的所有派系"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT * FROM factions WHERE world_id = ? ORDER BY power_level DESC",
                (world_id,)
            ).fetchall()

            return [self._row_to_faction(row) for row in rows]

    def _row_to_faction(self, row: sqlite3.Row) -> Faction:
        """转换行到Faction"""
        return Faction(
            id=row['id'],
            world_id=row['world_id'],
            name=row['name'],
            purpose=row['purpose'],
            ideology=row['ideology'],
            resources=json.loads(row['resources']) if row['resources'] else None,
            territory=json.loads(row['territory']) if row['territory'] else None,
            power_level=row['power_level'],
            relationships=json.loads(row['relationships']) if row['relationships'] else None,
            structure=row['structure'],
            key_members=json.loads(row['key_members']) if row['key_members'] else None,
            voice_style=row['voice_style'],
            behavior_patterns=json.loads(row['behavior_patterns']) if row['behavior_patterns'] else None,
            status=row['status'],
            created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None,
            updated_at=datetime.fromisoformat(row['updated_at']) if row['updated_at'] else None
        )
