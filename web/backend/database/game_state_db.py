"""
游戏状态数据库管理器 - 处理存档、游戏状态持久化
基于 docs/TECHNICAL_IMPLEMENTATION_PLAN.md 的设计
"""

import sqlite3
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path


class GameStateManager:
    """游戏状态管理器 - 处理数据库访问和存档管理"""

    def __init__(self, db_path: str):
        """
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_tables()

    def _ensure_tables(self):
        """确保数据库表存在"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 游戏存档表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS game_saves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL DEFAULT 'default_user',
                    slot_id INTEGER NOT NULL CHECK(slot_id >= 1 AND slot_id <= 10),
                    save_name TEXT NOT NULL,
                    game_state TEXT NOT NULL,
                    metadata TEXT,
                    screenshot_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, slot_id)
                )
            """)

            # 存档快照表（用于回滚）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS save_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    save_id INTEGER NOT NULL,
                    turn_number INTEGER NOT NULL,
                    snapshot_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (save_id) REFERENCES game_saves(id) ON DELETE CASCADE
                )
            """)

            # 自动保存记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auto_saves (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    game_state TEXT NOT NULL,
                    turn_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 会话状态表（内存缓存的补充）
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_states (
                    session_id TEXT PRIMARY KEY,
                    game_state TEXT NOT NULL,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_game_saves_user_id ON game_saves(user_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_save_snapshots_save_id ON save_snapshots(save_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_auto_saves_user_id ON auto_saves(user_id)")

            conn.commit()
            print("✅ 游戏状态数据库表初始化成功")

        except Exception as e:
            print(f"❌ 数据库表初始化失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    # ==================== 会话状态管理 ====================

    def get_session_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从数据库获取会话状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT game_state FROM session_states WHERE session_id = ?
            """, (session_id,))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

        finally:
            conn.close()

    def save_session_state(self, session_id: str, game_state: Dict[str, Any]) -> bool:
        """保存会话状态到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT OR REPLACE INTO session_states (session_id, game_state, last_updated)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (session_id, json.dumps(game_state, ensure_ascii=False)))

            conn.commit()
            return True

        except Exception as e:
            print(f"❌ 保存会话状态失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def delete_session_state(self, session_id: str) -> bool:
        """删除会话状态"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM session_states WHERE session_id = ?", (session_id,))
            conn.commit()
            return True
        finally:
            conn.close()

    # ==================== 存档管理 ====================

    def save_game(
        self,
        user_id: str,
        slot_id: int,
        save_name: str,
        game_state: Dict[str, Any],
        auto_save: bool = False
    ) -> int:
        """
        保存游戏到存档槽位

        Args:
            user_id: 用户ID
            slot_id: 存档槽位（1-10）
            save_name: 存档名称
            game_state: 游戏状态
            auto_save: 是否为自动保存

        Returns:
            存档ID
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # 提取元数据
            metadata = {
                "turn_number": game_state.get("world", {}).get("time", 0),
                "location": game_state.get("player", {}).get("location"),
                "hp": game_state.get("player", {}).get("hp", 100),
                "max_hp": game_state.get("player", {}).get("maxHp", 100),
                "level": game_state.get("player", {}).get("level", 1) if hasattr(game_state.get("player", {}), "level") else 1
            }

            # 插入或更新存档
            cursor.execute("""
                INSERT INTO game_saves (user_id, slot_id, save_name, game_state, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(user_id, slot_id) DO UPDATE SET
                    save_name = ?,
                    game_state = ?,
                    metadata = ?,
                    updated_at = CURRENT_TIMESTAMP
            """, (
                user_id, slot_id, save_name,
                json.dumps(game_state, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False),
                save_name,
                json.dumps(game_state, ensure_ascii=False),
                json.dumps(metadata, ensure_ascii=False)
            ))

            save_id = cursor.lastrowid

            # 如果不是自动保存，创建快照
            if not auto_save and save_id > 0:
                cursor.execute("""
                    INSERT INTO save_snapshots (save_id, turn_number, snapshot_data)
                    VALUES (?, ?, ?)
                """, (save_id, metadata["turn_number"], json.dumps(game_state, ensure_ascii=False)))

            # 如果是自动保存，也记录到auto_saves表
            if auto_save:
                cursor.execute("""
                    INSERT INTO auto_saves (user_id, game_state, turn_number)
                    VALUES (?, ?, ?)
                """, (user_id, json.dumps(game_state, ensure_ascii=False), metadata["turn_number"]))

            conn.commit()
            return save_id

        except Exception as e:
            print(f"❌ 保存游戏失败: {e}")
            conn.rollback()
            raise
        finally:
            conn.close()

    def load_game(self, save_id: int) -> Optional[Dict[str, Any]]:
        """加载存档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT game_state, metadata
                FROM game_saves
                WHERE id = ?
            """, (save_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "game_state": json.loads(row[0]),
                    "metadata": json.loads(row[1]) if row[1] else {}
                }
            return None

        finally:
            conn.close()

    def get_saves(self, user_id: str) -> List[Dict[str, Any]]:
        """获取用户所有存档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, slot_id, save_name, metadata,
                       screenshot_url, created_at, updated_at
                FROM game_saves
                WHERE user_id = ?
                ORDER BY slot_id
            """, (user_id,))

            saves = []
            for row in cursor.fetchall():
                saves.append({
                    "save_id": row[0],
                    "slot_id": row[1],
                    "save_name": row[2],
                    "metadata": json.loads(row[3]) if row[3] else {},
                    "screenshot_url": row[4],
                    "created_at": row[5],
                    "updated_at": row[6]
                })

            return saves

        finally:
            conn.close()

    def delete_save(self, save_id: int) -> bool:
        """删除存档"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("DELETE FROM game_saves WHERE id = ?", (save_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def create_snapshot(self, save_id: int, turn_number: int, game_state: Dict[str, Any]) -> bool:
        """创建存档快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                INSERT INTO save_snapshots (save_id, turn_number, snapshot_data)
                VALUES (?, ?, ?)
            """, (save_id, turn_number, json.dumps(game_state, ensure_ascii=False)))

            conn.commit()
            return True
        except Exception as e:
            print(f"❌ 创建快照失败: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def get_snapshots(self, save_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """获取存档的快照列表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, turn_number, created_at
                FROM save_snapshots
                WHERE save_id = ?
                ORDER BY turn_number DESC
                LIMIT ?
            """, (save_id, limit))

            snapshots = []
            for row in cursor.fetchall():
                snapshots.append({
                    "snapshot_id": row[0],
                    "turn_number": row[1],
                    "created_at": row[2]
                })

            return snapshots

        finally:
            conn.close()

    def load_snapshot(self, snapshot_id: int) -> Optional[Dict[str, Any]]:
        """加载快照"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT snapshot_data FROM save_snapshots WHERE id = ?
            """, (snapshot_id,))

            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
            return None

        finally:
            conn.close()

    # ==================== 自动保存管理 ====================

    def get_latest_autosave(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取最新的自动保存"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                SELECT id, game_state, turn_number, created_at
                FROM auto_saves
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """, (user_id,))

            row = cursor.fetchone()
            if row:
                return {
                    "autosave_id": row[0],
                    "game_state": json.loads(row[1]),
                    "turn_number": row[2],
                    "created_at": row[3]
                }
            return None

        finally:
            conn.close()

    def clean_old_autosaves(self, user_id: str, keep_count: int = 5):
        """清理旧的自动保存（保留最新的N个）"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM auto_saves
                WHERE user_id = ? AND id NOT IN (
                    SELECT id FROM auto_saves
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    LIMIT ?
                )
            """, (user_id, user_id, keep_count))

            conn.commit()
            return cursor.rowcount

        finally:
            conn.close()


# ==================== 会话状态缓存（内存 + 数据库） ====================

class GameStateCache:
    """游戏状态缓存 - 内存缓存 + 数据库持久化"""

    def __init__(self, db_manager: GameStateManager):
        self.db_manager = db_manager
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get_state(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取游戏状态（优先从内存）"""
        # 1. 先查内存缓存
        if session_id in self._cache:
            return self._cache[session_id]

        # 2. 从数据库加载
        state = self.db_manager.get_session_state(session_id)
        if state:
            self._cache[session_id] = state
            return state

        # 3. 返回None（由上层创建新状态）
        return None

    def save_state(self, session_id: str, state: Dict[str, Any]):
        """保存游戏状态（内存 + 数据库）"""
        # 1. 更新内存缓存
        self._cache[session_id] = state

        # 2. 保存到数据库
        self.db_manager.save_session_state(session_id, state)

    def clear_cache(self, session_id: Optional[str] = None):
        """清理缓存"""
        if session_id:
            self._cache.pop(session_id, None)
        else:
            self._cache.clear()

    def get_or_create(self, session_id: str, default_factory) -> Dict[str, Any]:
        """获取或创建新状态"""
        state = self.get_state(session_id)
        if state is None:
            state = default_factory()
            self.save_state(session_id, state)
        return state
