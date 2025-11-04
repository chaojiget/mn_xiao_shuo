"""Global Director 使用示例

演示如何使用全局导演系统进行事件调度、一致性审计和线索经济管理
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.director import (
    GlobalDirector,
    DirectorConfig,
    DirectorMode,
    ClueEconomyManager
)
from src.models.world_state import WorldState, Character, Resource, Location
from src.models.event_node import EventNode, EventArc
from src.models.clue import Setup, Clue, Evidence


def create_demo_world() -> WorldState:
    """创建演示用的世界状态"""
    # 创建主角
    protagonist = Character(
        id="PROTAGONIST",
        name="张三",
        role="protagonist",
        description="修真界新人",
        attributes={
            "cultivation_level": 0,  # 炼气期
            "strength": 10,
            "intelligence": 15
        },
        resources={
            "灵石": 100.0,
            "HP": 100.0
        },
        location="新手村"
    )

    # 创建地点
    location = Location(
        id="新手村",
        name="新手村",
        type="村庄",
        description="修真界的新手村"
    )

    # 创建世界状态
    world = WorldState(
        timestamp=0,
        turn=0,
        characters={"PROTAGONIST": protagonist},
        locations={"新手村": location},
        resources={
            "灵石": Resource(type="灵石", amount=100.0)
        }
    )

    return world


def create_demo_events() -> list[EventNode]:
    """创建演示用的事件"""
    events = []

    # 事件1：遇到神秘老者
    event1 = EventNode(
        id="event_001",
        arc_id="main_arc",
        title="遇到神秘老者",
        goal="获得修炼指导",
        # 可玩性指标（提高到合理范围）
        puzzle_density=0.6,
        skill_checks_variety=0.7,
        failure_grace=0.8,
        hint_latency=0.5,
        exploit_resistance=0.6,
        reward_loop=0.7,
        # 叙事指标（提高到合理范围）
        arc_progress=0.6,
        theme_echo=0.8,
        conflict_gradient=0.5,
        payoff_debt=0.0,
        scene_specificity=0.8,
        pacing_smoothness=0.7,
        # 玄幻指标（提高到合理范围）
        upgrade_frequency=0.3,
        resource_gain=0.6,
        combat_variety=0.4,
        reversal_satisfaction=0.0,
        faction_expansion=0.0,
        # 效果
        effects={
            "flags": {"met_elder": True}
        },
        rewards={
            "灵石": 50.0
        },
        # 线索
        setups=["setup_001"],  # 埋下伏笔
        description="在新手村遇到神秘老者，获得修炼指导"
    )
    events.append(event1)

    # 事件2：修炼突破
    event2 = EventNode(
        id="event_002",
        arc_id="main_arc",
        title="修炼突破",
        goal="突破到下一境界",
        prerequisites=["event_001"],
        required_flags={"met_elder": True},
        required_resources={"灵石": 100.0},
        # 可玩性指标（高可玩性事件）
        puzzle_density=0.7,
        skill_checks_variety=0.8,
        failure_grace=0.6,
        hint_latency=0.7,
        exploit_resistance=0.7,
        reward_loop=0.9,
        # 叙事指标（高叙事价值）
        arc_progress=0.8,
        theme_echo=0.9,
        conflict_gradient=0.7,
        payoff_debt=0.8,  # 偿还伏笔
        scene_specificity=0.9,
        pacing_smoothness=0.8,
        # 玄幻指标（升级事件）
        upgrade_frequency=1.0,
        resource_gain=0.4,
        combat_variety=0.5,
        reversal_satisfaction=0.9,
        faction_expansion=0.2,
        # 效果
        effects={
            "characters": {
                "PROTAGONIST": {
                    "attributes": {"cultivation_level": 1}
                }
            }
        },
        payoffs=["setup_001"],  # 偿还伏笔
        description="在老者指导下突破境界"
    )
    events.append(event2)

    # 事件3：接受任务
    event3 = EventNode(
        id="event_003",
        arc_id="side_arc",
        title="清理魔物",
        goal="清理村外的魔物",
        prerequisites=["event_001"],
        # 可玩性指标（战斗向事件）
        puzzle_density=0.5,
        skill_checks_variety=0.9,
        failure_grace=0.7,
        hint_latency=0.6,
        exploit_resistance=0.8,
        reward_loop=0.8,
        # 叙事指标
        arc_progress=0.5,
        theme_echo=0.6,
        conflict_gradient=0.9,
        payoff_debt=0.0,
        scene_specificity=0.7,
        pacing_smoothness=0.6,
        # 玄幻指标（战斗+资源获取）
        upgrade_frequency=0.4,
        resource_gain=0.8,
        combat_variety=0.9,
        reversal_satisfaction=0.5,
        faction_expansion=0.0,
        # 效果
        rewards={
            "灵石": 80.0,
            "经验": 100.0
        },
        description="帮助村民清理魔物"
    )
    events.append(event3)

    return events


def demo_basic_usage():
    """演示基本用法"""
    print("=" * 60)
    print("Global Director 基本用法演示")
    print("=" * 60)

    # 1. 创建世界状态
    world = create_demo_world()
    print(f"\n创建世界状态: Turn {world.turn}")
    print(f"主角: {world.get_protagonist().name}")
    print(f"位置: {world.get_protagonist().location}")

    # 2. 创建导演配置
    config = DirectorConfig(
        mode=DirectorMode.BALANCED,
        genre="xianxia",
        enable_consistency_audit=True,
        enable_clue_economy=True
    )

    # 3. 创建设定
    setting = {
        "类型": "玄幻",
        "境界划分": ["炼气期", "筑基期", "金丹期"],
        "主题": "修仙成长"
    }

    # 4. 初始化导演
    director = GlobalDirector(config, setting)
    print(f"\n初始化导演: 模式={config.mode.value}, 类型={config.genre}")

    # 5. 创建事件
    events = create_demo_events()
    print(f"\n创建 {len(events)} 个事件")

    # 6. 选择第一个事件
    print("\n" + "-" * 60)
    print("第一回合：选择事件")
    print("-" * 60)

    decision = director.select_next_event(world, events)

    if decision.selected_event:
        print(f"\n选中事件: {decision.selected_event.title}")
        print(f"总分: {decision.score.total_score:.1f}/100")
        print(f"\n评分详情:")
        print(f"  - 可玩性: {decision.score.playability_score:.1f}/100")
        print(f"  - 叙事性: {decision.score.narrative_score:.1f}/100")
        print(f"  - 类型分: {decision.score.genre_score:.1f}/100")
        print(f"\n决策说明:\n{decision.reasoning}")

        if decision.warnings:
            print(f"\n警告:")
            for warning in decision.warnings:
                print(f"  - {warning}")

        if decision.suggestions:
            print(f"\n建议:")
            for suggestion in decision.suggestions[:3]:
                print(f"  - {suggestion}")

        # 7. 执行事件
        print("\n执行事件...")
        director.execute_event(decision.selected_event, world)

        # 8. 完成事件
        print("完成事件...")
        director.complete_event(decision.selected_event, world, success=True)

    else:
        print("\n未选中任何事件")
        print(f"原因: {decision.reasoning}")

    # 9. 查看状态
    print("\n" + "-" * 60)
    print("导演状态")
    print("-" * 60)
    status = director.get_status()
    print(f"当前回合: {status['current_turn']}")
    print(f"已完成事件: {status['completed_events']}")
    print(f"活跃事件: {status['active_events']}")


def demo_clue_economy():
    """演示线索经济管理"""
    print("\n\n" + "=" * 60)
    print("线索经济管理演示")
    print("=" * 60)

    # 创建线索经济管理器
    manager = ClueEconomyManager()

    # 1. 创建伏笔
    print("\n创建伏笔:")
    setup1 = manager.create_setup(
        description="老者提到的秘密宝藏",
        setup_event_id="event_001",
        sla_deadline=10,
        priority=0.8
    )
    print(f"  - {setup1.description} (SLA: {setup1.sla_deadline} 回合)")

    setup2 = manager.create_setup(
        description="村外魔物的来源",
        setup_event_id="event_003",
        sla_deadline=15,
        priority=0.6
    )
    print(f"  - {setup2.description} (SLA: {setup2.sla_deadline} 回合)")

    # 2. 注册线索
    print("\n注册线索:")
    clue1 = manager.register_clue(
        content="老者留下的地图碎片",
        clue_type="物证",
        related_event="event_001"
    )
    print(f"  - {clue1.content}")

    # 3. 推进回合
    print("\n推进回合...")
    for i in range(1, 12):
        manager.advance_turn()
        if i % 5 == 0:
            print(f"  Turn {manager.current_turn}")

    # 4. 检查健康度
    print("\n线索经济健康度:")
    metrics = manager.get_health_metrics()
    print(f"  总体健康度: {metrics.overall_health:.1f}/100")
    print(f"  伏笔总数: {metrics.total_setups}")
    print(f"  已偿还: {metrics.paid_setups}")
    print(f"  逾期: {metrics.overdue_setups}")
    print(f"  偿还率: {metrics.payoff_rate * 100:.1f}%")

    # 5. 获取建议
    print("\n改进建议:")
    suggestions = manager.get_suggestions()
    for suggestion in suggestions:
        print(f"  {suggestion}")

    # 6. 偿还伏笔
    print(f"\n偿还伏笔: {setup1.description}")
    manager.pay_off_setup(setup1.id, "event_002")

    # 7. 重新检查健康度
    print("\n偿还后的健康度:")
    metrics = manager.get_health_metrics()
    print(f"  总体健康度: {metrics.overall_health:.1f}/100")
    print(f"  已偿还: {metrics.paid_setups}/{metrics.total_setups}")


def demo_consistency_audit():
    """演示一致性审计"""
    print("\n\n" + "=" * 60)
    print("一致性审计演示")
    print("=" * 60)

    from src.director import ConsistencyAuditor

    # 创建设定
    setting = {
        "类型": "玄幻",
        "境界划分": ["炼气期", "筑基期", "金丹期"]
    }

    # 创建审计器
    auditor = ConsistencyAuditor(setting)

    # 创建有问题的世界状态
    world = create_demo_world()

    # 1. 正常状态
    print("\n检查正常状态:")
    report = auditor.audit_world_state(world)
    print(f"  结果: {report.summary}")
    print(f"  通过: {report.passed}")

    # 2. 引入违规：资源为负
    print("\n引入资源违规:")
    world.resources["灵石"].amount = -50.0
    report = auditor.audit_world_state(world)
    print(f"  结果: {report.summary}")
    print(f"  通过: {report.passed}")
    print(f"  违规数: {len(report.violations)}")

    if report.violations:
        print("\n  违规详情:")
        for v in report.violations:
            print(f"    - [{v.severity.value}] {v.description}")
            if v.suggested_fix:
                print(f"      建议: {v.suggested_fix}")

    # 3. 修复违规
    print("\n修复违规:")
    world.resources["灵石"].amount = 100.0
    report = auditor.audit_world_state(world)
    print(f"  结果: {report.summary}")
    print(f"  通过: {report.passed}")


def main():
    """主函数"""
    # 运行所有演示
    demo_basic_usage()
    demo_clue_economy()
    demo_consistency_audit()

    print("\n\n" + "=" * 60)
    print("演示完成")
    print("=" * 60)


if __name__ == "__main__":
    main()
