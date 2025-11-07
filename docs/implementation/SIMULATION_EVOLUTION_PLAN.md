# 沉浸式叙事模拟器 - 演化迭代计划

**日期**: 2025-11-07
**目标**: 从"小说生成器"演化为"沉浸式叙事模拟器"
**核心指标**: Flow Index（流状态指数）、沉浸感、可玩性

---

## 📊 当前项目状态分析

### ✅ 已有基础（强项）

#### 1. 核心数据模型（src/models/）
- ✅ `WorldState`: 世界状态快照与补丁系统
- ✅ `Character`: 角色状态（属性、资源、关系）
- ✅ `EventNode` & `EventArc`: 事件系统
- ✅ `ActionQueue`: 动作队列
- ✅ `Clue`, `Evidence`, `Setup`: 线索经济基础

#### 2. 导演系统（src/director/）
- ✅ `GlobalDirector`: 场景循环主逻辑
- ✅ `EventScorer`: 可玩性/叙事评分
- ✅ `ConsistencyAuditor`: 一致性审计
- ✅ `ClueEconomyManager`: 线索/伏笔管理

#### 3. LLM 后端（web/backend/llm/）
- ✅ LangChain 1.0 + OpenRouter 集成
- ✅ 15 个游戏工具（@tool 装饰器）
- ✅ DM Agent（create_agent）
- ✅ 流式生成支持
- ✅ 多模型支持（DeepSeek/Claude/GPT-4/Qwen）

#### 4. Web 服务（web/backend/）
- ✅ FastAPI 后端（分层架构）
- ✅ Next.js 14 前端（shadcn/ui）
- ✅ WebSocket 实时生成
- ✅ 游戏引擎（GameEngine）
- ✅ 任务系统（QuestEngine）
- ✅ NPC 系统

#### 5. 数据库与持久化
- ✅ SQLite Schema（database/schema/）
- ✅ 游戏状态存档（game_state.log）
- ✅ LangGraph Checkpoint 支持（可选）
- ✅ 世界数据库（WorldDatabase）

### 🔍 当前架构与新规划的对接点

#### 对接良好（可直接扩展）
1. **EventNode** → **事件溯源（Event Sourcing）**
   - 现有: EventNode 有 prerequisites, effects, scoring
   - 需要: 添加 `seed`、`tick`、`actor`、`audit_flags`

2. **WorldState** → **Simulation State**
   - 现有: WorldState.apply_patch()
   - 需要: 时间戳、快照/回放机制

3. **GlobalDirector.run_scene_loop()** → **Simulation Loop**
   - 现有: 场景循环主逻辑
   - 需要: 接入 WorldClock 驱动

4. **GameTools** → **System Packs**
   - 现有: 15 个游戏工具
   - 需要: 重构为可插拔系统包（social/economy/geography/tech_magic）

#### 需要新建（核心缺失）
1. **WorldClock & Scheduler**
   - 时间推进与事件调度
   - 固定步长/可变步长支持

2. **Event Store**
   - 事件溯源（append-only）
   - 回放与分支管理

3. **AgentMind**
   - NPC 认知/记忆/动机
   - Utility AI/BDI 混合

4. **Flow Controller**
   - 动态难度调整
   - 情绪曲线管理

5. **Reader Model**
   - 读者偏好/耐心/期待管理

---

## 🎯 演化路线图

### Phase 1.5: 可回放的模拟循环内核（2 周）

**目标**: 建立"世界心跳"，支持确定性回放

#### 核心交付件

1. **src/sim/clock.py** - WorldClock
```python
class WorldClock:
    """世界时钟：驱动模拟循环"""
    def __init__(self, start=0, step=1):
        self.t = start  # 当前时间（tick）
        self.step = step

    def tick(self) -> int:
        """推进一个时间步"""
        self.t += self.step
        return self.t
```

2. **src/sim/scheduler.py** - Event Scheduler
```python
class Scheduler:
    """事件调度器：优先队列管理"""
    def schedule(self, when: int, task: Callable):
        """调度任务到指定时间"""

    def pop_due(self, now: int) -> List[Task]:
        """获取到期任务"""
```

3. **src/sim/event_store.py** - Event Sourcing
```python
class EventStore:
    """事件溯源：append-only 事件日志"""
    def append(self, event: Event):
        """追加事件（含 seed、tick、actor）"""

    def snapshot(self, world: WorldState) -> Snapshot:
        """创建世界快照"""

    def replay(self, to_tick: int) -> WorldState:
        """回放到指定时间点"""
```

