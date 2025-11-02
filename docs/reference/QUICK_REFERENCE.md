# 快速参考指南
Quick Reference Guide

> 系统核心功能速查手册

---

## 📦 新增核心模块

### 1. 可编辑设定系统

**位置**: `src/models/editable_setting.py`

```python
from src.models.editable_setting import EditableNovelSetting, NovelTypeConfig

# 创建空白设定
setting = EditableNovelSetting.create_empty("scifi")  # 或 "xianxia"

# 从旧配置迁移
setting = EditableNovelSetting.from_json_config(old_config_dict)

# 修改主角
setting.update_protagonist(name="新名字", role="新职业")

# 添加地点(真实层,主角未知)
setting.add_location("lab_01", {
    "name": "实验室01",
    "type": "restricted_area",
    "secrets": ["隐藏的数据终端"]
})

# 主角探索发现
setting.protagonist_discovers("lab_01", level="partial",
                              revealed_keys=["name", "type"])

# 获取主角视角(用于生成章节提示词)
view = setting.get_protagonist_view()
```

---

### 2. NPC按需生成

**位置**: `src/models/npc_lifecycle.py`

```python
from src.models.npc_lifecycle import NPCPool, NPCGenerator, NPCSeed

# 初始化NPC池
pool = NPCPool()

# 添加NPC种子
seed = pool.add_seed(
    archetype="mentor",  # mentor/companion/opponent/neutral
    role_in_story="神秘科学家",
    spawn_conditions=["主角到达实验室", "触发警报"],
    seed_description="知晓实验真相的老博士",
    generation_constraints={"faction": "科学院", "power_level": 7},
    priority=8
)

# 检查哪些种子可以生成
ready_seeds = pool.check_spawn_conditions(world_state)

# 生成NPC(使用LLM)
generator = NPCGenerator(llm_client)
npc_data = await generator.generate_npc_from_seed(seed, world_context)
npc = pool.instantiate_npc(seed, npc_data)

# NPC互动
npc.engage("主角与博士进行了长谈,了解了实验的真相")
npc.adapt({"relationships": {"protagonist": 50}})  # 关系+50

# 获取活跃NPC
active_npcs = pool.get_active_npcs()
npcs_at_lab = pool.get_npcs_at_location("lab_01")
```

---

### 3. 事件线评分

**位置**: `src/director/event_scorer.py`

```python
from src.director.event_scorer import EventScorer, DynamicWeightAdjuster

# 创建评分器
scorer = EventScorer(
    preference="hybrid",  # playability/narrative/hybrid
    playability_weight=0.6,
    narrative_weight=0.4
)

# 评分事件
score = scorer.score_event(
    event_data={
        "event_id": "E01",
        "puzzles": ["解密终端", "绕过安保"],
        "required_skills": ["hacking", "stealth"],
        "rewards": {"intel": 5},
        ...
    },
    world_state=current_world_state,
    history=game_history
)

print(f"综合得分: {score.weighted_score:.2f}")
print(f"停滞风险: {score.stall_risk:.2f}")

# 动态调节权重
adjuster = DynamicWeightAdjuster(base_playability_weight=0.6,
                                 base_narrative_weight=0.4)

new_play_w, new_narr_w = adjuster.adjust_weights(
    history={"consecutive_stall_turns": 3},  # 停滞3回合
    pending_setups=overdue_setups
)
```

---

### 4. 线索经济管理

**位置**: `src/director/clue_economy.py`

```python
from src.director.clue_economy import ClueEconomyManager

manager = ClueEconomyManager(red_herring_cap=2)

# 注册线索
clue = manager.register_clue(
    content="墙上有奇怪符号",
    clue_type="implicit",  # implicit/explicit/red_herring
    related_secret="实验室密码",
    verification_method="解密"
)

# 创建伏笔(带SLA)
setup = manager.create_setup(
    description="主角承诺找出真相",
    setup_type="promise",  # foreshadowing/promise/mystery/question
    deadline_turns=20,
    priority="high"
)

# 创建证据链
chain = manager.create_evidence_chain(
    target_conclusion="实验室发生过事故",
    logic_type="convergent"  # sequential/convergent/elimination
)
manager.add_evidence_to_chain(chain.chain_id, clue.clue_id)

# 回合推进
manager.tick_all_setups()

# 检查债务
overdue = manager.get_overdue_setups()
urgent = manager.get_urgent_setups(threshold=0.7)
stats = manager.get_debt_stats()

# 健康度检查
health = manager.get_economy_health()
print(f"健康度: {health['overall_health']:.2%}")
print(f"伏笔偿还率: {health['payoff_rate']:.2%}")

# 智能建议
suggestions = manager.suggest_next_clues()
```

