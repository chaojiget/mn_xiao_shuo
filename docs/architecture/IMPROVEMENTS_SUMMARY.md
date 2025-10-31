# 系统改进总结
Architecture Improvements Summary

> 最后更新: 2025-01-31

---

## 改进概览

本次改进实现了完整的全局导演(Global Director)架构,将系统从"简单LLM包装器"升级为"事件驱动的智能叙事引擎"。

### 核心理念

**之前**: 线性生成 → 用户输入 → LLM生成章节 → 保存
**现在**: 设定编辑 → 事件线评分 → NPC按需生成 → 一致性审计 → 线索经济管理 → 生成

---

## ✅ 已实现功能

### 1. 可编辑设定系统 (`src/models/editable_setting.py`)

**核心特性**:
- **世界知识分层**: 真实层(系统持有) vs 主角已知层(玩家视角)
- **探索发现机制**: 主角通过游戏过程逐步发现世界真相
- **动态增删改查**: 支持运行时修改世界观、主角、地点、势力等

**主要类**:
```python
class EditableNovelSetting:
    - NovelTypeConfig: 科幻/玄幻类型配置,包含评分权重
    - WorldSetting: 世界观,支持知识分层
    - ProtagonistSetting: 主角设定(可编辑)
    - RouteOverview: 路线总览
    - WorldKnowledge: 知识元素(unknown/partial/full)
```

**工作流**:
```python
# 1. 创建设定
setting = EditableNovelSetting.create_empty("scifi")

# 2. 添加地点(仅系统知道,主角未知)
setting.add_location("research_station", {
    "name": "深空研究站",
    "description": "一个被遗弃的研究设施",
    "secrets": ["实验室藏有禁忌技术"]
})

# 3. 主角探索发现
setting.protagonist_discovers("research_station", level="partial",
                              revealed_keys=["name", "description"])

# 4. 获取主角视角(生成章节时使用)
protagonist_view = setting.get_protagonist_view()
```

---

### 2. NPC按需生成机制 (`src/models/npc_lifecycle.py`)

**核心流程**: `seed → instantiate → engage → adapt → retire`

**主要类**:
```python
class NPCSeed:  # NPC种子(潜在存在)
    - archetype: mentor/companion/opponent
    - spawn_conditions: 生成触发条件
    - generation_constraints: 生成约束

class NPCInstance:  # NPC实例(已生成)
    - 基本信息(name, role, personality)
    - 关系网(relationships)
    - 知识(known_secrets, can_provide_clues)
    - 生命周期(instantiated/engaged/adapted/retired)

class NPCPool:  # NPC池管理器
    - seeds: 种子池
    - instances: 实例池
    - active_npc_ids: 活跃NPC列表
```

**使用示例**:
```python
# 1. 添加NPC种子
pool = NPCPool()
seed = pool.add_seed(
    archetype="mentor",
    role_in_story="神秘导师",
    spawn_conditions=["主角到达研究站", "触发特定事件"],
    seed_description="一个知晓真相的老科学家"
)

# 2. 检查生成条件
ready_seeds = pool.check_spawn_conditions(world_state)

# 3. 生成NPC(使用LLM)
generator = NPCGenerator(llm_client)
npc_data = await generator.generate_npc_from_seed(seed, world_context)
npc = pool.instantiate_npc(seed, npc_data)

# 4. 互动与适应
npc.engage("主角与导师进行了深入对话")
npc.adapt({"relationships": {"protagonist": 30}})  # 好感度+30
```

**优势**:
- **节省资源**: 不预先生成所有NPC
- **剧情驱动**: 根据故事需要动态创建
- **自适应**: NPC随剧情发展改变

---

### 3. 事件线评分系统 (`src/director/event_scorer.py`)

**三种评分模式**:
- **A) 可玩性优先** (playability): 谜题、技能检定、奖励循环
- **B) 叙事优先** (narrative): 主题、冲突、伏笔兑现
- **C) 混合模式** (hybrid): 动态平衡

**核心指标**:

**可玩性指标** (`PlayabilityMetrics`):
```python
- puzzle_density: 谜题密度 (0-1)
- skill_checks_variety: 技能检定多样性
- failure_grace: 失败宽容度
- hint_latency: 提示延迟
- exploit_resistance: 防刷抗性
- reward_loop: 奖励循环质量
```

**叙事性指标** (`NarrativeMetrics`):
```python
- arc_progress: 事件线推进度
- theme_echo: 主题回响
- conflict_gradient: 冲突梯度
- payoff_debt: 伏笔偿还率
- scene_specificity: 场景具体性
- pacing_smoothness: 节奏平滑度
```