4. **src/sim/simulation.py** - 顶层协调
```python
class Simulation:
    """模拟器：协调 Clock + Scheduler + EventStore + GlobalDirector"""
    def __init__(self, seed: int, setting: dict):
        self.clock = WorldClock()
        self.scheduler = Scheduler()
        self.event_store = EventStore()
        self.director = GlobalDirector(...)

    def run(self, max_ticks: int) -> ReplayHandle:
        """运行模拟"""
        for _ in range(max_ticks):
            tick = self.clock.tick()
            tasks = self.scheduler.pop_due(tick)
            # 执行 GlobalDirector.run_scene_loop()
            # 记录事件到 EventStore
```

#### 接口定义

```python
# 核心接口
Simulation.run(max_ticks: int) -> ReplayHandle
ReplayHandle.replay(to_tick: int) -> WorldState
ReplayHandle.snapshot() -> Snapshot
ReplayHandle.restore(snapshot: Snapshot)
```

#### 退出标准

- [x] 同一 seed 下，N 次运行生成完全一致的事件序列
- [x] 单一设定（科幻/玄幻）各运行 1000 Tick 无异常中断
- [x] 支持回放到任意时间点
- [x] 快照/恢复功能正常

#### 测试计划

```python
# tests/sim/test_determinism.py
def test_deterministic_replay():
    """测试确定性回放"""
    sim1 = Simulation(seed=42, setting=scifi_setting)
    sim2 = Simulation(seed=42, setting=scifi_setting)

    events1 = sim1.run(max_ticks=100)
    events2 = sim2.run(max_ticks=100)

    assert events1 == events2  # 完全一致

# tests/sim/test_snapshot.py
def test_snapshot_restore():
    """测试快照恢复"""
    sim = Simulation(seed=42, setting=scifi_setting)
    handle = sim.run(max_ticks=50)

    snapshot = handle.snapshot()
    handle.run_more(max_ticks=50)  # 继续运行

    handle.restore(snapshot)  # 恢复到 tick=50
    assert handle.clock.t == 50
```

---

### Phase 2: System Packs 基础（3 周）

**目标**: 重构游戏工具为可插拔系统包

#### 核心交付件

1. **src/sim/packs/social.py** - 社会系统
```python
class SocialPack(SystemPack):
    """社会关系/声望/派系目标"""
    def apply(self, world: WorldState, dt: float) -> List[Patch]:
        """应用社会系统规则"""
        # 关系衰减/声望变化/派系目标更新
```

2. **src/sim/packs/economy.py** - 经济系统
```python
class EconomyPack(SystemPack):
    """资源流动/生产-消耗-交易"""
    def apply(self, world: WorldState, dt: float) -> List[Patch]:
        """应用经济规则"""
        # 价格波动/稀缺性/市场供需
```

3. **src/sim/packs/geography.py** - 地理系统
```python
class GeographyPack(SystemPack):
    """地点/路径/可达性（NetworkX 图）"""
    def apply(self, world: WorldState, dt: float) -> List[Patch]:
        """应用地理规则"""
        # 路径查找/旅行时间/区域事件
```

4. **src/sim/packs/tech_magic.py** - 科技/修行系统
```python
class TechMagicPack(SystemPack):
    """科技树｜修行体系"""
    def apply(self, world: WorldState, dt: float) -> List[Patch]:
        """应用科技/修行规则"""
        # 能力解锁/代价/副作用/境界突破
```

#### 配置驱动（YAML）

```yaml
# config/system_packs.yaml
scifi:
  enabled_packs:
    - social
    - economy
    - geography
    - tech_magic

  tech_magic:
    mode: tech_tree
    energy_conservation: true
    ftl_limit: true

xianxia:
  enabled_packs:
    - social
    - economy
    - geography
    - tech_magic

  tech_magic:
    mode: cultivation
    realms: [炼气, 筑基, 金丹, 元婴, 化神]
    karma_enabled: true
```

#### 退出标准

- [x] 系统包可独立开关，不影响核心循环
- [x] 科幻/玄幻设定使用不同配置
- [x] 产出可解释且可度量（日志记录所有规则触发）

---

### Phase 3: AgentMind 认知系统（3 周）

**目标**: NPC 具备自主目标、记忆、决策能力

#### 核心交付件

1. **src/sim/agent/mind.py** - AgentMind
```python
class AgentMind:
    """Utility AI/BDI 混合认知系统"""
    def __init__(self, agent_id: str):
        self.beliefs = {}  # 信念
        self.desires = []  # 欲望
        self.intentions = []  # 意图

    def decide(self, goals: List[Goal], context: WorldState) -> Intent:
        """决策：根据目标和上下文选择行动"""
```

