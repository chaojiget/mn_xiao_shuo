"""
测试 WorldState 与 Simulation 的集成

测试世界状态的快照、恢复、序列化等功能。
"""

import sys
import pytest
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.sim.simulation import Simulation
from src.models.world_state import WorldState, Character, Location, Faction, Resource


class TestWorldStateIntegration:
    """测试 WorldState 集成"""

    def test_simulation_has_world_state(self):
        """测试 Simulation 包含 WorldState"""
        sim = Simulation(seed=42, setting={})

        assert hasattr(sim, 'world_state')
        assert isinstance(sim.world_state, WorldState)
        assert sim.world_state.timestamp == 0
        assert sim.world_state.turn == 0

    def test_world_state_in_snapshot(self):
        """测试快照包含世界状态"""
        sim = Simulation(seed=42, setting={})

        # 添加角色到世界状态
        char = Character(
            id="test_char",
            name="Test Character",
            role="player",
            description="A test character",
            attributes={"strength": 10.0}
        )
        sim.world_state.characters["test_char"] = char

        # 创建快照
        snapshot = sim.snapshot()

        # 验证快照包含世界状态
        assert snapshot.world_state is not None
        assert "characters" in snapshot.world_state
        assert "test_char" in snapshot.world_state["characters"]

    def test_world_state_snapshot_and_restore(self):
        """测试世界状态的快照和恢复"""
        sim = Simulation(seed=42, setting={})

        # 添加角色
        char1 = Character(
            id="hero",
            name="Hero",
            role="protagonist",
            description="The main character",
            attributes={"hp": 100.0, "mp": 50.0}
        )
        sim.world_state.characters["hero"] = char1

        # 创建快照
        snapshot = sim.snapshot()

        # 修改世界状态
        sim.world_state.characters["hero"].attributes["hp"] = 50.0
        sim.world_state.characters["hero"].name = "Modified Hero"

        # 恢复快照
        sim.restore(snapshot)

        # 验证状态恢复
        assert "hero" in sim.world_state.characters
        assert sim.world_state.characters["hero"].attributes["hp"] == 100.0
        assert sim.world_state.characters["hero"].name == "Hero"

    def test_world_state_with_multiple_entities(self):
        """测试包含多种实体的世界状态"""
        sim = Simulation(seed=42, setting={})

        # 添加角色
        char = Character(
            id="char1",
            name="Character 1",
            role="ally",
            description="An ally",
            location="loc1"
        )
        sim.world_state.characters["char1"] = char

        # 添加地点
        loc = Location(
            id="loc1",
            name="Village",
            type="settlement",
            description="A peaceful village"
        )
        sim.world_state.locations["loc1"] = loc

        # 添加势力
        faction = Faction(
            id="fac1",
            name="The Guild",
            type="organization",
            alignment="neutral"
        )
        sim.world_state.factions["fac1"] = faction

        # 添加资源
        resource = Resource(
            type="gold",
            amount=1000.0
        )
        sim.world_state.resources["gold"] = resource

        # 创建快照
        snapshot = sim.snapshot()

        # 清空世界状态
        sim.world_state.characters.clear()
        sim.world_state.locations.clear()
        sim.world_state.factions.clear()
        sim.world_state.resources.clear()

        # 恢复快照
        sim.restore(snapshot)

        # 验证所有实体都被恢复
        assert "char1" in sim.world_state.characters
        assert "loc1" in sim.world_state.locations
        assert "fac1" in sim.world_state.factions
        assert "gold" in sim.world_state.resources


class TestWorldStateReplay:
    """测试 WorldState 与 Replay 的集成"""

    def test_replay_preserves_world_state(self):
        """测试回放保留世界状态"""
        sim = Simulation(seed=42, setting={})

        # 运行一段时间
        sim.run(max_ticks=30)

        # 添加角色
        char = Character(
            id="char1",
            name="Character 1",
            role="player",
            description="Test"
        )
        sim.world_state.characters["char1"] = char

        # 创建快照
        snapshot = sim.snapshot()

        # 继续运行
        sim.run(max_ticks=20)

        # 回放到之前
        sim.replay(to_tick=30)

        # 恢复快照
        sim.restore(snapshot)

        # 验证角色仍然存在
        assert "char1" in sim.world_state.characters