**使用示例**:
```python
scorer = EventScorer(preference="hybrid",
                     playability_weight=0.6,
                     narrative_weight=0.4)

score = scorer.score_event(event_data, world_state, history)

print(f"综合得分: {score.weighted_score:.2f}")
print(f"可玩性: {score.playability.overall_score():.2f}")
print(f"叙事性: {score.narrative.overall_score():.2f}")
print(f"停滞风险: {score.stall_risk:.2f}")
```

**动态权重调节**:
```python
adjuster = DynamicWeightAdjuster()

# 根据游戏状态自动调节
playability_w, narrative_w = adjuster.adjust_weights(
    history={"consecutive_stall_turns": 3},  # 停滞3回合
    pending_setups=overdue_setups  # 逾期伏笔
)
# → 自动提高可玩性权重(降低难度)
# → 自动提高叙事权重(兑现伏笔)
```

---

### 4. 线索经济管理 (`src/director/clue_economy.py`)

**核心概念**:
- **线索注册**: 隐性/显性/红鲱鱼
- **伏笔债务**: SLA截止时间,逾期告警
- **证据链**: 多线索汇聚验证
- **经济健康度**: 偿还率、发现率、完成度

**主要类**:
```python
class ClueInstance:  # 线索实例
    - clue_type: implicit/explicit/red_herring
    - discovered: 是否已发现
    - verified: 是否已验证
    - reliability: 可靠性(0-1)

class SetupDebt:  # 伏笔债务
    - deadline_turns: SLA截止回合
    - is_overdue: 是否逾期
    - urgency: 紧迫度(0-1)

class EvidenceChain:  # 证据链
    - logic_type: sequential/convergent/elimination
    - completeness: 完整性(0-1)

class ClueEconomyManager:  # 管理器
    - clues: 线索池
    - setup_debts: 伏笔债务池
    - evidence_chains: 证据链池
```

**使用示例**:
```python
manager = ClueEconomyManager(red_herring_cap=2)

# 1. 注册线索
clue1 = manager.register_clue(
    content="实验室墙上有奇怪的符号",
    clue_type="implicit",
    related_secret="禁忌技术的启动密码",
    verification_method="解密符号"
)

# 2. 创建伏笔
setup = manager.create_setup(
    description="主角承诺会找到真相",
    setup_type="promise",
    deadline_turns=20,  # 20章内必须兑现
    priority="high"
)

# 3. 创建证据链
chain = manager.create_evidence_chain(
    target_conclusion="研究站发生过重大事故",
    logic_type="convergent"  # 多证据汇聚
)
manager.add_evidence_to_chain(chain.chain_id, clue1.clue_id)

# 4. 回合推进与检查
manager.tick_all_setups()
overdue = manager.get_overdue_setups()  # 获取逾期伏笔
urgent = manager.get_urgent_setups(threshold=0.7)  # 获取紧迫伏笔

# 5. 健康度检查
health = manager.get_economy_health()
print(f"线索经济健康度: {health['overall_health']:.2f}")
print(f"伏笔偿还率: {health['payoff_rate']:.2%}")
```

**智能建议**:
```python
suggestions = manager.suggest_next_clues()
# → ["投放线索兑现伏笔: 主角承诺会找到真相...",
#    "补充证据链: 研究站发生过重大事故...",
#    "可投放红鲱鱼增加悬念"]
```

---

### 5. 一致性审计系统 (`src/director/consistency_auditor.py`)

**审计类别**:
1. **硬规则** (Hard Rules): 能量守恒、禁止读心、因果自洽
2. **因果一致性**: 前置条件、事件引用
3. **资源守恒**: 资源消耗/来源合理性
4. **角色一致性**: 行为与性格匹配
5. **时间线一致性**: 时间顺序、间隔合理
6. **主题一致性**: 内容呼应核心主题

**使用示例**:
```python
auditor = ConsistencyAuditor(
    hard_rules=[
        "能量守恒",
        "禁止读心",
        "因果自洽",
        "技术推演符合基本物理规律"
    ]
)

# 审计章节内容
report = auditor.audit_content(
    content=chapter_text,
    world_state=world_state,
    history=history,
    content_type="chapter"
)

if not report.passed:
    print(f"发现 {report.critical_count} 个严重问题:")
    for issue in report.issues:
        print(f"  [{issue['severity']}] {issue['description']}")
        print(f"  建议: {issue['suggestion']}")
```

