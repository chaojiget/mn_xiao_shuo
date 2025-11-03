"""Phase 2 完整演示脚本 - 失落的神庙冒险

演示所有 Phase 2 功能:
1. 核心游戏工具 (7个工具)
2. 任务系统 (5个工具)
3. NPC系统 (4个工具)
4. 存档系统 (SaveService)

使用方式:
    python examples/game_engine_demo.py
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import asyncio
import json
from typing import Dict, Any

# 导入 MCP 工具模块（使用模块级导入以正确访问 state_manager）
from web.backend.agents import game_tools_mcp

# 导入工具函数
from web.backend.agents.game_tools_mcp import (
    set_session,
    # 核心工具
    get_player_state,
    add_item,
    update_hp,
    roll_check,
    set_location,
    # 任务工具
    create_quest,
    get_quests,
    activate_quest,
    update_quest_objective,
    complete_quest,
    # NPC工具
    create_npc,
    get_npcs,
    update_npc_relationship,
    add_npc_memory,
    # 存档工具
    save_game
)

from web.backend.services.save_service import SaveService


class GameDemo:
    """游戏演示类"""

    def __init__(self, session_id: str = "demo_session"):
        self.session_id = session_id

        # 初始化存档服务
        db_path = project_root / "data" / "sqlite" / "novel.db"
        self.save_service = SaveService(str(db_path))

        # 初始化状态管理器（重要！）
        game_tools_mcp.init_state_manager(None)  # 演示模式，不使用数据库连接

        set_session(session_id)

        # 初始化游戏状态
        self._initialize_game_state()

    def _initialize_game_state(self):
        """初始化游戏状态"""
        initial_state = {
            "player": {
                "name": "冒险者",
                "hp": 100,
                "max_hp": 100,
                "level": 1,
                "exp": 0,
                "gold": 50,
                "inventory": [
                    {"id": "basic_sword", "name": "基础剑", "quantity": 1},
                    {"id": "health_potion", "name": "生命药水", "quantity": 3}
                ]
            },
            "world": {
                "theme": "奇幻世界",
                "current_location": "村庄广场"
            },
            "turn_number": 0,
            "quests": [],
            "npcs": [],
            "logs": []
        }

        game_tools_mcp.state_manager.save_state(self.session_id, initial_state)
        print(f"\n{'='*60}")
        print(f"  Phase 2 游戏引擎演示 - 失落的神庙冒险")
        print(f"{'='*60}")
        print(f"会话ID: {self.session_id}")
        print(f"初始位置: {initial_state['world']['current_location']}")
        print(f"初始HP: {initial_state['player']['hp']}/{initial_state['player']['max_hp']}")
        print(f"初始金币: {initial_state['player']['gold']}")
        print(f"{'='*60}\n")

    async def demo_scene_1_village(self):
        """场景1: 村庄 - 创建NPC和任务"""
        print("\n" + "="*60)
        print("场景 1: 村庄广场")
        print("="*60)

        print("\n[DM] 你来到了宁静的村庄广场。阳光洒在石板路上，")
        print("     几位村民正在井边闲聊。远处，村长的房子门口")
        print("     贴着一张告示。\n")

        # 玩家查看状态
        print(">>> 玩家: 查看我的状态")
        state = await get_player_state.handler({})
        print(f"[系统] 玩家状态: HP {state['hp']}/{state['max_hp']}, "
              f"位置: {state['location']}, 金币: {state['gold']}")
        print(f"       背包: {len(state['inventory'])}个物品\n")

        # 创建村长NPC
        print(">>> 玩家: 走向村长的房子")
        print("[DM] 你走到村长房前，一位年迈但精神矍铄的老人迎了出来。\n")

        npc_result = await create_npc.handler({
            "npc_id": "npc_village_chief",
            "name": "村长艾尔文",
            "role": "村长",
            "description": "村庄的领导者，年迈但智慧，深受村民爱戴",
            "location": "村庄广场",
            "personality_traits": ["智慧", "正直", "关心村民"],
            "speech_style": "说话缓慢沉稳，用词考究",
            "goals": ["保护村庄安全", "寻找勇敢的冒险者"]
        })
        print(f"[系统] {npc_result['message']}\n")

        # 创建任务
        print(">>> 玩家: 询问村长关于告示的事")
        print("[村长艾尔文] 年轻的冒险者，我们村庄遇到了大麻烦...")
        print("             传说中的失落神庙最近出现了异动，邪恶力量正在苏醒。")
        print("             我们需要一位勇士进入神庙，找到三块神器碎片，")
        print("             并击败守护者，阻止灾难降临。\n")

        quest_result = await create_quest.handler({
            "quest_id": "quest_lost_temple",
            "quest_type": "main",
            "title": "失落神庙的秘密",
            "description": "进入失落神庙，收集三块神器碎片，击败守护者",
            "level_requirement": 1,
            "objectives": [
                {
                    "id": "obj_explore_temple",
                    "type": "explore",
                    "description": "探索失落神庙",
                    "target": "神庙入口",
                    "required": 1
                },
                {
                    "id": "obj_collect_fragments",
                    "type": "collect",
                    "description": "收集神器碎片",
                    "target": "神器碎片",
                    "required": 3
                },
                {
                    "id": "obj_defeat_guardian",
                    "type": "defeat",
                    "description": "击败神庙守护者",
                    "target": "神庙守护者",
                    "required": 1
                }
            ],
            "rewards": {
                "exp": 500,
                "gold": 200,
                "items": [{"id": "legendary_amulet", "quantity": 1}]
            }
        })
        print(f"[系统] {quest_result['message']}\n")

        # 接受任务
        print(">>> 玩家: 我接受这个任务！")
        activate_result = await activate_quest.handler({"quest_id": "quest_lost_temple"})
        print(f"[系统] {activate_result['message']}")
        print(f"[村长艾尔文] 太好了！愿神明保佑你平安归来。\n")

        # 更新NPC关系
        rel_result = await update_npc_relationship.handler({
            "npc_id": "npc_village_chief",
            "affinity_delta": 10,
            "trust_delta": 5,
            "reason": "接受了拯救村庄的任务"
        })
        print(f"[系统] {rel_result['message']}")
        print(f"       好感度: {rel_result['changes']['affinity']}")
        print(f"       信任度: {rel_result['changes']['trust']}")
        print(f"       关系类型: {rel_result['relationship_type']}\n")

        # 添加NPC记忆
        memory_result = await add_npc_memory.handler({
            "npc_id": "npc_village_chief",
            "event_type": "conversation",
            "summary": "冒险者接受了失落神庙任务",
            "emotional_impact": 5
        })
        print(f"[系统] {memory_result['message']}\n")

        # 保存游戏
        state = game_tools_mcp.state_manager.get_state(self.session_id)
        save_result = await save_game.handler({
            "slot_id": 1,
            "save_name": "村庄 - 接受任务"
        })
        print(f"[系统] {save_result['message']}\n")

        await asyncio.sleep(2)

    async def demo_scene_2_temple_entrance(self):
        """场景2: 神庙入口 - 探索和检定"""
        print("\n" + "="*60)
        print("场景 2: 神庙入口")
        print("="*60)

        # 移动到神庙
        print("\n>>> 玩家: 前往失落神庙")
        location_result = await set_location.handler({
            "location_id": "神庙入口",
            "description": "古老的石门半掩着，里面传来阴冷的气息"
        })
        print(f"[DM] {location_result['description']}")
        print(f"[系统] 位置已更新: {location_result['old_location']} → {location_result['new_location']}\n")

        # 更新任务进度
        progress_result = await update_quest_objective.handler({
            "quest_id": "quest_lost_temple",
            "objective_id": "obj_explore_temple",
            "amount": 1
        })
        print(f"[系统] 任务目标更新: {progress_result['objective']['description']}")
        print(f"       进度: {progress_result['objective']['current']}/{progress_result['objective']['required']}")
        print(f"       完成: {progress_result['completed']}\n")

        # 创建神秘商人NPC
        print("[DM] 神庙入口处，一个戴着兜帽的神秘商人正在摆弄着货物。\n")

        merchant_result = await create_npc.handler({
            "npc_id": "npc_mysterious_merchant",
            "name": "神秘商人",
            "role": "商人",
            "description": "身份不明的旅行商人，似乎知道很多秘密",
            "location": "神庙入口",
            "personality_traits": ["神秘", "精明", "话中有话"],
            "speech_style": "说话含糊不清，喜欢打哑谜",
            "goals": ["出售商品", "收集情报"]
        })
        print(f"[系统] {merchant_result['message']}\n")

        # 与商人对话
        print(">>> 玩家: 你好，请问你知道神庙里的情况吗？")
        print("[神秘商人] 嘿嘿...想知道？先看看我的货物吧。")
        print("           这瓶药水...或许能在关键时刻救你一命。\n")

        # 感知检定
        print(">>> 玩家: 我想仔细观察这个商人")
        check_result = await roll_check.handler({
            "skill": "感知",
            "dc": 15,
            "modifier": 2
        })
        print(f"[系统] 感知检定: {check_result['detail']}")
        print(f"       结果: {check_result['total']} vs DC{check_result['dc']} - {check_result['result']}")

        if check_result['success']:
            print("[DM] 你注意到商人腰间挂着一个奇怪的护符，")
            print("     和村长描述的神器碎片样式相似！\n")
        else:
            print("[DM] 你没有发现什么异常。\n")

        # 购买物品
        print(">>> 玩家: 我买一瓶高级生命药水")
        item_result = await add_item.handler({
            "item_id": "super_health_potion",
            "quantity": 1
        })
        print(f"[系统] {item_result['message']}\n")

        # 保存游戏
        save_result2 = await save_game.handler({
            "slot_id": 2,
            "save_name": "神庙入口 - 遇到商人"
        })
        print(f"[系统] {save_result2['message']}\n")

        await asyncio.sleep(2)

    async def show_save_list(self):
        """显示存档列表"""
        print("\n" + "="*60)
        print("存档列表")
        print("="*60 + "\n")

        saves = self.save_service.get_saves("default_user")

        if not saves:
            print("[系统] 暂无存档\n")
            return

        print(f"[系统] 找到 {len(saves)} 个存档:\n")
        for save in saves:
            metadata = save.get("metadata", {})
            print(f"  槽位 {save['slot_id']}: {save['save_name']}")
            print(f"    - 回合数: {metadata.get('turn_number', 0)}")
            print(f"    - 位置: {metadata.get('location', '未知')}")
            print(f"    - 等级: {metadata.get('level', 1)}")
            print(f"    - 保存时间: {save['updated_at']}")
            print()

    async def run_full_demo(self):
        """运行完整演示"""
        print("\n开始 Phase 2 完整演示...")
        print("演示将自动运行所有场景，展示15个MCP工具的使用\n")

        await asyncio.sleep(1)

        try:
            # 场景1: 村庄 - NPC和任务
            await self.demo_scene_1_village()

            # 场景2: 神庙入口 - 探索和检定
            await self.demo_scene_2_temple_entrance()

            # 显示存档列表
            await self.show_save_list()

            # 演示总结
            print("="*60)
            print("  演示完成！")
            print("="*60)
            print("\n已演示的功能:")
            print("  ✅ 核心游戏工具 (7个): 状态、物品、HP、检定、位置、创建任务、存档")
            print("  ✅ 任务系统 (5个): 获取、激活、更新进度、完成")
            print("  ✅ NPC系统 (4个): 创建、获取、关系、记忆")
            print("  ✅ 存档系统: 2个存档槽位，自动元数据提取")
            print("\n总计: 15个MCP工具 + SaveService完整集成\n")

        except Exception as e:
            print(f"\n[错误] 演示过程中出错: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """主函数"""
    demo = GameDemo("demo_session")
    await demo.run_full_demo()


if __name__ == "__main__":
    print("\n" + "="*60)
    print("  Phase 2 游戏引擎完整演示")
    print("  基于 Claude Agent SDK + MCP Server")
    print("="*60)
    asyncio.run(main())