---

### 5. 一致性审计

**位置**: `src/director/consistency_auditor.py`

```python
from src.director.consistency_auditor import ConsistencyAuditor, AutoFixer

# 创建审计器
auditor = ConsistencyAuditor(
    hard_rules=[
        "能量守恒",
        "禁止读心",
        "因果自洽",
        "技术推演符合基本物理规律"
    ],
    soft_rules=["主题一致性"]
)

# 审计内容
report = auditor.audit_content(
    content=chapter_text,
    world_state=current_world_state,
    history=game_history,
    content_type="chapter"
)

if not report.passed:
    print(f"❌ 审计未通过:")
    print(f"  严重问题: {report.critical_count}")
    print(f"  高优先级: {report.high_count}")

    for issue in report.issues:
        print(f"\n[{issue['severity']}] {issue['category']}")
        print(f"  问题: {issue['description']}")
        print(f"  位置: {issue['location']}")
        print(f"  建议: {issue['suggestion']}")

# 自动修复建议
fixer = AutoFixer(llm_client)
fixes = await fixer.suggest_fixes(chapter_text, report)
```

---

### 6. 会话历史管理

**位置**: `src/models/conversation_history.py`

```python
from src.models.conversation_history import ConversationSession, Message

# 创建会话
session = ConversationSession(novel_id="novel_123")

# 添加消息
session.add_message(
    role="user",
    content="我选择调查实验室",
    message_type="choice",
    metadata={"choice_id": "investigate_lab"}
)

session.add_message(
    role="assistant",
    content="你进入了昏暗的实验室...",
    message_type="chapter",
    metadata={"chapter_num": 3}
)

# 获取历史
recent = session.get_conversation_history(limit=10)
context = session.get_active_branch().get_context_window(max_tokens=4000)

# 创建分支
new_branch = session.create_branch(
    branch_name="支线:秘密调查",
    from_message_id=last_choice_id
)

# 导出Markdown
markdown = session.export_to_markdown()
with open("conversation.md", "w") as f:
    f.write(markdown)
```

---

## 🎯 典型工作流

### 初始化新小说

```python
from src.models.editable_setting import EditableNovelSetting
from src.models.npc_lifecycle import NPCPool
from src.director.clue_economy import ClueEconomyManager
from src.director.event_scorer import EventScorer
from src.director.consistency_auditor import ConsistencyAuditor
from src.models.conversation_history import ConversationSession

# 1. 创建设定
setting = EditableNovelSetting.create_empty("scifi")
setting.world_setting.title = "星际迷航"
setting.world_setting.setting_text = "2157年,深空探索遭遇未知..."

setting.protagonist.name = "艾莉克斯"
setting.protagonist.role = "工程师"

# 2. 添加世界元素
setting.add_location("station_alpha", {
    "name": "阿尔法空间站",
    "status": "失联",
    "secrets": ["隐藏的AI核心"]
})

setting.add_faction("united_colonies", {
    "name": "联合殖民地",
    "type": "government",
    "stance": "neutral"
})

# 3. 添加NPC种子(不立即生成)
npc_pool = NPCPool()
npc_pool.add_seed(
    archetype="mentor",
    role_in_story="老船长",
    spawn_conditions=["到达空间站"],
    seed_description="经验丰富的太空船长"
)

# 4. 初始化管理器
clue_manager = ClueEconomyManager()
event_scorer = EventScorer(preference="hybrid")
auditor = ConsistencyAuditor(hard_rules=setting.constraints["hard_rules"])
conversation = ConversationSession(novel_id="novel_123")

# 5. 保存设定
# (TODO: 实现数据库保存逻辑)
```

---

### 生成章节流程