2. **src/sim/agent/memory.py** - 记忆系统
```python
class MemoryStore:
    """分层记忆：episodic/semantic/affective"""
    def remember(self, event: Event, salience: float):
        """存储记忆（带显著性权重）"""

    def recall(self, query: str, k: int = 5) -> List[Memory]:
        """检索相关记忆（向量检索/关键片段）"""
```

#### 退出标准

- [x] NPC 能在无指令下自发形成子目标
- [x] 示例：宗门弟子自发"夺宝/护道/泄密"
- [x] 记忆检索准确率 > 85%（人工评估）

---

### Phase 4: Flow Controller 与动态难度（2 周）

**目标**: 实时调节叙事节奏与难度，维持"流"状态

#### 核心交付件

1. **src/director/flow_controller.py** - Flow Controller
```python
class FlowController:
    """流状态控制器：动态调整 GD 权重"""
    def compute_flow(self, metrics: Metrics) -> float:
        """计算 Flow Index（0-1）"""
        # Flow = σ(α·Match + β·Tension + γ·Coherence + δ·Curiosity - ε·CogLoad)

    def adjust_weights(self, gd_params: dict, flow: float):
        """根据 Flow 调整权重"""
        if flow < 0.4:  # 低流状态
            # 降低信息密度、提升兑现率
        elif flow > 0.8:  # 高流状态
            # 插入悬念/支线
```

2. **src/director/reader_model.py** - 读者模型
```python
class ReaderModel:
    """读者偏好/能力/耐心管理"""
    def estimate_skill(self, history: List[Choice]) -> float:
        """估计读者能力（基于过往选择）"""

    def predict_patience(self) -> float:
        """预测读者耐心阈值"""
```

#### Flow Index 定义

```python
Flow = sigmoid(
    α * match(challenge, skill_hat)     # 难度-能力匹配
  + β * tension_slope                   # 张力斜率
  + γ * coherence                       # 一致性
  + δ * curiosity_gain                  # 未解问题增量
  - ε * cognitive_load                  # 认知负荷惩罚
)
```

#### 退出标准

- [x] Flow Index 可实时计算（< 50ms）
- [x] A/B 实验：Flow 控制组 vs 对照组，Revisit Rate 提升 > 15%

---

### Phase 5: UI/UX MVP（3 周）

**目标**: 实现沉浸式阅读界面（Reader App）

#### 核心交付件

**Reader App 必备页面**

1. **Run 页面（核心阅读）**
   - `SceneHeader`: 章名/地点/时间
   - `SceneBody`: 流式文本（骨架屏）
   - `ChoiceList`: 选项条（风险/信息标签）
   - `PayoffToast`: 伏笔兑现提示
   - `FlowIndicator`: Flow 进度条

2. **Journal 侧栏（编年史/线索）**
   - 编年史（时间线）
   - 线索列表（已证/待证）
   - 证据链（简化版）

3. **Branches 缩略图（分支树）**
   - 当前路径高亮
   - 支持软存档
   - 回放到分叉点

#### 组件库（shadcn/ui）

```typescript
// components/reader/SceneBody.tsx
export function SceneBody({ content, isStreaming }) {
  // 流式文本 + 骨架屏
}

// components/reader/ChoiceList.tsx
export function ChoiceList({ choices, onSelect }) {
  // 选项条（风险/信息徽标）
}

// components/reader/PayoffToast.tsx
export function PayoffToast({ clue, payoff }) {
  // 伏笔兑现提示（右下角）
}

// components/reader/FlowIndicator.tsx
export function FlowIndicator({ flow, tension, curiosity }) {
  // Flow 仪表盘（小型）
}
```

#### Design System

**双主题（科幻/玄幻）**

```css
/* 科幻主题 */
:root[data-theme="scifi"] {
  --bg-primary: #0a0e17;
  --text-primary: #e4e8f0;
  --accent: #00d9ff;
  --risk-high: #ff3366;
}

/* 玄幻主题 */
:root[data-theme="xianxia"] {
  --bg-primary: #f5f0e8;
  --text-primary: #2d2520;
  --accent: #c73e1d;
  --risk-high: #8b0000;
}
```

#### 性能指标

- [x] 首次进入 ≤ 2s 到可读文本
- [x] 选择后 ≤ 400ms 出首段流式文本
- [x] 侧栏操作不影响主文滚动位置
- [x] 键盘直选选项（1/2/3）100% 可用

---

### Phase 6: Telemetry & Metrics（2 周）

**目标**: 建立完整的度量体系

#### 核心指标

1. **Flow Metrics**
   - Flow Index（综合）
   - Tension Slope（张力斜率）
   - Curiosity Gain（未解问题增量）
   - Choice Entropy（选项分布熵）

