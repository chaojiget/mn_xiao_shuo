"""Phase 2 游戏引擎集成测试

测试所有 Phase 2 功能的集成:
- 核心游戏工具 (7个)
- 任务系统 (5个)
- NPC系统 (4个)
- 存档系统 (SaveService)

使用 Claude Agent SDK + MCP 工具
"""

import pytest
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入模块以正确访问 state_manager
from web.backend.agents import game_tools_mcp

# 导入工具函数
from web.backend.agents.game_tools_mcp import (
    set_session,
    get_player_state,
    add_item,
    update_hp,
    roll_check,
    set_location,
    create_quest,
    get_quests,
    activate_quest,
    update_quest_objective,
    complete_quest,
    create_npc,
    get_npcs,
    update_npc_relationship,
    add_npc_memory,
    save_game,
    ALL_GAME_TOOLS
)

from web.backend.services.save_service import SaveService


class TestGameEngineIntegration:
    """游戏引擎集成测试"""

    @pytest.fixture
    def session_id(self):
        """测试会话ID"""
        return "test_session_integration"

    @pytest.fixture
    def save_service(self):
        """存档服务"""
        db_path = project_root / "data" / "sqlite" / "novel.db"
        return SaveService(str(db_path))

    @pytest.fixture(autouse=True)
    def setup_session(self, session_id):
        """初始化测试会话"""
        # 初始化状态管理器（重要！）
        game_tools_mcp.init_state_manager(None)

        set_session(session_id)

        # 创建初始状态
        initial_state = {
            "player": {
                "name": "测试冒险者",
                "hp": 100,
                "max_hp": 100,
                "level": 1,
                "exp": 0,
                "gold": 50,
                "inventory": []
            },
            "world": {
                "theme": "测试世界",
                "current_location": "起始点"
            },
            "turn_number": 0,
            "quests": [],
            "npcs": [],
            "logs": []
        }

        game_tools_mcp.state_manager.save_state(session_id, initial_state)
        yield
        # 清理（可选）

    @pytest.mark.asyncio
    async def test_01_core_game_tools(self, session_id):
        """测试核心游戏工具"""
        print("\n=== 测试 1: 核心游戏工具 ===")

        # 测试 get_player_state
        state = await get_player_state.handler({})
        assert state["hp"] == 100
        assert state["max_hp"] == 100
        assert state["location"] == "起始点"
        print(f"✓ get_player_state: HP={state['hp']}, 位置={state['location']}")

        # 测试 add_item
        result = await add_item.handler({"item_id": "test_sword", "quantity": 1})
        assert result["success"] is True
        print(f"✓ add_item: {result['message']}")

        # 测试 update_hp
        result = await update_hp.handler({"change": -20, "reason": "测试受伤"})
        assert result["old_hp"] == 100
        assert result["new_hp"] == 80
        print(f"✓ update_hp: {result['old_hp']} → {result['new_hp']}")

        # 测试 roll_check
        result = await roll_check.handler({"skill": "力量", "dc": 15, "modifier": 2})
        assert "roll" in result
        assert 1 <= result["roll"] <= 20
        print(f"✓ roll_check: 骰值={result['roll']}, 总计={result['total']}, 成功={result['success']}")

        # 测试 set_location
        result = await set_location.handler({"location_id": "新位置", "description": "测试描述"})
        assert result["old_location"] == "起始点"
        assert result["new_location"] == "新位置"
        print(f"✓ set_location: {result['old_location']} → {result['new_location']}")

    @pytest.mark.asyncio
    async def test_02_quest_system(self, session_id):
        """测试任务系统"""
        print("\n=== 测试 2: 任务系统 ===")

        # 测试 create_quest
        quest_result = await create_quest.handler({
            "quest_id": "test_quest",
            "quest_type": "main",
            "title": "测试任务",
            "description": "这是一个测试任务",
            "level_requirement": 1,
            "objectives": [
                {
                    "id": "obj_1",
                    "type": "collect",
                    "description": "收集物品",
                    "target": "test_item",
                    "required": 3
                }
            ],
            "rewards": {
                "exp": 100,
                "gold": 50,
                "items": []
            }
        })
        assert quest_result["success"] is True
        print(f"✓ create_quest: {quest_result['message']}")

        # 测试 get_quests
        quests = await get_quests.handler({"status": "available"})
        assert quests["count"] >= 1
        print(f"✓ get_quests: 找到 {quests['count']} 个可接取任务")

        # 测试 activate_quest
        activate_result = await activate_quest.handler({"quest_id": "test_quest"})
        assert activate_result["success"] is True
        print(f"✓ activate_quest: {activate_result['message']}")

        # 测试 update_quest_objective
        progress_result = await update_quest_objective.handler({
            "quest_id": "test_quest",
            "objective_id": "obj_1",
            "amount": 2
        })
        assert progress_result["objective"]["current"] == 2
        print(f"✓ update_quest_objective: 进度 {progress_result['objective']['current']}/3")

        # 完成目标
        await update_quest_objective.handler({
            "quest_id": "test_quest",
            "objective_id": "obj_1",
            "amount": 1
        })

        # 测试 complete_quest
        complete_result = await complete_quest.handler({"quest_id": "test_quest"})
        assert complete_result["success"] is True
        assert complete_result["rewards"]["exp"] == 100
        print(f"✓ complete_quest: 获得 {complete_result['rewards']['exp']} 经验值")

    @pytest.mark.asyncio
    async def test_03_npc_system(self, session_id):
        """测试NPC系统"""
        print("\n=== 测试 3: NPC系统 ===")

        # 测试 create_npc
        npc_result = await create_npc.handler({
            "npc_id": "test_npc",
            "name": "测试NPC",
            "role": "测试角色",
            "description": "这是一个测试NPC",
            "location": "测试位置",
            "personality_traits": ["友善", "乐于助人"],
            "speech_style": "说话温和",
            "goals": ["帮助冒险者"]
        })
        assert npc_result["success"] is True
        print(f"✓ create_npc: {npc_result['message']}")

        # 测试 get_npcs
        npcs_result = await get_npcs.handler({"location": "测试位置"})
        assert npcs_result["count"] >= 1
        print(f"✓ get_npcs: 在测试位置找到 {npcs_result['count']} 个NPC")

        # 测试 update_npc_relationship
        rel_result = await update_npc_relationship.handler({
            "npc_id": "test_npc",
            "affinity_delta": 15,
            "trust_delta": 10,
            "reason": "测试关系更新"
        })
        assert rel_result["affinity"] == 15
        assert rel_result["trust"] == 10
        print(f"✓ update_npc_relationship: 好感度={rel_result['affinity']}, 信任度={rel_result['trust']}")

        # 测试 add_npc_memory
        memory_result = await add_npc_memory.handler({
            "npc_id": "test_npc",
            "event_type": "conversation",
            "summary": "测试对话记忆",
            "emotional_impact": 5
        })
        assert memory_result["success"] is True
        print(f"✓ add_npc_memory: {memory_result['message']}")

    @pytest.mark.asyncio
    async def test_04_save_system(self, session_id, save_service):
        """测试存档系统"""
        print("\n=== 测试 4: 存档系统 ===")

        # 测试 save_game (通过MCP工具)
        save_result = await save_game.handler({
            "slot_id": 9,
            "save_name": "集成测试存档"
        })
        assert save_result["success"] is True
        assert save_result["slot_id"] == 9
        print(f"✓ save_game (MCP): {save_result['message']}")

        # 测试 SaveService（仅当有数据库连接时）
        if game_tools_mcp.state_manager.db:
            saves = save_service.get_saves("default_user")
            test_save = next((s for s in saves if s["slot_id"] == 9), None)
            assert test_save is not None
            assert test_save["save_name"] == "集成测试存档"
            print(f"✓ SaveService.get_saves: 找到测试存档")

            # 测试加载存档
            save_data = save_service.load_game(save_result["save_id"])
            assert save_data is not None
            assert "game_state" in save_data
            print(f"✓ SaveService.load_game: 成功加载存档")

            # 清理测试存档
            save_service.delete_save(save_result["save_id"])
            print(f"✓ 测试存档已清理")
        else:
            print(f"⊘ SaveService 测试跳过（无数据库连接）")

    @pytest.mark.asyncio
    async def test_05_integrated_workflow(self, session_id):
        """测试完整的集成流程"""
        print("\n=== 测试 5: 完整集成流程 ===")

        # 1. 创建NPC
        await create_npc.handler({
            "npc_id": "workflow_npc",
            "name": "任务发布者",
            "role": "任务NPC",
            "description": "发布任务的NPC",
            "location": "村庄",
            "personality_traits": ["严肃"],
            "speech_style": "简洁明了",
            "goals": ["发布任务"]
        })
        print("✓ Step 1: 创建NPC")

        # 2. NPC发布任务
        await create_quest.handler({
            "quest_id": "workflow_quest",
            "quest_type": "side",
            "title": "工作流测试任务",
            "description": "测试完整工作流",
            "level_requirement": 1,
            "objectives": [
                {
                    "id": "obj_workflow",
                    "type": "collect",
                    "description": "收集测试物品",
                    "target": "test_item",
                    "required": 1
                }
            ],
            "rewards": {"exp": 50, "gold": 25, "items": []}
        })
        print("✓ Step 2: 创建任务")

        # 3. 接受任务
        await activate_quest.handler({"quest_id": "workflow_quest"})
        print("✓ Step 3: 激活任务")

        # 4. 完成任务目标
        await add_item.handler({"item_id": "test_item", "quantity": 1})
        await update_quest_objective.handler({
            "quest_id": "workflow_quest",
            "objective_id": "obj_workflow",
            "amount": 1
        })
        print("✓ Step 4: 完成任务目标")

        # 5. 完成任务
        result = await complete_quest.handler({"quest_id": "workflow_quest"})
        assert result["success"] is True
        print("✓ Step 5: 完成任务并获得奖励")

        # 6. 更新NPC关系
        await update_npc_relationship.handler({
            "npc_id": "workflow_npc",
            "affinity_delta": 20,
            "trust_delta": 15,
            "reason": "完成了任务"
        })
        print("✓ Step 6: 更新NPC关系")

        # 7. 添加NPC记忆
        await add_npc_memory.handler({
            "npc_id": "workflow_npc",
            "event_type": "quest",
            "summary": "冒险者完成了工作流测试任务",
            "emotional_impact": 8
        })
        print("✓ Step 7: 添加NPC记忆")

        # 8. 保存游戏
        await save_game.handler({
            "slot_id": 10,
            "save_name": "集成测试 - 工作流完成"
        })
        print("✓ Step 8: 保存游戏")

        print("\n✅ 完整集成流程测试通过！")


