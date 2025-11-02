"""SQLite 数据库操作"""

import sqlite3
import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime

from ..models import WorldState, EventNode, EventArc, Clue, Evidence, Setup


class Database:
    """SQLite 数据库管理器"""

    def __init__(self, db_path: str = None):
        """
        初始化数据库连接

        Args:
            db_path: 数据库文件路径,默认从环境变量获取
        """
        if db_path is None:
            db_url = os.getenv("DATABASE_URL", "sqlite:///./data/sqlite/novel.db")
            # 解析 sqlite:///path 格式
            db_path = db_url.replace("sqlite:///", "")

        # 确保目录存在
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        self.db_path = db_path
        self.conn = None

    def connect(self):
        """连接数据库"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # 支持字典式访问
        return self.conn

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def __enter__(self):
        """上下文管理器"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """退出上下文"""
        self.close()

    def init_schema(self, schema_file: str = "database/schema/core.sql"):
        """
        初始化数据库结构

        Args:
            schema_file: SQL schema 文件路径
        """
        if not self.conn:
            self.connect()

        schema_path = Path(schema_file)
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema 文件不存在: {schema_file}")

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # 执行所有 SQL 语句
        self.conn.executescript(schema_sql)
        self.conn.commit()

    # ==================== 小说元数据 ====================

    def create_novel(
        self,
        novel_id: str,
        title: str,
        novel_type: str,
        setting_json: Dict,
        preference: str = "hybrid"
    ):
        """创建新小说"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO novels (id, title, novel_type, preference, setting_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (novel_id, title, novel_type, preference, json.dumps(setting_json, ensure_ascii=False))
        )
        self.conn.commit()

    def get_novel(self, novel_id: str) -> Optional[Dict]:
        """获取小说信息"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM novels WHERE id = ?", (novel_id,))
        row = cursor.fetchone()

        if row:
            return dict(row)
        return None

    def update_novel_progress(self, novel_id: str, turn: int, total_chapters: int):
        """更新小说进度"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            UPDATE novels
            SET current_turn = ?, total_chapters = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (turn, total_chapters, novel_id)
        )
        self.conn.commit()

    # ==================== 世界状态 ====================

    def save_world_state(self, novel_id: str, world_state: WorldState):
        """保存世界状态"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO world_states (novel_id, turn, timestamp, state_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                novel_id,
                world_state.turn,
                world_state.timestamp,
                json.dumps(world_state.to_dict(), ensure_ascii=False)
            )
        )
        self.conn.commit()

    def load_world_state(self, novel_id: str, turn: Optional[int] = None) -> Optional[Dict]:
        """
        加载世界状态

        Args:
            novel_id: 小说ID
            turn: 回合数,None表示最新状态

        Returns:
            世界状态字典
        """
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        if turn is None:
            # 加载最新状态
            cursor.execute(
                """
                SELECT state_json FROM world_states
                WHERE novel_id = ?
                ORDER BY turn DESC
                LIMIT 1
                """,
                (novel_id,)
            )
        else:
            # 加载指定回合
            cursor.execute(
                """
                SELECT state_json FROM world_states
                WHERE novel_id = ? AND turn = ?
                """,
                (novel_id, turn)
            )

        row = cursor.fetchone()
        if row:
            return json.loads(row["state_json"])
        return None

    # ==================== 事件节点 ====================

    def save_event_node(self, novel_id: str, event: EventNode):
        """保存事件节点"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO event_nodes (
                id, novel_id, arc_id, title, goal,
                prerequisites, required_flags, required_resources,
                effects, rewards,
                tension_delta,
                puzzle_density, skill_checks_variety, failure_grace,
                hint_latency, exploit_resistance, reward_loop,
                arc_progress, theme_echo, conflict_gradient,
                payoff_debt, scene_specificity, pacing_smoothness,
                upgrade_frequency, resource_gain, combat_variety,
                reversal_satisfaction, faction_expansion,
                setups, clues, payoffs,
                status, attempts, description, tags
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?
            )
            """,
            (
                event.id, novel_id, event.arc_id, event.title, event.goal,
                json.dumps(event.prerequisites), json.dumps(event.required_flags),
                json.dumps(event.required_resources),
                json.dumps(event.effects), json.dumps(event.rewards),
                event.tension_delta,
                event.puzzle_density, event.skill_checks_variety, event.failure_grace,
                event.hint_latency, event.exploit_resistance, event.reward_loop,
                event.arc_progress, event.theme_echo, event.conflict_gradient,
                event.payoff_debt, event.scene_specificity, event.pacing_smoothness,
                event.upgrade_frequency, event.resource_gain, event.combat_variety,
                event.reversal_satisfaction, event.faction_expansion,
                json.dumps(event.setups), json.dumps(event.clues), json.dumps(event.payoffs),
                event.status.value, event.attempts, event.description, json.dumps(event.tags)
            )
        )
        self.conn.commit()

    def get_events_by_arc(self, novel_id: str, arc_id: str) -> List[Dict]:
        """获取事件线的所有事件"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM event_nodes WHERE novel_id = ? AND arc_id = ? ORDER BY id",
            (novel_id, arc_id)
        )

        return [dict(row) for row in cursor.fetchall()]

    def update_event_status(self, event_id: str, status: str, attempts: int = None):
        """更新事件状态"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        if attempts is not None:
            cursor.execute(
                "UPDATE event_nodes SET status = ?, attempts = ? WHERE id = ?",
                (status, attempts, event_id)
            )
        else:
            cursor.execute(
                "UPDATE event_nodes SET status = ? WHERE id = ?",
                (status, event_id)
            )
        self.conn.commit()

    # ==================== 章节内容 ====================

    def save_chapter(
        self,
        novel_id: str,
        chapter_num: int,
        content: str,
        title: str = None,
        event_ids: List[str] = None
    ):
        """保存章节"""
        if not self.conn:
            self.connect()

        word_count = len(content)

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO chapters (novel_id, chapter_num, title, content, word_count, event_ids)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                novel_id, chapter_num, title, content, word_count,
                json.dumps(event_ids) if event_ids else None
            )
        )
        self.conn.commit()

    def get_chapter(self, novel_id: str, chapter_num: int) -> Optional[Dict]:
        """获取章节"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chapters WHERE novel_id = ? AND chapter_num = ?",
            (novel_id, chapter_num)
        )

        row = cursor.fetchone()
        if row:
            return dict(row)
        return None

    def get_all_chapters(self, novel_id: str) -> List[Dict]:
        """获取所有章节"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM chapters WHERE novel_id = ? ORDER BY chapter_num",
            (novel_id,)
        )

        return [dict(row) for row in cursor.fetchall()]

    # ==================== 线索与伏笔 ====================

    def save_clue(self, novel_id: str, clue: Clue):
        """保存线索"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO clues (
                id, novel_id, content, type,
                evidence_ids, verification_method, status,
                related_event, leads_to, discovery_requirements,
                discovered_at, verified_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                clue.id, novel_id, clue.content, clue.type,
                json.dumps(clue.evidence_ids), clue.verification_method, clue.status.value,
                clue.related_event, json.dumps(clue.leads_to),
                json.dumps(clue.discovery_requirements),
                clue.discovered_at, clue.verified_at
            )
        )
        self.conn.commit()

    def save_setup(self, novel_id: str, setup: Setup):
        """保存伏笔"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO setup_debts (
                id, novel_id, description, setup_event_id,
                sla_deadline, setup_turn,
                payoff_event_id, payoff_turn,
                status, priority, type
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                setup.id, novel_id, setup.description, setup.setup_event_id,
                setup.sla_deadline, setup.setup_turn,
                setup.payoff_event_id, setup.payoff_turn,
                setup.status.value, setup.priority, setup.type
            )
        )
        self.conn.commit()

    def get_overdue_setups(self, novel_id: str, current_turn: int) -> List[Dict]:
        """获取逾期伏笔"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT * FROM setup_debts
            WHERE novel_id = ?
              AND status != 'paid_off'
              AND (? - setup_turn) > sla_deadline
            ORDER BY priority DESC
            """,
            (novel_id, current_turn)
        )

        return [dict(row) for row in cursor.fetchall()]

    # ==================== 执行日志 ====================

    def log_execution(
        self,
        novel_id: str,
        event_id: str,
        turn: int,
        action_queue: Dict,
        result: Dict,
        success: bool,
        model_used: str = None,
        tokens_used: int = None,
        duration_ms: int = None
    ):
        """记录执行日志"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO execution_logs (
                novel_id, event_id, turn,
                action_queue, result, success,
                model_used, tokens_used, duration_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                novel_id, event_id, turn,
                json.dumps(action_queue, ensure_ascii=False),
                json.dumps(result, ensure_ascii=False),
                1 if success else 0,
                model_used, tokens_used, duration_ms
            )
        )
        self.conn.commit()

    # ==================== 工具方法 ====================

    def vacuum(self):
        """优化数据库"""
        if not self.conn:
            self.connect()

        self.conn.execute("VACUUM")

    def get_stats(self, novel_id: str) -> Dict:
        """获取统计信息"""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor()

        # 章节数
        cursor.execute("SELECT COUNT(*) as count FROM chapters WHERE novel_id = ?", (novel_id,))
        chapter_count = cursor.fetchone()["count"]

        # 事件数
        cursor.execute("SELECT COUNT(*) as count FROM event_nodes WHERE novel_id = ?", (novel_id,))
        event_count = cursor.fetchone()["count"]

        # 完成事件数
        cursor.execute(
            "SELECT COUNT(*) as count FROM event_nodes WHERE novel_id = ? AND status = 'completed'",
            (novel_id,)
        )
        completed_events = cursor.fetchone()["count"]

        # 线索数
        cursor.execute("SELECT COUNT(*) as count FROM clues WHERE novel_id = ?", (novel_id,))
        clue_count = cursor.fetchone()["count"]

        # 逾期伏笔数
        cursor.execute(
            "SELECT COUNT(*) as count FROM setup_debts WHERE novel_id = ? AND status = 'overdue'",
            (novel_id,)
        )
        overdue_setups = cursor.fetchone()["count"]

        return {
            "chapters": chapter_count,
            "events": event_count,
            "completed_events": completed_events,
            "clues": clue_count,
            "overdue_setups": overdue_setups
        }
