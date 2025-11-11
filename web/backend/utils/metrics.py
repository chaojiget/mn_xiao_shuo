"""
轻量埋点/事件记录工具

将关键事件写入 SQLite 的 game_events 表（database/schema/world_generation.sql 定义），
用于后续统计与问题定位。
"""

from __future__ import annotations

import json
import sqlite3
import time
from typing import Any, Dict, Optional

from config.settings import settings
from utils.logger import get_logger

logger = get_logger(__name__)


def record_game_event(
    session_id: str,
    turn: int,
    action: str,
    payload: Optional[Dict[str, Any]] = None,
    result: Optional[Dict[str, Any]] = None,
    latency_ms: Optional[int] = None,
) -> None:
    """记录游戏事件到 SQLite game_events 表。"""
    try:
        db_path = str(settings.database_path)
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO game_events (session_id, turn, action, payload, result, latency_ms)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                int(turn or 0),
                action,
                json.dumps(payload or {}, ensure_ascii=False),
                json.dumps(result or {}, ensure_ascii=False),
                int(latency_ms) if latency_ms is not None else None,
            ),
        )
        conn.commit()
    except Exception as e:
        logger.debug(f"记录 game_event 失败（忽略）：{e}")
    finally:
        try:
            conn.close()
        except Exception:
            pass


class Timer:
    """简单耗时计时器"""

    def __enter__(self):
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb):
        self.ms = int((time.perf_counter() - self._t0) * 1000)
        return False

