"""
WorldPack加载器
将预生成的WorldPack转换为GameState，用于开始游戏
"""

import gzip
import json
import sqlite3
from typing import Optional
from pathlib import Path

from models.world_pack import WorldPack
from game.game_tools import (
    GameState,
    PlayerState,
    WorldState,
    GameMap,
    MapNode,
    MapEdge,
    Quest as GameQuest,
    QuestObjective as GameQuestObjective,
    InventoryItem
)


class WorldLoader:
    """WorldPack加载器"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    def load_world_pack(self, world_id: str) -> Optional[WorldPack]:
        """从数据库加载WorldPack"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT json_gz FROM worlds WHERE id = ?",
            (world_id,)
        )

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        # 解压缩
        json_gz = row[0]
        json_str = gzip.decompress(json_gz).decode('utf-8')
        data = json.loads(json_str)

        # 反序列化为WorldPack
        return WorldPack(**data)

    def world_pack_to_game_state(self, world_pack: WorldPack) -> GameState:
        """将WorldPack转换为GameState"""

        # 1. 转换地图
        game_map = self._convert_map(world_pack)

        # 2. 创建初始玩家
        player = self._create_initial_player(world_pack)

        # 3. 转换世界状态
        world = self._convert_world_state(world_pack)

        # 4. 转换任务
        quests = self._convert_quests(world_pack)

        # 5. 创建GameState
        state = GameState(
            version="1.0.0",
            turn_number=0,
            player=player,
            world=world,
            quests=quests,
            map=game_map,
            log=[],
            metadata={
                "createdAt": int(world_pack.meta.created_at.timestamp() * 1000),
                "updatedAt": int(world_pack.meta.created_at.timestamp() * 1000),
                "playTime": 0,
                "worldPackId": world_pack.meta.id,
                "worldPackTitle": world_pack.meta.title
            }
        )

        return state

    def _convert_map(self, world_pack: WorldPack) -> GameMap:
        """转换地图"""
        # 转换地点为地图节点
        nodes = []
        for i, location in enumerate(world_pack.locations):
            node = MapNode(
                id=location.id,
                name=location.name,
                shortDesc=location.description or f"{location.biome}地区",
                discovered=i == 0,  # 只有第一个地点是已发现的
                locked=False,
                metadata={
                    "biome": location.biome,
                    "coord": {"x": location.coord.x, "y": location.coord.y},
                    "pois": [poi.dict() for poi in location.pois]
                }
            )
            nodes.append(node)

        # 根据坐标创建边（简单策略：相邻地点连接）
        edges = []
        for i, loc1 in enumerate(world_pack.locations):
            for j, loc2 in enumerate(world_pack.locations[i+1:], start=i+1):
                # 计算距离
                dx = loc1.coord.x - loc2.coord.x
                dy = loc1.coord.y - loc2.coord.y
                distance = (dx*dx + dy*dy) ** 0.5

                # 距离小于30的地点连接
                if distance < 30:
                    edge = MapEdge(
                        fromNode=loc1.id,
                        toNode=loc2.id,
                        bidirectional=True
                    )
                    edges.append(edge)

        # 从第一个地点开始
        current_node_id = world_pack.locations[0].id if world_pack.locations else "start"

        return GameMap(
            nodes=nodes,
            edges=edges,
            currentNodeId=current_node_id
        )

    def _create_initial_player(self, world_pack: WorldPack) -> PlayerState:
        """创建初始玩家"""
        # 根据难度设置初始属性
        difficulty = world_pack.meta.difficulty

        if difficulty == "story":
            hp, stamina, money = 150, 150, 100
        elif difficulty == "hard":
            hp, stamina, money = 80, 80, 30
        else:  # normal
            hp, stamina, money = 100, 100, 50

        # 初始背包
        inventory = [
            InventoryItem(
                id="gold_coin",
                name="金币",
                description="通用货币",
                quantity=money,
                type="misc"
            )
        ]

        # 从第一个地点开始
        start_location = world_pack.locations[0].id if world_pack.locations else "start"

        return PlayerState(
            hp=hp,
            maxHp=hp,
            stamina=stamina,
            maxStamina=stamina,
            traits=["冒险者"],
            inventory=inventory,
            location=start_location,
            money=0  # 金币在背包里
        )

    def _convert_world_state(self, world_pack: WorldPack) -> WorldState:
        """转换世界状态"""
        # 初始只发现第一个地点
        discovered = [world_pack.locations[0].id] if world_pack.locations else []

        return WorldState(
            time=0,
            flags={},
            discoveredLocations=discovered,
            variables={
                "world_pack_id": world_pack.meta.id,
                "world_pack_title": world_pack.meta.title,
                "world_tone": world_pack.meta.tone,
                "world_difficulty": world_pack.meta.difficulty
            },
            theme=world_pack.meta.tone
        )

    def _convert_quests(self, world_pack: WorldPack) -> list:
        """转换任务"""
        game_quests = []

        for quest in world_pack.quests:
            # 转换目标
            objectives = []
            for obj in quest.objectives:
                objectives.append(GameQuestObjective(
                    id=obj.id,
                    description=obj.text,
                    completed=obj.done,
                    required=True  # WorldPack的objective默认都是必需的
                ))

            # 转换为GameQuest
            game_quest = GameQuest(
                id=quest.id,
                quest_id=quest.id,
                title=quest.title,
                description=quest.summary or "完成任务目标",
                status="inactive",  # 初始都是未激活
                hints=[],
                objectives=objectives,
                rewards={
                    "exp": quest.rewards.get("exp", 0) if quest.rewards else 0,
                    "money": quest.rewards.get("gold", 0) if quest.rewards else 0,
                    "items": quest.rewards.get("items", []) if quest.rewards else []
                }
            )

            game_quests.append(game_quest)

        # 激活主线任务
        for quest in game_quests:
            if "main" in quest.id.lower() or len([q for q in game_quests if q.status == "active"]) == 0:
                quest.status = "active"
                break

        return game_quests

    def load_and_convert(self, world_id: str) -> Optional[GameState]:
        """加载WorldPack并转换为GameState（一站式）"""
        world_pack = self.load_world_pack(world_id)
        if not world_pack:
            return None

        return self.world_pack_to_game_state(world_pack)
