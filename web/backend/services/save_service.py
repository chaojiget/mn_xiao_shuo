"""游戏存档服务

Phase 2 - 存档系统实现
实现游戏的保存、加载、删除、快照等功能
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class SaveService:
    """游戏存档服务

    功能:
    - 保存游戏到指定槽位 (1-10)
    - 加载游戏存档
    - 获取用户所有存档列表
    - 删除存档
    - 创建存档快照（用于回滚）
    - 自动保存
    """

    def __init__(self, db_path: str):
        """初始化存档服务

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """确保数据库文件存在"""
        db_file = Path(self.db_path)
        if not db_file.exists():
            raise FileNotFoundError(f"数据库文件不存在: {self.db_path}")

    def save_game(
        self,
        user_id: str,
        slot_id: int,
        save_name: str,
        game_state: Dict[str, Any],
        auto_save: bool = False,
    ) -> int:
        """保存游戏到存档槽位

        Args:
            user_id: 用户ID
            slot_id: 存档槽位 (1-10)
            save_name: 存档名称
            game_state: 完整游戏状态字典
            auto_save: 是否为自动保存

        Returns:
            save_id: 存档ID

        Raises:
            ValueError: 如果 slot_id 不在 1-10 范围内
        """
        # slot_id 0 保留给自动保存
        if not 0 <= slot_id <= 10:
            raise ValueError(f"存档槽位必须在 0-10 之间（0为自动保存），当前: {slot_id}")

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 提取元数据 - 优化以支持多种游戏状态格式
            player = game_state.get("player", {})
            world = game_state.get("world", {})
            game_map = game_state.get("map", {})

            # 回合数：优先使用 world.time，其次 turn_number
            turn_number = world.get("time", game_state.get("turn_number", 0))

            # 位置：尝试多种来源
            location = None
            # 1. 从 player.location 获取
            if player.get("location"):
                location = player.get("location")
            # 2. 从 map.currentNodeId 查找节点名称
            elif game_map.get("currentNodeId") and game_map.get("nodes"):
                current_node_id = game_map.get("currentNodeId")
                for node in game_map.get("nodes", []):
                    if node.get("id") == current_node_id:
                        location = node.get("name", current_node_id)
                        break
            # 3. 从 world.current_location 获取
            elif world.get("current_location"):
                location = world.get("current_location")

            metadata = {
                "turn_number": turn_number,
                "playtime": game_state.get("playtime", 0),
                "location": location,
                "level": player.get("level", 1),
                "hp": player.get("hp", 100),
                "max_hp": player.get("maxHp", player.get("max_hp", 100)),  # 支持 maxHp 和 max_hp
            }

            # 序列化游戏状态和元数据
            game_state_json = json.dumps(game_state, ensure_ascii=False)
            metadata_json = json.dumps(metadata, ensure_ascii=False)

            # 插入或更新存档
            cursor.execute(
                """
                INSERT INTO game_saves (user_id, slot_id, save_name, game_state, metadata, updated_at)
                VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, slot_id) DO UPDATE SET
                    save_name = excluded.save_name,
                    game_state = excluded.game_state,
                    metadata = excluded.metadata,
                    updated_at = CURRENT_TIMESTAMP
            """,
                (user_id, slot_id, save_name, game_state_json, metadata_json),
            )

            # 获取存档ID
            cursor.execute(
                "SELECT id FROM game_saves WHERE user_id = ? AND slot_id = ?", (user_id, slot_id)
            )
            row = cursor.fetchone()
            save_id = row[0] if row else cursor.lastrowid

            # 如果不是自动保存，创建快照
            if not auto_save:
                turn_number = game_state.get("turn_number", 0)
                snapshot_json = json.dumps(game_state, ensure_ascii=False)

                cursor.execute(
                    """
                    INSERT INTO save_snapshots (save_id, turn_number, snapshot_data)
                    VALUES (?, ?, ?)
                """,
                    (save_id, turn_number, snapshot_json),
                )

            conn.commit()
            return save_id

        finally:
            conn.close()

    def load_game(self, save_id: int) -> Optional[Dict[str, Any]]:
        """加载游戏存档

        Args:
            save_id: 存档ID

        Returns:
            包含游戏状态和元数据的字典，如果存档不存在返回 None
            {
                "game_state": {...},
                "metadata": {...},
                "save_info": {"save_id": int, "slot_id": int, "save_name": str, ...}
            }
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, slot_id, save_name, game_state, metadata,
                       screenshot_url, created_at, updated_at
                FROM game_saves
                WHERE id = ?
            """,
                (save_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            game_state = json.loads(row[3])
            metadata = json.loads(row[4]) if row[4] else {}

            return {
                "game_state": game_state,
                "metadata": metadata,
                "save_info": {
                    "save_id": row[0],
                    "slot_id": row[1],
                    "save_name": row[2],
                    "screenshot_url": row[5],
                    "created_at": row[6],
                    "updated_at": row[7],
                },
            }

        finally:
            conn.close()

    def get_saves(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户的所有存档列表

        Args:
            user_id: 用户ID

        Returns:
            存档列表，按槽位排序
            每个元素包含: save_id, slot_id, save_name, metadata, screenshot_url, created_at, updated_at
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, slot_id, save_name, metadata,
                       screenshot_url, created_at, updated_at
                FROM game_saves
                WHERE user_id = ?
                ORDER BY slot_id
            """,
                (user_id,),
            )

            saves = []
            for row in cursor.fetchall():
                metadata = json.loads(row[3]) if row[3] else {}

                saves.append(
                    {
                        "save_id": row[0],
                        "slot_id": row[1],
                        "save_name": row[2],
                        "metadata": metadata,
                        "screenshot_url": row[4],
                        "created_at": row[5],
                        "updated_at": row[6],
                    }
                )

            return saves

        finally:
            conn.close()

    def delete_save(self, save_id: int) -> bool:
        """删除存档

        Args:
            save_id: 存档ID

        Returns:
            是否删除成功
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM game_saves WHERE id = ?", (save_id,))
            conn.commit()

            # 检查是否删除了行
            return cursor.rowcount > 0

        finally:
            conn.close()

    def create_snapshot(self, save_id: int, turn_number: int, game_state: Dict[str, Any]) -> int:
        """为存档创建快照

        Args:
            save_id: 存档ID
            turn_number: 回合数
            game_state: 游戏状态

        Returns:
            快照ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            snapshot_json = json.dumps(game_state, ensure_ascii=False)

            cursor.execute(
                """
                INSERT INTO save_snapshots (save_id, turn_number, snapshot_data)
                VALUES (?, ?, ?)
            """,
                (save_id, turn_number, snapshot_json),
            )

            conn.commit()
            return cursor.lastrowid

        finally:
            conn.close()

    def get_snapshots(self, save_id: int) -> List[Dict[str, Any]]:
        """获取存档的所有快照

        Args:
            save_id: 存档ID

        Returns:
            快照列表，按回合数排序
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT id, turn_number, created_at
                FROM save_snapshots
                WHERE save_id = ?
                ORDER BY turn_number DESC
            """,
                (save_id,),
            )

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append(
                    {"snapshot_id": row[0], "turn_number": row[1], "created_at": row[2]}
                )

            return snapshots

        finally:
            conn.close()

    def load_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """加载快照数据

        Args:
            snapshot_id: 快照ID

        Returns:
            游戏状态字典，如果不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                SELECT snapshot_data
                FROM save_snapshots
                WHERE id = ?
            """,
                (snapshot_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return json.loads(row[0])

        finally:
            conn.close()

    def auto_save(self, user_id: str, game_state: Dict[str, Any], turn_number: int) -> int:
        """自动保存游戏

        自动保存不占用存档槽位，保存到独立的 auto_saves 表

        Args:
            user_id: 用户ID
            game_state: 游戏状态
            turn_number: 回合数

        Returns:
            自动保存ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            game_state_json = json.dumps(game_state, ensure_ascii=False)

            cursor.execute(
                """
                INSERT INTO auto_saves (user_id, game_state, turn_number)
                VALUES (?, ?, ?)
            """,
                (user_id, game_state_json, turn_number),
            )

            conn.commit()
            return cursor.lastrowid

        finally:
            conn.close()

    def get_latest_auto_save(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取最新的自动保存

        Args:
            user_id: 用户ID

        Returns:
            包含游戏状态和元数据的字典，如果不存在返回 None
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 使用 ID 排序而不是 created_at，因为 ID 是自增的，更可靠
            cursor.execute(
                """
                SELECT id, game_state, turn_number, created_at
                FROM auto_saves
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT 1
            """,
                (user_id,),
            )

            row = cursor.fetchone()
            if not row:
                return None

            return {
                "auto_save_id": row[0],
                "game_state": json.loads(row[1]),
                "turn_number": row[2],
                "created_at": row[3],
            }

        finally:
            conn.close()

    def cleanup_old_auto_saves(self, user_id: str, keep_count: int = 5) -> int:
        """清理旧的自动保存，只保留最近的 N 个

        Args:
            user_id: 用户ID
            keep_count: 保留的自动保存数量

        Returns:
            删除的记录数
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 获取要保留的 ID（使用 ID 排序）
            cursor.execute(
                """
                SELECT id FROM auto_saves
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
            """,
                (user_id, keep_count),
            )

            keep_ids = [row[0] for row in cursor.fetchall()]

            if not keep_ids:
                return 0

            # 删除其他的
            placeholders = ",".join("?" * len(keep_ids))
            cursor.execute(
                f"""
                DELETE FROM auto_saves
                WHERE user_id = ? AND id NOT IN ({placeholders})
            """,
                [user_id] + keep_ids,
            )

            conn.commit()
            return cursor.rowcount

        finally:
            conn.close()
