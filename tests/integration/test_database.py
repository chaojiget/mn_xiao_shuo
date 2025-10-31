#!/usr/bin/env python3
"""
测试数据库功能
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.utils.database import Database
from src.models import WorldState, Character, EventNode, EventArc, Clue, Evidence, Setup
from src.models.event_node import EventStatus
from src.models.clue import ClueStatus, SetupStatus


def test_basic_operations():
    """测试基础操作"""
    print("=" * 60)
    print("测试 1: 基础数据库操作")
    print("=" * 60)

    with Database() as db:
        # 创建小说
        novel_id = "test_novel_001"
        db.create_novel(
            novel_id=novel_id,
            title="测试小说",
            novel_type="scifi",
            setting_json={"test": "setting"},
            preference="hybrid"
        )
        print("✅ 创建小说成功")

        # 获取小说
        novel = db.get_novel(novel_id)
        assert novel is not None
        assert novel["title"] == "测试小说"
        print("✅ 获取小说成功")

        return novel_id


def test_world_state(novel_id: str):
    """测试世界状态保存/加载"""
    print("\n" + "=" * 60)
    print("测试 2: 世界状态保存/加载")
    print("=" * 60)

    with Database() as db:
        # 创建世界状态
        world_state = WorldState(timestamp=0, turn=1)

        # 添加角色
        protagonist = Character(
            id="CHAR-001",
            name="测试主角",
            role="protagonist",
            attributes={"智力": 9, "魅力": 7},
            resources={"金币": 1000, "声望": 50}
        )
        world_state.characters["CHAR-001"] = protagonist

        # 保存
        db.save_world_state(novel_id, world_state)
        print("✅ 保存世界状态成功")

        # 加载
        loaded_state_dict = db.load_world_state(novel_id)
        assert loaded_state_dict is not None
        assert loaded_state_dict["turn"] == 1
        assert "CHAR-001" in loaded_state_dict["characters"]
        print("✅ 加载世界状态成功")

        # 打印状态
        print(f"\n角色数: {len(loaded_state_dict['characters'])}")
        print(f"回合: {loaded_state_dict['turn']}")


def test_events(novel_id: str):
    """测试事件系统"""
    print("\n" + "=" * 60)
    print("测试 3: 事件节点保存/查询")
    print("=" * 60)

    with Database() as db:
        # 创建事件
        event = EventNode(
            id="ARC-1:E001",
            arc_id="ARC-1",
            title="测试事件",
            goal="完成测试目标",
            tension_delta=0.3,
            puzzle_density=0.5,
            arc_progress=0.2
        )

        # 保存
        db.save_event_node(novel_id, event)
        print("✅ 保存事件节点成功")

        # 查询
        events = db.get_events_by_arc(novel_id, "ARC-1")
        assert len(events) == 1
        assert events[0]["title"] == "测试事件"
        print("✅ 查询事件节点成功")

        # 更新状态
        db.update_event_status("ARC-1:E001", EventStatus.COMPLETED.value, attempts=1)
        print("✅ 更新事件状态成功")


def test_chapters(novel_id: str):
    """测试章节保存"""
    print("\n" + "=" * 60)
    print("测试 4: 章节保存/查询")
    print("=" * 60)

    with Database() as db:
        # 保存章节
        db.save_chapter(
            novel_id=novel_id,
            chapter_num=1,
            title="第一章: 开端",
            content="这是第一章的内容...(测试数据)\n" * 50,
            event_ids=["ARC-1:E001"]
        )
        print("✅ 保存章节成功")

        # 获取章节
        chapter = db.get_chapter(novel_id, 1)
        assert chapter is not None
        assert chapter["title"] == "第一章: 开端"
        print("✅ 获取章节成功")

        print(f"\n章节字数: {chapter['word_count']}")


def test_clues_and_setups(novel_id: str):
    """测试线索和伏笔"""
    print("\n" + "=" * 60)
    print("测试 5: 线索和伏笔管理")
    print("=" * 60)

    with Database() as db:
        # 保存线索
        clue = Clue(
            id="CLUE-001",
            content="发现异常数据",
            type="data_anomaly",
            evidence_ids=["EVIDENCE-001"],
            status=ClueStatus.DISCOVERED
        )
        db.save_clue(novel_id, clue)
        print("✅ 保存线索成功")

        # 保存伏笔
        setup = Setup(
            id="SETUP-001",
            description="主角获得神秘物品",
            setup_event_id="ARC-1:E001",
            sla_deadline=10,
            setup_turn=1,
            status=SetupStatus.PENDING
        )
        db.save_setup(novel_id, setup)
        print("✅ 保存伏笔成功")

        # 查询逾期伏笔 (当前回合15,SLA是10,应该逾期)
        overdue = db.get_overdue_setups(novel_id, current_turn=15)
        assert len(overdue) == 1
        print("✅ 查询逾期伏笔成功")


def test_execution_log(novel_id: str):
    """测试执行日志"""
    print("\n" + "=" * 60)
    print("测试 6: 执行日志")
    print("=" * 60)

    with Database() as db:
        db.log_execution(
            novel_id=novel_id,
            event_id="ARC-1:E001",
            turn=1,
            action_queue={"steps": []},
            result={"content": "测试内容"},
            success=True,
            model_used="claude-sonnet",
            tokens_used=500,
            duration_ms=1200
        )
        print("✅ 记录执行日志成功")


def test_stats(novel_id: str):
    """测试统计信息"""
    print("\n" + "=" * 60)
    print("测试 7: 统计信息")
    print("=" * 60)

    with Database() as db:
        stats = db.get_stats(novel_id)
        print("✅ 获取统计信息成功\n")

        print("统计数据:")
        print(f"  - 章节数: {stats['chapters']}")
        print(f"  - 事件数: {stats['events']}")
        print(f"  - 完成事件: {stats['completed_events']}")
        print(f"  - 线索数: {stats['clues']}")
        print(f"  - 逾期伏笔: {stats['overdue_setups']}")


def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print(" SQLite 数据库功能测试")
    print("=" * 60)

    try:
        # 测试基础操作
        novel_id = test_basic_operations()

        # 测试世界状态
        test_world_state(novel_id)

        # 测试事件
        test_events(novel_id)

        # 测试章节
        test_chapters(novel_id)

        # 测试线索和伏笔
        test_clues_and_setups(novel_id)

        # 测试执行日志
        test_execution_log(novel_id)

        # 测试统计
        test_stats(novel_id)

        # 总结
        print("\n" + "=" * 60)
        print("🎉 所有数据库测试通过!")
        print("=" * 60)

        print("\n数据库已准备就绪,可以开始开发了!")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
