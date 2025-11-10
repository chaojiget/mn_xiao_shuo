"""SQLite Store for LangGraph memory

基于 LangGraph BaseStore 的 SQLite 实现
用于持久化存储 Agent 的记忆数据
"""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from langgraph.store.base import BaseStore, Item

logger = logging.getLogger(__name__)


class SqliteStore(BaseStore):
    """SQLite 实现的 LangGraph Store

    功能：
    - 持久化存储 Agent 记忆
    - 支持命名空间（namespace）
    - 支持键值对存储
    - 兼容 LangGraph InMemoryStore API

    使用示例：
        store = SqliteStore("data/memory.db")
        store.put(("users",), "user_123", {"name": "John"})
        value = store.get(("users",), "user_123")
    """

    def __init__(self, db_path: str):
        """初始化 SQLite Store

        Args:
            db_path: SQLite 数据库文件路径
        """
        self.db_path = db_path

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # 初始化数据库
        self._init_db()

        logger.info(f"✅ SqliteStore 初始化完成: {db_path}")

    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS store_items (
                namespace TEXT NOT NULL,
                key TEXT NOT NULL,
                value TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (namespace, key)
            )
        """
        )

        # 创建索引加速查询
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_namespace
            ON store_items(namespace)
        """
        )

        conn.commit()
        conn.close()

    def _namespace_to_str(self, namespace: Tuple[str, ...]) -> str:
        """将 namespace tuple 转换为字符串

        Args:
            namespace: 命名空间元组，如 ("users",) 或 ("users", "preferences")

        Returns:
            命名空间字符串，如 "users" 或 "users:preferences"
        """
        return ":".join(namespace)

    def put(self, namespace: Tuple[str, ...], key: str, value: Dict[str, Any]) -> None:
        """保存数据到 store

        Args:
            namespace: 命名空间元组，如 ("users",)
            key: 键，如 "user_123"
            value: 值，字典类型

        示例：
            store.put(("users",), "user_123", {"name": "John", "age": 30})
        """
        namespace_str = self._namespace_to_str(namespace)
        value_json = json.dumps(value, ensure_ascii=False)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO store_items (namespace, key, value, updated_at)
            VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(namespace, key) DO UPDATE SET
                value = excluded.value,
                updated_at = CURRENT_TIMESTAMP
        """,
            (namespace_str, key, value_json),
        )

        conn.commit()
        conn.close()

        logger.debug(f"📝 Store.put: {namespace_str}/{key}")

    def get(self, namespace: Tuple[str, ...], key: str) -> Optional[Item]:
        """获取数据

        Args:
            namespace: 命名空间元组
            key: 键

        Returns:
            Item 对象（包含 value、created_at、updated_at）或 None

        示例：
            item = store.get(("users",), "user_123")
            if item:
                logger.info(item.value)  # {"name": "John", "age": 30}
        """
        namespace_str = self._namespace_to_str(namespace)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT value, created_at, updated_at
            FROM store_items
            WHERE namespace = ? AND key = ?
        """,
            (namespace_str, key),
        )

        row = cursor.fetchone()
        conn.close()

        if row:
            value = json.loads(row[0])
            logger.debug(f"📖 Store.get: {namespace_str}/{key} -> found")

            return Item(
                value=value, key=key, namespace=namespace, created_at=row[1], updated_at=row[2]
            )
        else:
            logger.debug(f"📖 Store.get: {namespace_str}/{key} -> not found")
            return None

    def delete(self, namespace: Tuple[str, ...], key: str) -> None:
        """删除数据

        Args:
            namespace: 命名空间元组
            key: 键
        """
        namespace_str = self._namespace_to_str(namespace)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM store_items
            WHERE namespace = ? AND key = ?
        """,
            (namespace_str, key),
        )

        conn.commit()
        conn.close()

        logger.debug(f"🗑️  Store.delete: {namespace_str}/{key}")

    def search(self, namespace: Tuple[str, ...]) -> List[Item]:
        """搜索命名空间下的所有数据

        Args:
            namespace: 命名空间元组

        Returns:
            Item 列表

        示例：
            items = store.search(("users",))
            for item in items:
                logger.info(f"{item.key}: {item.value}")
        """
        namespace_str = self._namespace_to_str(namespace)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 支持前缀匹配（如果 namespace 是 ("users",)，匹配 "users" 和 "users:*"）
        cursor.execute(
            """
            SELECT key, value, created_at, updated_at
            FROM store_items
            WHERE namespace = ? OR namespace LIKE ?
            ORDER BY created_at DESC
        """,
            (namespace_str, f"{namespace_str}:%"),
        )

        rows = cursor.fetchall()
        conn.close()

        items = []
        for row in rows:
            items.append(
                Item(
                    key=row[0],
                    value=json.loads(row[1]),
                    namespace=namespace,
                    created_at=row[2],
                    updated_at=row[3],
                )
            )

        logger.debug(f"🔍 Store.search: {namespace_str} -> {len(items)} items")
        return items

    def list_namespaces(self) -> List[str]:
        """列出所有命名空间

        Returns:
            命名空间字符串列表
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT DISTINCT namespace
            FROM store_items
            ORDER BY namespace
        """
        )

        rows = cursor.fetchall()
        conn.close()

        namespaces = [row[0] for row in rows]
        return namespaces

    def clear_namespace(self, namespace: Tuple[str, ...]) -> int:
        """清空整个命名空间

        Args:
            namespace: 命名空间元组

        Returns:
            删除的记录数
        """
        namespace_str = self._namespace_to_str(namespace)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(
            """
            DELETE FROM store_items
            WHERE namespace = ? OR namespace LIKE ?
        """,
            (namespace_str, f"{namespace_str}:%"),
        )

        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()

        logger.info(f"🗑️  Store.clear_namespace: {namespace_str} -> deleted {deleted_count} items")
        return deleted_count

    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计信息

        Returns:
            统计信息字典
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 总记录数
        cursor.execute("SELECT COUNT(*) FROM store_items")
        total_items = cursor.fetchone()[0]

        # 各命名空间的记录数
        cursor.execute(
            """
            SELECT namespace, COUNT(*) as count
            FROM store_items
            GROUP BY namespace
            ORDER BY count DESC
        """
        )
        namespace_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # 数据库大小（页数 * 页大小）
        cursor.execute("PRAGMA page_count")
        page_count = cursor.fetchone()[0]
        cursor.execute("PRAGMA page_size")
        page_size = cursor.fetchone()[0]
        db_size_bytes = page_count * page_size

        conn.close()

        return {
            "total_items": total_items,
            "namespace_counts": namespace_counts,
            "db_size_bytes": db_size_bytes,
            "db_size_mb": round(db_size_bytes / 1024 / 1024, 2),
        }