2. **Engagement Metrics**
   - Payoff Latency（伏笔兑现延迟）
   - Revisit Rate（回看率）
   - Session Duration（会话时长）
   - Drop-off Points（流失点）

3. **System Metrics**
   - Coherence Score（一致性）
   - Audit Pass Rate（审计通过率）
   - LLM Cost per Session（成本）
   - Cache Hit Rate（缓存命中率）

#### Telemetry 事件

```typescript
// Reader 事件
trackEvent('scene_view', {
  scene_id, tick, words, reading_ms
});

trackEvent('choice_select', {
  choice_id, info_gain, risk_tag
});

trackEvent('clue_expand', {
  clue_id, credibility_before, credibility_after
});

// Studio 事件
trackEvent('weight_change', {
  playability, narrative
});

trackEvent('audit_apply_patch', {
  audit_id, patch_type
});
```

#### 仪表板

```
┌──────────── Flow Dashboard ────────────┐
│  Flow Index:      0.72 ████████░░      │
│  Tension Slope:   0.58 ██████░░░░      │
│  Curiosity Gain:  0.81 █████████░      │
│  Coherence:       0.94 ██████████      │
└────────────────────────────────────────┘

┌──────────── Engagement ────────────────┐
│  Avg Session:     32 min               │
│  Revisit Rate:    23%                  │
│  Payoff Latency:  4.2 scenes           │
└────────────────────────────────────────┘
```

---

## 📅 时间线总览

```
Phase 1.5 (2周): 模拟循环内核
  Week 1: WorldClock + Scheduler + EventStore
  Week 2: Simulation + 确定性测试

Phase 2 (3周): System Packs
  Week 3-4: Social + Economy
  Week 5: Geography + TechMagic

Phase 3 (3周): AgentMind
  Week 6-7: BDI + Memory
  Week 8: 自主目标测试

Phase 4 (2周): Flow Controller
  Week 9: Flow Index + ReaderModel
  Week 10: A/B 实验

Phase 5 (3周): UI/UX MVP
  Week 11: Run 页面 + ChoiceList
  Week 12: Journal + Branches
  Week 13: 主题 + 性能优化

Phase 6 (2周): Telemetry
  Week 14: 事件埋点 + 仪表板
  Week 15: 数据验证 + 迭代

总计: 15 周（约 4 个月）
```

---

## 🎯 第一周任务清单（Phase 1.5 Week 1）

### 任务 1: 建立 src/sim/ 目录结构

```bash
mkdir -p src/sim/{packs,agent}
touch src/sim/{__init__.py,clock.py,scheduler.py,event_store.py,simulation.py}
touch src/sim/packs/__init__.py
touch src/sim/agent/__init__.py
```

### 任务 2: 实现 WorldClock

```python
# src/sim/clock.py
class WorldClock:
    def __init__(self, start: int = 0, step: int = 1):
        self.t = start
        self.step = step

    def tick(self) -> int:
        self.t += self.step
        return self.t

    def reset(self, start: int = 0):
        self.t = start
```

### 任务 3: 实现 Scheduler

```python
# src/sim/scheduler.py
import heapq
from typing import Callable, List, Tuple

class Task:
    def __init__(self, when: int, fn: Callable):
        self.when = when
        self.fn = fn

    def __lt__(self, other):
        return self.when < other.when

class Scheduler:
    def __init__(self):
        self.queue: List[Task] = []

    def schedule(self, when: int, fn: Callable):
        heapq.heappush(self.queue, Task(when, fn))

    def pop_due(self, now: int) -> List[Task]:
        due = []
        while self.queue and self.queue[0].when <= now:
            due.append(heapq.heappop(self.queue))
        return due
```

### 任务 4: 实现 EventStore（基础版）

```python
# src/sim/event_store.py
from typing import List, Dict, Any
from dataclasses import dataclass
import json

@dataclass
class Event:
    tick: int
    actor: str
    action: str
    payload: Dict[str, Any]
    seed: str

class EventStore:
    def __init__(self):
        self.events: List[Event] = []

    def append(self, event: Event):
        self.events.append(event)

    def get_events(self, from_tick: int = 0, to_tick: int = None) -> List[Event]:
        if to_tick is None:
            return [e for e in self.events if e.tick >= from_tick]
        return [e for e in self.events if from_tick <= e.tick <= to_tick]

    def save_to_file(self, path: str):
        with open(path, 'w') as f:
            json.dump([e.__dict__ for e in self.events], f, indent=2)

    def load_from_file(self, path: str):
        with open(path, 'r') as f:
            data = json.load(f)
            self.events = [Event(**e) for e in data]
```