class TestWorldStateSerialization:
    """测试 WorldState 序列化"""

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        # 创建原始世界状态
        ws = WorldState(timestamp=100, turn=10)

        # 添加角色
        char = Character(
            id="char1",
            name="Test Char",
            role="player",
            description="Test",
            attributes={"hp": 100.0},
            resources={"mp": 50.0},
            inventory=["sword", "shield"]
        )
        ws.characters["char1"] = char

        # 添加地点
        loc = Location(
            id="loc1",
            name="Test Location",
            type="city",
            description="A test city",
            properties={"population": 1000}
        )
        ws.locations["loc1"] = loc

        # 序列化
        data = ws.to_dict()

        # 反序列化
        ws2 = WorldState.from_dict(data)

        # 验证
        assert ws2.timestamp == 100
        assert ws2.turn == 10
        assert "char1" in ws2.characters
        assert ws2.characters["char1"].name == "Test Char"
        assert ws2.characters["char1"].attributes["hp"] == 100.0
        assert "loc1" in ws2.locations
        assert ws2.locations["loc1"].properties["population"] == 1000

    def test_complex_world_state_serialization(self):
        """测试复杂世界状态的序列化"""
        ws = WorldState(timestamp=500, turn=50)

        # 添加多个角色
        for i in range(5):
            char = Character(
                id=f"char{i}",
                name=f"Character {i}",
                role="ally" if i % 2 == 0 else "enemy",
                description=f"Character {i} description",
                attributes={"level": float(i * 10)},
                relationships={f"char{j}": float(j - i) for j in range(5) if j != i}
            )
            ws.characters[f"char{i}"] = char

        # 添加多个地点
        for i in range(3):
            loc = Location(
                id=f"loc{i}",
                name=f"Location {i}",
                type="dungeon" if i % 2 == 0 else "town",
                description=f"Location {i} description"
            )
            ws.locations[f"loc{i}"] = loc

        # 序列化
        data = ws.to_dict()

        # 反序列化
        ws2 = WorldState.from_dict(data)

        # 验证
        assert len(ws2.characters) == 5
        assert len(ws2.locations) == 3
        assert ws2.characters["char2"].role == "ally"  # char2: i=2, 2%2==0, ally
        assert ws2.characters["char3"].role == "enemy"  # char3: i=3, 3%2==1, enemy
        assert ws2.locations["loc2"].type == "dungeon"  # loc2: i=2, 2%2==0, dungeon
        assert ws2.locations["loc1"].type == "town"  # loc1: i=1, 1%2==1, town


class TestWorldStatePatches:
    """测试 WorldState 补丁应用"""

    def test_apply_state_patch(self):
        """测试应用状态补丁"""
        ws = WorldState(timestamp=0, turn=0)

        # 添加角色
        char = Character(
            id="char1",
            name="Hero",
            role="protagonist",
            description="The hero",
            attributes={"hp": 100.0, "mp": 50.0}
        )
        ws.characters["char1"] = char

        # 应用补丁
        patch = {
            "characters": {
                "char1": {
                    "attributes": {"hp": 80.0, "mp": 30.0}
                }
            }
        }
        ws.apply_state_patch(patch)

        # 验证补丁应用
        assert ws.characters["char1"].attributes["hp"] == 80.0
        assert ws.characters["char1"].attributes["mp"] == 30.0

    def test_apply_resource_patch(self):
        """测试资源补丁"""
        ws = WorldState(timestamp=0, turn=0)

        # 添加资源
        ws.resources["gold"] = Resource(type="gold", amount=1000.0)

        # 应用补丁（增加金币）
        patch = {
            "resources": {
                "gold": 500.0  # 增加 500
            }
        }
        ws.apply_state_patch(patch)

        # 验证
        assert ws.resources["gold"].amount == 1500.0

    def test_apply_flags_patch(self):
        """测试标志位补丁"""
        ws = WorldState(timestamp=0, turn=0)

        # 初始标志位
        ws.flags = {"quest1_completed": False, "boss_defeated": False}

        # 应用补丁
        patch = {
            "flags": {
                "quest1_completed": True,
                "new_flag": True
            }
        }
        ws.apply_state_patch(patch)

        # 验证
        assert ws.flags["quest1_completed"] is True
        assert ws.flags["new_flag"] is True
        assert ws.flags["boss_defeated"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