**自动修复建议**:
```python
fixer = AutoFixer(llm_client)
fixes = await fixer.suggest_fixes(chapter_text, report)

if fixes["rewrite_suggestion"]:
    print("建议重写整段内容")
else:
    for fix in fixes["fixes"]:
        print(f"问题 {fix['issue_index']}: {fix['fix_description']}")
        print(f"建议文本: {fix['suggested_text']}")
```

---

### 6. 会话历史管理 (`src/models/conversation_history.py`)

**核心特性**:
- **完整记录**: 用户与系统的所有对话
- **分支管理**: 支持多条探索路径
- **上下文窗口**: 智能截取相关历史
- **导出功能**: Markdown格式导出

**主要类**:
```python
class Message:  # 单条消息
    - role: user/assistant/system
    - content: 消息内容
    - message_type: text/choice/setting_edit/chapter
    - metadata: 附加数据

class ConversationBranch:  # 对话分支
    - messages: 消息列表
    - get_recent_messages(n): 获取最近N条
    - get_context_window(max_tokens): 智能截取上下文

class ConversationSession:  # 完整会话
    - branches: 分支字典
    - active_branch_id: 当前活跃分支
    - create_branch(): 创建新分支
    - switch_branch(): 切换分支
```

**使用示例**:
```python
session = ConversationSession(novel_id="novel_123")

# 1. 添加消息
session.add_message(
    role="user",
    content="我想探索废弃研究站",
    message_type="choice"
)

session.add_message(
    role="assistant",
    content="你小心翼翼地进入研究站...",
    message_type="chapter",
    metadata={"chapter_num": 5}
)

# 2. 创建分支(探索不同路径)
branch = session.create_branch(
    branch_name="支线:调查实验室",
    from_message_id=last_message_id
)

# 3. 导出历史
markdown = session.export_to_markdown()
```

---

## 📐 架构改进对比

### 之前的架构 (Simple LLM Wrapper)

```
用户输入 → 构建简单提示词 → LLM生成 → 保存章节
```

**问题**:
- ❌ 无事件规划
- ❌ 无状态管理
- ❌ 无一致性检查
- ❌ NPC预先生成浪费资源
- ❌ 无伏笔跟踪
- ❌ 无历史会话

### 现在的架构 (Event-Driven Narrative Engine)

```
┌─────────────────────────────────────────────────────────────┐
│  可编辑设定层 (Editable Settings)                            │
│  - WorldSetting (知识分层)                                   │
│  - ProtagonistSetting (可编辑)                              │
│  - RouteOverview (路线规划)                                  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  全局导演 (Global Director) [待实现]                         │
│  - 事件线评分 (EventScorer)                                  │
│  - 事件选择与调度                                             │
│  - NPC池管理 (NPCPool)                                      │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  生成与审计层                                                 │
│  - LLM生成内容                                               │
│  - 一致性审计 (ConsistencyAuditor)                          │
│  - 自动修复建议 (AutoFixer)                                  │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  线索经济管理 (ClueEconomyManager)                           │
│  - 线索注册与发现                                             │
│  - 伏笔债务SLA检查                                           │
│  - 证据链验证                                                 │
└─────────────┬───────────────────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────────────────┐
│  状态更新与持久化                                             │
│  - WorldState更新                                            │
│  - 会话历史记录 (ConversationSession)                        │
│  - 数据库保存                                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 下一步工作

### 1. 创建全局导演核心类 (`src/director/global_director.py`)

需要整合所有组件:
```python
class GlobalDirector:
    def __init__(self, setting: EditableNovelSetting, llm_client, database):
        self.setting = setting
        self.event_scorer = EventScorer(...)
        self.npc_pool = NPCPool()
        self.clue_manager = ClueEconomyManager()
        self.auditor = ConsistencyAuditor(...)
        self.conversation = ConversationSession(...)

    async def run_turn(self, user_input: str):
        # 1. 检查NPC生成条件
        # 2. 评分候选事件
        # 3. 选择最佳事件
        # 4. 生成内容
        # 5. 审计内容
        # 6. 更新状态
        # 7. 更新线索经济
        # 8. 保存历史
```

### 2. 初始化流程改造

```python
# 新的初始化流程
async def initialize_novel(config_dict):
    # 1. 创建可编辑设定
    setting = EditableNovelSetting.from_json_config(config_dict)

    # 2. 添加NPC种子(不立即生成)
    for npc_seed_data in config_dict.get("npc_seeds", []):
        setting.npc_pool.add_seed(...)

    # 3. 创建事件线
    event_arcs = await generate_event_arcs(setting, llm_client)

    # 4. 创建全局导演
    director = GlobalDirector(setting, llm_client, database)

    # 5. 生成首章
    first_chapter = await director.run_turn("开始故事")

    return director, first_chapter