```python
async def generate_chapter_with_audit(
    user_input: str,
    setting: EditableNovelSetting,
    npc_pool: NPCPool,
    clue_manager: ClueEconomyManager,
    auditor: ConsistencyAuditor,
    llm_client
):
    # 1. 检查NPC生成条件
    ready_npcs = npc_pool.check_spawn_conditions(world_state)
    for seed in ready_npcs[:2]:  # 最多生成2个
        generator = NPCGenerator(llm_client)
        npc_data = await generator.generate_npc_from_seed(seed, world_context)
        npc = npc_pool.instantiate_npc(seed, npc_data)

    # 2. 获取主角视角(隐藏未发现的世界元素)
    protagonist_view = setting.get_protagonist_view()

    # 3. 构建提示词
    prompt = build_chapter_prompt(
        protagonist_view=protagonist_view,
        user_input=user_input,
        active_npcs=npc_pool.get_active_npcs(),
        discovered_clues=clue_manager.get_discovered_clues()
    )

    # 4. 生成章节
    chapter_text = await llm_client.generate(prompt)

    # 5. 审计内容
    report = auditor.audit_content(
        content=chapter_text,
        world_state=world_state,
        history=game_history
    )

    # 6. 如果审计未通过,尝试修复
    if not report.passed and report.critical_count > 0:
        fixer = AutoFixer(llm_client)
        fixes = await fixer.suggest_fixes(chapter_text, report)

        if fixes["rewrite_suggestion"]:
            # 重新生成
            chapter_text = await llm_client.generate(prompt + "\n修正要求:\n" + str(fixes))
        else:
            # 应用修复
            for fix in fixes["fixes"]:
                # 应用修复建议
                pass

    # 7. 更新状态
    # - 主角可能发现新元素
    # - NPC互动
    # - 线索注册
    # - 伏笔兑现

    # 8. 推进回合
    clue_manager.tick_all_setups()

    return chapter_text, report
```

---

## 📊 关键数据结构

### EditableNovelSetting

```python
{
    "novel_type_config": {
        "novel_type": "scifi",
        "playability_weight": 0.6,
        "narrative_weight": 0.4
    },
    "world_setting": {
        "title": "...",
        "setting_text": "...",
        "locations": {...},
        "factions": {...},
        "knowledge_layer": {  # 主角探索发现
            "loc_01": {
                "discovery_status": "partial",
                "protagonist_knowledge": {"name": "..."}
            }
        }
    },
    "protagonist": {...},
    "routes": [...]
}
```

### NPCPool

```python
{
    "seeds": {
        "seed_01": {
            "archetype": "mentor",
            "status": "dormant",  # dormant/ready/instantiated
            "spawn_conditions": [...]
        }
    },
    "instances": {
        "npc_01": {
            "lifecycle_stage": "engaged",  # instantiated/engaged/adapted/retired
            "relationships": {"protagonist": 50}
        }
    }
}
```

### ClueEconomyManager

```python
{
    "clues": {
        "clue_01": {
            "discovered": true,
            "verified": false,
            "reliability": 1.0
        }
    },
    "setup_debts": {
        "setup_01": {
            "current_turn": 15,
            "deadline_turns": 20,
            "is_overdue": false,
            "urgency": 0.75
        }
    }
}
```

---

## 🚀 下一步

### 待完成任务

1. **全局导演整合** (`src/director/global_director.py`)
   - 整合所有管理器
   - 实现回合循环
   - 事件选择逻辑

2. **初始化流程改造**
   - 支持可编辑设定
   - NPC种子创建
   - 事件线生成

3. **Web界面更新**
   - 设定编辑器
   - 历史查看
   - NPC管理面板
   - 线索看板

4. **API更新**
   - `/api/setting/edit` - 编辑设定
   - `/api/npcs/pool` - NPC池状态
   - `/api/clues/economy` - 线索经济健康度
   - `/api/conversation/history` - 会话历史

---

## ❓ 常见问题

**Q: 如何迁移旧的JSON配置?**
```python
old_config = load_json("examples/scifi_example.json")
new_setting = EditableNovelSetting.from_json_config(old_config)
```

**Q: 如何让主角逐步发现世界?**
```python
# 1. 添加元素时默认主角不知道
setting.add_location("secret_lab", {...})

# 2. 剧情推进时让主角发现
setting.protagonist_discovers("secret_lab", level="partial",
                              revealed_keys=["name", "type"])

# 3. 生成章节时只使用主角已知部分
protagonist_view = setting.get_protagonist_view()
```

**Q: 如何平衡可玩性和叙事?**
```python
# 使用混合模式+动态调节
scorer = EventScorer(preference="hybrid")
adjuster = DynamicWeightAdjuster()

# 根据游戏状态自动调节
new_weights = adjuster.adjust_weights(history, pending_setups)
```

**Q: 如何管理伏笔债务?**
```python
# 创建伏笔时设置SLA
setup = manager.create_setup(
    description="...",
    deadline_turns=20  # 20章内必须兑现
)

# 定期检查逾期
overdue = manager.get_overdue_setups()
if overdue:
    # 优先安排兑现事件
    pass
```

---

## 📖 完整文档

- **架构设计**: `docs/architecture/ARCHITECTURE.md`
- **改进总结**: `docs/architecture/IMPROVEMENTS_SUMMARY.md`
- **项目指引**: `CLAUDE.md`
- **快速开始**: `README.md`
