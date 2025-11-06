"""
世界校验器
提供完整的世界数据校验，包括引用完整性、DAG检测、业务规则等
"""

from typing import List, Dict, Set, Tuple
from models.world_pack import WorldPack, Quest, NPC, Location


class ValidationProblem:
    """校验问题"""

    def __init__(
        self,
        severity: str,  # "error" / "warning" / "info"
        category: str,  # "reference" / "dag" / "business" / "data"
        message: str,
        entity_id: str = None
    ):
        self.severity = severity
        self.category = category
        self.message = message
        self.entity_id = entity_id

    def __repr__(self):
        prefix = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(self.severity, "?")
        return f"{prefix} [{self.category}] {self.message}"


class WorldValidator:
    """世界校验器"""

    def __init__(self):
        self.problems: List[ValidationProblem] = []

    def validate_all(self, world_pack: WorldPack) -> List[ValidationProblem]:
        """
        执行完整的世界校验

        Args:
            world_pack: 世界包

        Returns:
            List[ValidationProblem]: 问题列表
        """
        self.problems = []

        # 1. 引用完整性
        self._validate_references(world_pack)

        # 2. 任务 DAG
        self._validate_quest_dag(world_pack)

        # 3. 业务规则
        self._validate_business_rules(world_pack)

        # 4. 数据质量
        self._validate_data_quality(world_pack)

        return self.problems

    def _validate_references(self, world_pack: WorldPack):
        """校验引用完整性"""

        # 构建 ID 集合
        location_ids = {loc.id for loc in world_pack.locations}
        npc_ids = {npc.id for npc in world_pack.npcs}
        loot_table_ids = {t.id for t in world_pack.loot_tables}
        encounter_table_ids = {t.id for t in world_pack.encounter_tables}

        # 检查 NPC 的 home_location
        for npc in world_pack.npcs:
            if npc.home_location_id and npc.home_location_id not in location_ids:
                self.problems.append(ValidationProblem(
                    severity="error",
                    category="reference",
                    message=f"NPC '{npc.name}' 引用不存在的地点: {npc.home_location_id}",
                    entity_id=npc.id
                ))

            # 检查 NPC 关系
            for other_npc_id in npc.relationship.keys():
                if other_npc_id not in npc_ids:
                    self.problems.append(ValidationProblem(
                        severity="warning",
                        category="reference",
                        message=f"NPC '{npc.name}' 的关系引用不存在的 NPC: {other_npc_id}",
                        entity_id=npc.id
                    ))

        # 检查 Location 的 NPCs
        for loc in world_pack.locations:
            for npc_id in loc.npcs:
                if npc_id not in npc_ids:
                    self.problems.append(ValidationProblem(
                        severity="error",
                        category="reference",
                        message=f"地点 '{loc.name}' 引用不存在的 NPC: {npc_id}",
                        entity_id=loc.id
                    ))

            # 检查 POI 的掉落表和遭遇表
            for poi in loc.pois:
                if poi.loot_table_id and poi.loot_table_id not in loot_table_ids:
                    self.problems.append(ValidationProblem(
                        severity="warning",
                        category="reference",
                        message=f"POI '{poi.name}' 引用不存在的掉落表: {poi.loot_table_id}",
                        entity_id=poi.id
                    ))

                if poi.encounter_table_id and poi.encounter_table_id not in encounter_table_ids:
                    self.problems.append(ValidationProblem(
                        severity="warning",
                        category="reference",
                        message=f"POI '{poi.name}' 引用不存在的遭遇表: {poi.encounter_table_id}",
                        entity_id=poi.id
                    ))

        # 检查任务目标依赖
        for quest in world_pack.quests:
            objective_ids = {obj.id for obj in quest.objectives}

            for obj in quest.objectives:
                for req_id in obj.require:
                    if req_id not in objective_ids:
                        self.problems.append(ValidationProblem(
                            severity="error",
                            category="reference",
                            message=f"任务 '{quest.title}' 的目标 '{obj.text}' 引用不存在的依赖: {req_id}",
                            entity_id=quest.id
                        ))

    def _validate_quest_dag(self, world_pack: WorldPack):
        """校验任务依赖 DAG 无环"""

        # 构建任务依赖图
        quest_graph: Dict[str, List[str]] = {}
        for quest in world_pack.quests:
            quest_graph[quest.id] = quest.prereq_quest_ids

        # 拓扑排序检测环
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        cycle_path: List[str] = []

        def has_cycle(node: str, path: List[str]) -> bool:
            """DFS 检测环"""
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in quest_graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor, path):
                        return True
                elif neighbor in rec_stack:
                    # 找到环
                    cycle_start = path.index(neighbor)
                    cycle_path.extend(path[cycle_start:])
                    return True

            path.pop()
            rec_stack.remove(node)
            return False

        for quest_id in quest_graph:
            if quest_id not in visited:
                if has_cycle(quest_id, []):
                    quest_names = []
                    for qid in cycle_path:
                        quest = next((q for q in world_pack.quests if q.id == qid), None)
                        quest_names.append(quest.title if quest else qid)

                    self.problems.append(ValidationProblem(
                        severity="error",
                        category="dag",
                        message=f"任务依赖存在环路: {' -> '.join(quest_names)}",
                        entity_id=cycle_path[0] if cycle_path else None
                    ))
                    break

        # 检查目标依赖环
        for quest in world_pack.quests:
            obj_graph: Dict[str, List[str]] = {}
            for obj in quest.objectives:
                obj_graph[obj.id] = obj.require

            obj_visited: Set[str] = set()
            obj_rec_stack: Set[str] = set()

            def has_obj_cycle(node: str) -> bool:
                obj_visited.add(node)
                obj_rec_stack.add(node)

                for neighbor in obj_graph.get(node, []):
                    if neighbor not in obj_visited:
                        if has_obj_cycle(neighbor):
                            return True
                    elif neighbor in obj_rec_stack:
                        return True

                obj_rec_stack.remove(node)
                return False

            for obj_id in obj_graph:
                if obj_id not in obj_visited:
                    if has_obj_cycle(obj_id):
                        self.problems.append(ValidationProblem(
                            severity="error",
                            category="dag",
                            message=f"任务 '{quest.title}' 的目标依赖存在环路",
                            entity_id=quest.id
                        ))
                        break

    def _validate_business_rules(self, world_pack: WorldPack):
        """校验业务规则"""

        # 规则1: 每个世界至少有 3 个地点
        if len(world_pack.locations) < 3:
            self.problems.append(ValidationProblem(
                severity="warning",
                category="business",
                message=f"地点数量过少: {len(world_pack.locations)} (建议至少 3 个)"
            ))

        # 规则2: 每个世界至少有 1 个主线任务
        main_quests = [q for q in world_pack.quests if q.line == "main"]
        if len(main_quests) == 0:
            self.problems.append(ValidationProblem(
                severity="warning",
                category="business",
                message="没有主线任务"
            ))

        # 规则3: 地点名称不重复
        location_names = [loc.name for loc in world_pack.locations]
        if len(location_names) != len(set(location_names)):
            duplicates = [name for name in location_names if location_names.count(name) > 1]
            self.problems.append(ValidationProblem(
                severity="warning",
                category="business",
                message=f"地点名称重复: {', '.join(set(duplicates))}"
            ))

        # 规则4: NPC 名称不重复
        npc_names = [npc.name for npc in world_pack.npcs]
        if len(npc_names) != len(set(npc_names)):
            duplicates = [name for name in npc_names if npc_names.count(name) > 1]
            self.problems.append(ValidationProblem(
                severity="warning",
                category="business",
                message=f"NPC 名称重复: {', '.join(set(duplicates))}"
            ))

        # 规则5: 坐标不能超出地图范围
        map_width = world_pack.meta.map_size.get("w", 64)
        map_height = world_pack.meta.map_size.get("h", 64)

        for loc in world_pack.locations:
            if not (0 <= loc.coord.x < map_width and 0 <= loc.coord.y < map_height):
                self.problems.append(ValidationProblem(
                    severity="error",
                    category="business",
                    message=f"地点 '{loc.name}' 坐标超出地图范围: ({loc.coord.x}, {loc.coord.y})",
                    entity_id=loc.id
                ))

        # 规则6: 每个地点至少有 1 个 POI
        for loc in world_pack.locations:
            if len(loc.pois) == 0:
                self.problems.append(ValidationProblem(
                    severity="info",
                    category="business",
                    message=f"地点 '{loc.name}' 没有兴趣点",
                    entity_id=loc.id
                ))

    def _validate_data_quality(self, world_pack: WorldPack):
        """校验数据质量"""

        # 检查空字符串
        for loc in world_pack.locations:
            if not loc.name.strip():
                self.problems.append(ValidationProblem(
                    severity="error",
                    category="data",
                    message=f"地点名称为空: {loc.id}",
                    entity_id=loc.id
                ))

        for npc in world_pack.npcs:
            if not npc.name.strip():
                self.problems.append(ValidationProblem(
                    severity="error",
                    category="data",
                    message=f"NPC 名称为空: {npc.id}",
                    entity_id=npc.id
                ))

            if not npc.persona.strip():
                self.problems.append(ValidationProblem(
                    severity="warning",
                    category="data",
                    message=f"NPC '{npc.name}' 缺少 persona",
                    entity_id=npc.id
                ))

        for quest in world_pack.quests:
            if not quest.title.strip():
                self.problems.append(ValidationProblem(
                    severity="error",
                    category="data",
                    message=f"任务标题为空: {quest.id}",
                    entity_id=quest.id
                ))

            if len(quest.objectives) == 0:
                self.problems.append(ValidationProblem(
                    severity="warning",
                    category="data",
                    message=f"任务 '{quest.title}' 没有目标",
                    entity_id=quest.id
                ))

    def get_summary(self) -> Dict[str, int]:
        """获取问题统计"""
        return {
            "total": len(self.problems),
            "errors": len([p for p in self.problems if p.severity == "error"]),
            "warnings": len([p for p in self.problems if p.severity == "warning"]),
            "info": len([p for p in self.problems if p.severity == "info"])
        }

    def has_errors(self) -> bool:
        """是否有错误"""
        return any(p.severity == "error" for p in self.problems)