def test_all_tools_registered():
    """测试所有工具都已注册"""
    assert len(ALL_GAME_TOOLS) == 15, f"期望15个工具，实际{len(ALL_GAME_TOOLS)}个"

    tool_names = [tool.name for tool in ALL_GAME_TOOLS]

    # 核心工具 (7个)
    assert "get_player_state" in tool_names
    assert "add_item" in tool_names
    assert "update_hp" in tool_names
    assert "roll_check" in tool_names
    assert "set_location" in tool_names
    assert "create_quest" in tool_names
    assert "save_game" in tool_names

    # 任务工具 (4个，因为create_quest已在核心工具中)
    assert "get_quests" in tool_names
    assert "activate_quest" in tool_names
    assert "update_quest_objective" in tool_names
    assert "complete_quest" in tool_names

    # NPC工具 (4个)
    assert "create_npc" in tool_names
    assert "get_npcs" in tool_names
    assert "update_npc_relationship" in tool_names
    assert "add_npc_memory" in tool_names

    print(f"\n✅ 所有15个工具已正确注册：{', '.join(tool_names)}")


if __name__ == "__main__":
    """手动运行测试"""
    import asyncio

    print("\n" + "="*60)
    print("  Phase 2 游戏引擎集成测试")
    print("  使用 Claude Agent SDK + MCP 工具")
    print("="*60)

    # 初始化状态管理器
    game_tools_mcp.init_state_manager(None)

    # 运行同步测试
    test_all_tools_registered()

    # 运行异步测试
    async def run_tests():
        test = TestGameEngineIntegration()
        session_id = "test_session_manual"

        # Setup
        set_session(session_id)

        # 创建初始状态
        initial_state = {
            "player": {
                "name": "测试冒险者",
                "hp": 100,
                "max_hp": 100,
                "level": 1,
                "exp": 0,
                "gold": 50,
                "inventory": []
            },
            "world": {
                "theme": "测试世界",
                "current_location": "起始点"
            },
            "turn_number": 0,
            "quests": [],
            "npcs": [],
            "logs": []
        }
        game_tools_mcp.state_manager.save_state(session_id, initial_state)

        # Run tests
        await test.test_01_core_game_tools(session_id)
        await test.test_02_quest_system(session_id)
        await test.test_03_npc_system(session_id)

        db_path = project_root / "data" / "sqlite" / "novel.db"
        save_service = SaveService(str(db_path))
        await test.test_04_save_system(session_id, save_service)

        await test.test_05_integrated_workflow(session_id)

    asyncio.run(run_tests())

    print("\n" + "="*60)
    print("  ✅ 所有集成测试通过！")
    print("="*60 + "\n")