```

### 3. Web界面更新

**新增页面/组件**:
- **设定编辑器**: 可视化编辑世界观、主角、路线
- **路线选择**: 科幻 vs 玄幻,一眼看穿差异
- **历史回顾**: 查看完整对话历史,支持分支切换
- **NPC管理**: 查看种子池、活跃NPC、关系网
- **线索看板**: 已发现线索、待兑现伏笔、证据链进度
- **健康度仪表盘**: 线索经济健康度、审计通过率

---

## 📊 改进成果

### 核心模型层 ✅
- [x] `editable_setting.py` - 可编辑设定系统
- [x] `npc_lifecycle.py` - NPC生命周期管理
- [x] `conversation_history.py` - 会话历史管理

### 导演层 ✅
- [x] `event_scorer.py` - 事件线评分系统
- [x] `clue_economy.py` - 线索经济管理
- [x] `consistency_auditor.py` - 一致性审计系统

### 待实现 ⏳
- [ ] `global_director.py` - 全局导演整合
- [ ] 初始化流程改造
- [ ] Web界面更新
- [ ] API端点更新
- [ ] 测试用例

---

## 🔍 关键差异点总结

### 科幻 vs 玄幻 (一眼看穿)

| 维度 | 科幻超长小说 | 玄幻/仙侠网络小说 |
|------|-------------|------------------|
| **驱动力** | 设定推演(技术→问题→后果) | 成长升级(境界/功法/资源) |
| **红线** | 因果自洽、证据可验证 | 突破要代价、资源守恒 |
| **节奏** | 10-15章一次可检验进展 | 2-3章一个爽点 |
| **评分权重** | 可玩性:叙事 = 0.5:0.5 | 0.7:0.3 |
| **读者预期** | 反直觉但不反常识 | 短反馈、逆袭爽感 |

### NPC生成: 预先 vs 按需

| 方式 | 优点 | 缺点 | 适用场景 |
|------|------|------|----------|
| **预先生成** | 立即可用 | 浪费资源、僵化 | 固定剧本 |
| **按需生成** | 节省资源、灵活 | 需要触发条件 | 动态叙事 ✅ |

### 世界知识: 全知 vs 探索

| 模式 | 玩家体验 | 实现难度 | 叙事深度 |
|------|----------|----------|----------|
| **全知模式** | 一开始就知道所有设定 | 简单 | 低 |
| **探索模式** | 逐步发现世界真相 ✅ | 需要知识分层 | 高 |

---

## 📚 使用指南

### 快速开始

```python
from src.models.editable_setting import EditableNovelSetting, NovelTypeConfig
from src.models.npc_lifecycle import NPCPool, NPCGenerator
from src.director.event_scorer import EventScorer
from src.director.clue_economy import ClueEconomyManager
from src.director.consistency_auditor import ConsistencyAuditor

# 1. 创建设定
setting = EditableNovelSetting.create_empty("scifi")
setting.world_setting.title = "深空迷航"
setting.world_setting.setting_text = "2157年,人类殖民计划遭遇未知危机..."

# 2. 添加主角
setting.protagonist.name = "艾莉克斯"
setting.protagonist.role = "工程师"
setting.protagonist.attributes = {"智力": 8, "技术": 9}

# 3. 添加地点(主角未知)
setting.add_location("abandoned_station", {
    "name": "废弃空间站",
    "description": "一个失联已久的研究设施",
    "secrets": ["隐藏的AI核心", "禁忌实验记录"]
})

# 4. 初始化组件
event_scorer = EventScorer(preference="hybrid")
npc_pool = NPCPool()
clue_manager = ClueEconomyManager()
auditor = ConsistencyAuditor(hard_rules=setting.constraints["hard_rules"])

# 5. 开始游戏循环
# (需要全局导演整合)
```

---

## 🎉 总结

本次改进实现了:

1. **✅ 可编辑设定** - 动态管理世界观,支持探索发现
2. **✅ NPC按需生成** - seed→instantiate→engage完整生命周期
3. **✅ 事件线评分** - 可玩性/叙事/混合三种模式,动态权重调节
4. **✅ 线索经济** - 伏笔SLA、证据链验证、健康度监控
5. **✅ 一致性审计** - 硬规则/因果/资源/角色/时间线全方位检查
6. **✅ 会话历史** - 完整记录,支持分支,智能上下文

**系统已从"LLM包装器"进化为"智能叙事引擎"!** 🚀

下一步:整合为全局导演,实现完整的回合循环。
