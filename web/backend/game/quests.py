"""
任务系统 - 数据驱动的任务管理和规则引擎
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel

from .game_tools import GameState, GameTools, Quest
from utils.logger import get_logger

logger = get_logger(__name__)


class QuestCondition(BaseModel):
    """任务条件"""
    type: str
    # 可选字段根据type不同
    location: Optional[str] = None
    item_id: Optional[str] = None
    flag: Optional[str] = None
    min: Optional[int] = None
    max: Optional[int] = None
    action_contains: Optional[List[str]] = None


class QuestStage(BaseModel):
    """任务阶段"""
    id: str
    name: str
    description: str
    conditions: List[QuestCondition]
    hints: List[str] = []


class QuestReward(BaseModel):
    """任务奖励"""
    type: str  # experience, item, flag, unlock_location
    value: Optional[int] = None
    flag: Optional[str] = None
    location: Optional[str] = None
    item_id: Optional[str] = None
    item_name: Optional[str] = None
    quantity: Optional[int] = 1


class QuestConfig(BaseModel):
    """任务配置"""
    id: str
    title: str
    description: str
    triggers: List[QuestCondition]
    stages: List[QuestStage]
    rewards: List[QuestReward]
    fail_conditions: List[QuestCondition] = []
    initial_hints: List[str] = []


class QuestEngine:
    """任务引擎 - 规则检查与任务推进"""

    def __init__(self, quest_data_path: str):
        """
        初始化任务引擎

        Args:
            quest_data_path: 任务配置文件目录路径
        """
        self.quest_data_path = Path(quest_data_path)
        self.quest_configs: Dict[str, QuestConfig] = {}
        self._load_quests()

    def _load_quests(self):
        """从YAML文件加载所有任务配置"""
        if not self.quest_data_path.exists():
            logger.warning(f"[WARNING] 任务目录不存在: {self.quest_data_path}")
            return

        for quest_file in self.quest_data_path.glob("*.yaml"):
            try:
                with open(quest_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    config = QuestConfig(**data)
                    self.quest_configs[config.id] = config
                    logger.info(f"[INFO] 加载任务: {config.id} - {config.title}")
            except Exception as e:
                logger.error(f"[ERROR] 加载任务失败 {quest_file}: {e}")

    def check_condition(
        self,
        condition: QuestCondition,
        state: GameState,
        tools: GameTools,
        last_player_input: Optional[str] = None
    ) -> bool:
        """
        检查单个条件是否满足

        Args:
            condition: 条件对象
            state: 游戏状态
            tools: 游戏工具
            last_player_input: 最近的玩家输入

        Returns:
            bool: 条件是否满足
        """
        if condition.type == "always":
            return True

        elif condition.type == "location":
            return state.player.location == condition.location

        elif condition.type == "has_item":
            item = tools.get_inventory_item(condition.item_id)
            return item is not None

        elif condition.type == "flag_exists":
            flag_value = tools.get_flag(condition.flag)
            return flag_value is not None

        elif condition.type == "flag_not_exists":
            flag_value = tools.get_flag(condition.flag)
            return flag_value is None

        elif condition.type == "flag_equals":
            flag_value = tools.get_flag(condition.flag)
            return flag_value == condition.value  # type: ignore

        elif condition.type == "turn_count":
            if condition.min and state.world.time < condition.min:
                return False
            if condition.max and state.world.time > condition.max:
                return False
            return True

        elif condition.type == "location_changed":
            # 需要上下文信息,暂时简化处理
            return state.player.location != condition.location

        elif condition.type == "player_action":
            if not last_player_input or not condition.action_contains:
                return False
            return any(keyword in last_player_input for keyword in condition.action_contains)

        else:
            logger.warning(f"[WARNING] 未知条件类型: {condition.type}")
            return False

    def check_quest_trigger(
        self,
        quest_config: QuestConfig,
        state: GameState,
        tools: GameTools
    ) -> bool:
        """检查任务是否应该被触发"""
        return all(
            self.check_condition(cond, state, tools)
            for cond in quest_config.triggers
        )

    def check_stage_completion(
        self,
        stage: QuestStage,
        state: GameState,
        tools: GameTools,
        last_player_input: Optional[str] = None
    ) -> bool:
        """检查任务阶段是否完成"""
        return all(
            self.check_condition(cond, state, tools, last_player_input)
            for cond in stage.conditions
        )

    def update_quests(
        self,
        state: GameState,
        tools: GameTools,
        last_player_input: Optional[str] = None
    ) -> List[str]:
        """
        更新所有任务状态

        Returns:
            List[str]: 事件消息列表(新激活的任务、完成的阶段等)
        """
        events = []

        # 检查是否有新任务需要激活
        for quest_id, quest_config in self.quest_configs.items():
            # 检查任务是否已存在(包括已完成的)
            existing_quest = next(
                (q for q in state.quests if q.id == quest_id),
                None
            )

            # 只有当任务不存在时才检查触发条件
            if existing_quest is None:
                # 检查触发条件
                if self.check_quest_trigger(quest_config, state, tools):
                    # 激活任务
                    new_quest = Quest(
                        id=quest_config.id,
                        title=quest_config.title,
                        description=quest_config.description,
                        status="active",
                        hints=quest_config.initial_hints.copy(),
                        objectives=[]
                    )
                    state.quests.append(new_quest)
                    events.append(f"📜 新任务激活: {quest_config.title}")
                    logger.info(f"[INFO] 激活任务: {quest_id}")

        # 检查已激活任务的进度
        for quest in state.quests:
            if quest.status != "active":
                continue

            quest_config = self.quest_configs.get(quest.id)
            if not quest_config:
                continue

            # 检查各阶段完成情况
            for stage in quest_config.stages:
                # 检查这个阶段是否已完成
                stage_completed = any(
                    obj.id == stage.id and obj.completed
                    for obj in quest.objectives
                )

                if not stage_completed:
                    # 检查是否满足完成条件
                    if self.check_stage_completion(stage, state, tools, last_player_input):
                        # 标记阶段完成
                        from game_tools import QuestObjective

                        objective = QuestObjective(
                            id=stage.id,
                            description=stage.name,
                            completed=True
                        )
                        quest.objectives.append(objective)
                        events.append(f"✅ 任务进度: {quest.title} - {stage.name}")
                        logger.info(f"[INFO] 完成阶段: {quest.id}/{stage.id}")

            # 检查任务是否全部完成
            all_stages_done = len(quest.objectives) == len(quest_config.stages)
            if all_stages_done and quest.status == "active":
                quest.status = "completed"
                events.append(f"🎉 任务完成: {quest.title}")

                # 发放奖励
                reward_msgs = self.grant_rewards(quest_config, state, tools)
                events.extend(reward_msgs)
                logger.info(f"[INFO] 任务完成: {quest.id}")

        return events

    def grant_rewards(
        self,
        quest_config: QuestConfig,
        state: GameState,
        tools: GameTools
    ) -> List[str]:
        """发放任务奖励"""
        messages = []

        for reward in quest_config.rewards:
            if reward.type == "experience":
                messages.append(f"💫 获得 {reward.value} 点经验")

            elif reward.type == "item":
                tools.add_item(
                    item_id=reward.item_id,  # type: ignore
                    name=reward.item_name or reward.item_id,  # type: ignore
                    quantity=reward.quantity or 1
                )
                messages.append(f"🎁 获得物品: {reward.item_name} x{reward.quantity}")

            elif reward.type == "flag":
                tools.set_flag(reward.flag, True)  # type: ignore
                messages.append(f"🏁 设置标志: {reward.flag}")

            elif reward.type == "unlock_location":
                tools.unlock_location(reward.location)  # type: ignore
                messages.append(f"🗺️ 解锁地点: {reward.location}")

        return messages

    def get_active_quest_hints(self, state: GameState) -> List[str]:
        """获取当前活跃任务的提示"""
        hints = []

        for quest in state.quests:
            if quest.status != "active":
                continue

            quest_config = self.quest_configs.get(quest.id)
            if not quest_config:
                continue

            # 获取下一个未完成阶段的提示
            for stage in quest_config.stages:
                stage_completed = any(
                    obj.id == stage.id and obj.completed
                    for obj in quest.objectives
                )

                if not stage_completed and stage.hints:
                    hints.extend([f"[{quest.title}] {hint}" for hint in stage.hints[:2]])
                    break  # 只显示第一个未完成阶段的提示

        return hints