### 任务 5: 实现 Simulation（骨架）

```python
# src/sim/simulation.py
from .clock import WorldClock
from .scheduler import Scheduler
from .event_store import EventStore, Event

class Simulation:
    def __init__(self, seed: int, setting: dict):
        self.seed = seed
        self.setting = setting
        self.clock = WorldClock()
        self.scheduler = Scheduler()
        self.event_store = EventStore()

    def run(self, max_ticks: int):
        """运行模拟"""
        for _ in range(max_ticks):
            tick = self.clock.tick()
            tasks = self.scheduler.pop_due(tick)

            for task in tasks:
                # 执行任务（暂时只记录事件）
                event = Event(
                    tick=tick,
                    actor="system",
                    action="task_executed",
                    payload={"fn": str(task.fn)},
                    seed=f"{self.seed}/{tick}"
                )
                self.event_store.append(event)
                task.fn()

    def get_events(self):
        return self.event_store.events
```

### 任务 6: 编写基础测试

```python
# tests/sim/test_clock.py
from src.sim.clock import WorldClock

def test_clock_tick():
    clock = WorldClock(start=0, step=1)
    assert clock.tick() == 1
    assert clock.tick() == 2
    assert clock.t == 2

def test_clock_custom_step():
    clock = WorldClock(start=10, step=5)
    assert clock.tick() == 15
    assert clock.tick() == 20
```

```python
# tests/sim/test_scheduler.py
from src.sim.scheduler import Scheduler

def test_schedule_and_pop():
    scheduler = Scheduler()
    results = []

    scheduler.schedule(when=5, fn=lambda: results.append("task1"))
    scheduler.schedule(when=3, fn=lambda: results.append("task2"))
    scheduler.schedule(when=7, fn=lambda: results.append("task3"))

    # Pop at t=3
    due = scheduler.pop_due(3)
    assert len(due) == 1
    due[0].fn()
    assert results == ["task2"]

    # Pop at t=6
    due = scheduler.pop_due(6)
    assert len(due) == 1
    due[0].fn()
    assert results == ["task2", "task1"]
```

### 任务 7: 集成到 GlobalDirector（预演）

```python
# src/director/global_director.py (修改)
class GlobalDirector:
    def __init__(self, ..., clock: Optional[WorldClock] = None):
        # 现有代码...
        self.clock = clock  # 可选：接入时钟

    def run_scene_loop_with_clock(self, max_ticks: int):
        """时钟驱动的场景循环"""
        if not self.clock:
            raise ValueError("Clock not initialized")

        for _ in range(max_ticks):
            tick = self.clock.tick()
            # 执行原有的 run_scene_loop() 逻辑
            # 记录事件到 EventStore
```

---

## 🎯 验收标准（Phase 1.5）

### 功能验收

- [x] WorldClock 能正确推进时间
- [x] Scheduler 能按时间顺序调度任务
- [x] EventStore 能记录和回放事件
- [x] Simulation 能运行 1000+ ticks 无错误

### 确定性验收

```python
# tests/sim/test_determinism.py
def test_deterministic_simulation():
    """同一 seed 必须产生相同结果"""
    sim1 = Simulation(seed=42, setting={})
    sim2 = Simulation(seed=42, setting={})

    # 调度相同任务
    sim1.scheduler.schedule(5, lambda: print("task1"))
    sim2.scheduler.schedule(5, lambda: print("task1"))

    sim1.run(max_ticks=10)
    sim2.run(max_ticks=10)

    events1 = [e.__dict__ for e in sim1.get_events()]
    events2 = [e.__dict__ for e in sim2.get_events()]

    assert events1 == events2, "Determinism violated!"
```

---

## 📚 相关文档

- 技术规划: 本文档（SIMULATION_EVOLUTION_PLAN.md）
- UI/UX 规划: `docs/implementation/UI_UX_PLAN.md`（待创建）
- Flow 指标定义: `docs/reference/FLOW_METRICS.md`（待创建）
- System Packs 规范: `docs/reference/SYSTEM_PACKS_SPEC.md`（待创建）

---

## 💡 下一步行动

1. **创建目录结构** - `mkdir -p src/sim/{packs,agent}`
2. **实现 WorldClock** - 30 分钟
3. **实现 Scheduler** - 1 小时
4. **实现 EventStore** - 1.5 小时
5. **实现 Simulation** - 2 小时
6. **编写测试** - 2 小时
7. **集成测试** - 1 小时

**预计第一周完成时间**: 8-10 小时实际开发时间

---

**文档版本**: 1.0
**最后更新**: 2025-11-07
**负责人**: Claude + 用户协作
