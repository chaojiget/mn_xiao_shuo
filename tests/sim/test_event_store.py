"""
测试 EventStore 事件溯源

测试事件追加、查询、持久化等功能。
"""

import sys
import tempfile
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.event_store import Event, EventStore


class TestEvent:
    """测试 Event 数据类"""

    def test_event_creation(self):
        """测试事件创建"""
        event = Event(
            tick=1,
            actor="player",
            action="move",
            payload={"to": "room1", "from": "room0"},
            seed="seed/1"
        )

        assert event.tick == 1
        assert event.actor == "player"
        assert event.action == "move"
        assert event.payload == {"to": "room1", "from": "room0"}
        assert event.seed == "seed/1"

    def test_event_repr(self):
        """测试事件字符串表示"""
        event = Event(
            tick=5,
            actor="npc",
            action="talk",
            payload={"text": "Hello"},
            seed="seed/5"
        )

        assert "t=5" in repr(event)
        assert "actor='npc'" in repr(event)
        assert "action='talk'" in repr(event)


class TestEventStore:
    """测试 EventStore 类"""

    def test_append_and_count(self):
        """测试追加事件和计数"""
        store = EventStore()
        assert store.count() == 0

        store.append(Event(
            tick=1, actor="player", action="move",
            payload={"to": "room1"}, seed="seed/1"
        ))

        assert store.count() == 1

        store.append(Event(
            tick=2, actor="npc", action="talk",
            payload={"text": "hello"}, seed="seed/2"
        ))

        assert store.count() == 2

    def test_get_all_events(self):
        """测试获取所有事件"""
        store = EventStore()

        store.append(Event(
            tick=1, actor="player", action="move",
            payload={"to": "room1"}, seed="seed/1"
        ))
        store.append(Event(
            tick=2, actor="npc", action="talk",
            payload={"text": "hello"}, seed="seed/2"
        ))

        events = store.get_events()
        assert len(events) == 2
        assert events[0].tick == 1
        assert events[1].tick == 2

    def test_get_events_by_time_range(self):
        """测试按时间范围查询事件"""
        store = EventStore()

        # 添加多个事件
        for i in range(1, 11):
            store.append(Event(
                tick=i, actor="player", action="move",
                payload={"step": i}, seed=f"seed/{i}"
            ))

        # 测试从指定时间开始
        events = store.get_events(from_tick=5)
        assert len(events) == 6  # tick 5-10
        assert events[0].tick == 5

        # 测试时间范围
        events = store.get_events(from_tick=3, to_tick=7)
        assert len(events) == 5  # tick 3-7
        assert events[0].tick == 3
        assert events[-1].tick == 7

        # 测试精确时间点
        events = store.get_events(from_tick=5, to_tick=5)
        assert len(events) == 1
        assert events[0].tick == 5

    def test_get_by_actor(self):
        """测试按执行者查询"""
        store = EventStore()

        store.append(Event(
            tick=1, actor="player", action="move",
            payload={}, seed="seed/1"
        ))
        store.append(Event(
            tick=2, actor="npc", action="talk",
            payload={}, seed="seed/2"
        ))
        store.append(Event(
            tick=3, actor="player", action="attack",
            payload={}, seed="seed/3"
        ))

        # 查询玩家事件
        player_events = store.get_by_actor("player")
        assert len(player_events) == 2
        assert all(e.actor == "player" for e in player_events)

        # 查询 NPC 事件
        npc_events = store.get_by_actor("npc")
        assert len(npc_events) == 1
        assert npc_events[0].action == "talk"

    def test_get_by_action(self):
        """测试按动作类型查询"""
        store = EventStore()

        store.append(Event(
            tick=1, actor="player", action="move",
            payload={}, seed="seed/1"
        ))
        store.append(Event(
            tick=2, actor="npc", action="talk",
            payload={}, seed="seed/2"
        ))
        store.append(Event(
            tick=3, actor="player", action="move",
            payload={}, seed="seed/3"
        ))

        # 查询移动事件
        move_events = store.get_by_action("move")
        assert len(move_events) == 2
        assert all(e.action == "move" for e in move_events)

        # 查询对话事件
        talk_events = store.get_by_action("talk")
        assert len(talk_events) == 1
        assert talk_events[0].actor == "npc"

    def test_persistence(self):
        """测试文件持久化和加载"""
        store = EventStore()

        # 添加事件
        store.append(Event(
            tick=1, actor="test", action="test_action",
            payload={"data": "test"}, seed="seed/1"
        ))
        store.append(Event(
            tick=2, actor="test2", action="test_action2",
            payload={"data": "test2"}, seed="seed/2"
        ))

        # 保存到临时文件
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.json"
            store.save_to_file(path)

            # 验证文件存在
            assert path.exists()

            # 加载到新的 EventStore
            store2 = EventStore()
            store2.load_from_file(path)

            # 验证数据一致
            assert store2.count() == 2
            assert store2.events[0].actor == "test"
            assert store2.events[0].payload == {"data": "test"}
            assert store2.events[1].actor == "test2"

    def test_persistence_with_nested_directory(self):
        """测试持久化到嵌套目录"""
        store = EventStore()
        store.append(Event(
            tick=1, actor="test", action="test",
            payload={}, seed="seed/1"
        ))

        with tempfile.TemporaryDirectory() as tmpdir:
            # 测试创建嵌套目录
            path = Path(tmpdir) / "subdir" / "nested" / "events.json"
            store.save_to_file(path)

            assert path.exists()
            assert path.parent.exists()

    def test_clear(self):
        """测试清空事件"""
        store = EventStore()

        store.append(Event(
            tick=1, actor="test", action="test",
            payload={}, seed="seed/1"
        ))
        assert store.count() == 1

        store.clear()
        assert store.count() == 0
        assert store.get_events() == []

    def test_get_last_event(self):
        """测试获取最后一个事件"""
        store = EventStore()

        # 空 store
        assert store.get_last_event() is None

        # 添加事件
        store.append(Event(
            tick=1, actor="test", action="test1",
            payload={}, seed="seed/1"
        ))
        assert store.get_last_event().action == "test1"

        store.append(Event(
            tick=2, actor="test", action="test2",
            payload={}, seed="seed/2"
        ))
        assert store.get_last_event().action == "test2"

    def test_get_events_after(self):
        """测试获取指定时间之后的事件"""
        store = EventStore()

        for i in range(1, 6):
            store.append(Event(
                tick=i, actor="test", action="test",
                payload={}, seed=f"seed/{i}"
            ))

        # 获取 tick 3 之后的事件（不包含 3）
        events = store.get_events_after(3)
        assert len(events) == 2
        assert events[0].tick == 4
        assert events[1].tick == 5

    def test_repr(self):
        """测试字符串表示"""
        store = EventStore()

        # 空 store
        assert "empty" in repr(store)

        # 添加事件
        store.append(Event(
            tick=10, actor="test", action="test_action",
            payload={}, seed="seed/10"
        ))

        store_repr = repr(store)
        assert "count=1" in store_repr
        assert "last=10" in store_repr
        assert "test_action" in store_repr

    def test_complex_payload(self):
        """测试复杂的 payload 数据"""
        store = EventStore()

        # 添加包含嵌套数据的事件
        complex_payload = {
            "location": {"x": 10, "y": 20},
            "items": ["sword", "shield"],
            "metadata": {
                "level": 5,
                "tags": ["combat", "equipment"]
            }
        }

        store.append(Event(
            tick=1, actor="player", action="complex_action",
            payload=complex_payload, seed="seed/1"
        ))

        # 保存并加载
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "events.json"
            store.save_to_file(path)

            store2 = EventStore()
            store2.load_from_file(path)

            # 验证复杂数据保持不变
            loaded_event = store2.events[0]
            assert loaded_event.payload == complex_payload
            assert loaded_event.payload["location"]["x"] == 10
            assert "sword" in loaded_event.payload["items"]

    def test_determinism(self):
        """测试确定性（同样的事件序列应该产生同样的结果）"""
        def create_store():
            store = EventStore()
            for i in range(1, 11):
                store.append(Event(
                    tick=i, actor=f"actor_{i % 3}",
                    action=f"action_{i % 2}",
                    payload={"value": i * 10},
                    seed=f"seed/{i}"
                ))
            return store

        store1 = create_store()
        store2 = create_store()

        # 验证事件数量一致
        assert store1.count() == store2.count()

        # 验证每个事件都一致
        for e1, e2 in zip(store1.events, store2.events):
            assert e1.tick == e2.tick
            assert e1.actor == e2.actor
            assert e1.action == e2.action
            assert e1.payload == e2.payload
            assert e1.seed == e2.seed


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
