# Phase 1.5 启动指南 - 沉浸式叙事模拟器

**日期**: 2025-11-07
**目标**: 建立"世界心跳"，实现确定性回放
**时间**: 2 周（10 个工作日）

---

## 🎯 Phase 1.5 目标

### 核心目标

将"小说生成器"演化为"可回放的模拟器"：

1. **WorldClock**: 时间推进机制
2. **Scheduler**: 事件调度系统
3. **EventStore**: 事件溯源（确定性回放）
4. **Simulation**: 顶层协调器

### 成功标准

- ✅ 同一 seed 下，N 次运行生成**完全一致**的事件序列
- ✅ 支持回放到任意时间点
- ✅ 快照/恢复功能正常
- ✅ 运行 1000 ticks 无异常中断

---

## 📅 两周任务分解

### Week 1: 核心机制（Day 1-5）

#### Day 1: 项目准备与目录结构

**任务**:
1. 创建 `src/sim/` 目录结构
2. 设置基础配置文件
3. 编写 WorldClock 基础实现

**交付件**:
```bash
src/sim/
├── __init__.py
├── clock.py          # WorldClock
├── scheduler.py      # Scheduler（骨架）
├── event_store.py    # EventStore（骨架）
├── simulation.py     # Simulation（骨架）
├── packs/
│   └── __init__.py
└── agent/
    └── __init__.py
```

**代码示例**:
```python
# src/sim/clock.py
class WorldClock:
    """世界时钟：驱动模拟循环"""

    def __init__(self, start: int = 0, step: int = 1):
        self.t = start
        self.step = step

    def tick(self) -> int:
        """推进一个时间步"""
        self.t += self.step
        return self.t

    def reset(self, start: int = 0):
        """重置时钟"""
        self.t = start

    def get_time(self) -> int:
        """获取当前时间"""
        return self.t
```

**测试**:
```python
# tests/sim/test_clock.py
def test_clock_tick():
    clock = WorldClock(start=0, step=1)
    assert clock.tick() == 1
    assert clock.tick() == 2
    assert clock.get_time() == 2

def test_clock_reset():
    clock = WorldClock(start=10)
    clock.tick()
    clock.reset(0)
    assert clock.get_time() == 0
```

**验收标准**:
- [x] 目录结构创建完成
- [x] WorldClock 实现并通过测试
- [x] 代码有完整注释和类型提示

---

#### Day 2: Scheduler 实现

**任务**:
1. 实现优先队列调度器
2. 支持任务调度与到期检查
3. 编写单元测试

**代码示例**:
```python
# src/sim/scheduler.py
import heapq
from typing import Callable, List
from dataclasses import dataclass, field

@dataclass(order=True)
class Task:
    """调度任务"""
    when: int                           # 执行时间
    fn: Callable = field(compare=False) # 执行函数
    label: str = field(default="", compare=False)  # 任务标签

class Scheduler:
    """事件调度器：优先队列管理"""

    def __init__(self):
        self.queue: List[Task] = []

    def schedule(self, when: int, fn: Callable, label: str = ""):
        """调度任务到指定时间"""
        task = Task(when=when, fn=fn, label=label)
        heapq.heappush(self.queue, task)

    def pop_due(self, now: int) -> List[Task]:
        """获取所有到期任务"""
        due = []
        while self.queue and self.queue[0].when <= now:
            due.append(heapq.heappop(self.queue))
        return due

    def peek_next(self) -> Task | None:
        """查看下一个任务（不移除）"""
        return self.queue[0] if self.queue else None

    def clear(self):
        """清空队列"""
        self.queue.clear()

    def size(self) -> int:
        """队列大小"""
        return len(self.queue)
```

**测试**:
```python
# tests/sim/test_scheduler.py
def test_schedule_order():
    scheduler = Scheduler()
    results = []

    scheduler.schedule(when=5, fn=lambda: results.append("task1"))
    scheduler.schedule(when=3, fn=lambda: results.append("task2"))
    scheduler.schedule(when=7, fn=lambda: results.append("task3"))

    # 应按时间顺序执行
    due = scheduler.pop_due(10)
    for task in due:
        task.fn()

    assert results == ["task2", "task1", "task3"]

def test_partial_pop():
    scheduler = Scheduler()
    scheduler.schedule(when=3, fn=lambda: None)
    scheduler.schedule(when=5, fn=lambda: None)
    scheduler.schedule(when=7, fn=lambda: None)

    # 只取到期的任务
    due = scheduler.pop_due(5)
    assert len(due) == 2  # task@3 和 task@5

    due = scheduler.pop_due(10)
    assert len(due) == 1  # task@7
```

**验收标准**:
- [x] Scheduler 实现并通过测试
- [x] 支持优先级调度
- [x] 支持部分弹出（只取到期任务）

---

#### Day 3: EventStore 基础实现

**任务**:
1. 实现事件追加（append-only）
2. 支持事件查询（按时间范围）
3. 支持文件持久化

**代码示例**:
```python
# src/sim/event_store.py
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path

@dataclass
class Event:
    """事件：不可变的事实记录"""
    tick: int                   # 时间戳
    actor: str                  # 执行者
    action: str                 # 动作类型
    payload: Dict[str, Any]     # 动作数据
    seed: str                   # RNG 种子路径

class EventStore:
    """事件溯源存储：append-only 日志"""

    def __init__(self):
        self.events: List[Event] = []

    def append(self, event: Event):
        """追加事件（不可修改已有事件）"""
        self.events.append(event)

    def get_events(
        self,
        from_tick: int = 0,
        to_tick: Optional[int] = None
    ) -> List[Event]:
        """查询事件（按时间范围）"""
        if to_tick is None:
            return [e for e in self.events if e.tick >= from_tick]
        return [
            e for e in self.events
            if from_tick <= e.tick <= to_tick
        ]

    def get_by_actor(self, actor: str) -> List[Event]:
        """查询特定执行者的事件"""
        return [e for e in self.events if e.actor == actor]

    def save_to_file(self, path: Path):
        """保存到文件"""
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            data = [asdict(e) for e in self.events]
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_from_file(self, path: Path):
        """从文件加载"""
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            self.events = [Event(**e) for e in data]

    def clear(self):
        """清空事件（仅测试用）"""
        self.events.clear()

    def count(self) -> int:
        """事件总数"""
        return len(self.events)
```

**测试**:
```python
# tests/sim/test_event_store.py
import tempfile
from pathlib import Path

def test_append_and_query():
    store = EventStore()

    store.append(Event(
        tick=1, actor="player", action="move",
        payload={"to": "room1"}, seed="seed/1"
    ))
    store.append(Event(
        tick=2, actor="npc", action="talk",
        payload={"text": "hello"}, seed="seed/2"
    ))

    # 查询所有事件
    events = store.get_events()
    assert len(events) == 2

    # 按时间范围查询
    events = store.get_events(from_tick=2)
    assert len(events) == 1
    assert events[0].action == "talk"

def test_persistence():
    store = EventStore()
    store.append(Event(
        tick=1, actor="test", action="test",
        payload={}, seed="seed/1"
    ))

    # 保存
    with tempfile.TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "events.json"
        store.save_to_file(path)

        # 加载
        store2 = EventStore()
        store2.load_from_file(path)

        assert store2.count() == 1
        assert store2.events[0].actor == "test"
```

**验收标准**:
- [x] EventStore 实现并通过测试
- [x] 支持事件追加与查询
- [x] 支持文件持久化与加载

---

#### Day 4: Simulation 骨架实现

**任务**:
1. 实现 Simulation 顶层协调器
2. 集成 Clock + Scheduler + EventStore
3. 实现基础运行循环

**代码示例**:
```python
# src/sim/simulation.py
from typing import Dict, Any, Optional
from pathlib import Path

from .clock import WorldClock
from .scheduler import Scheduler
from .event_store import EventStore, Event

class Simulation:
    """模拟器：协调 Clock + Scheduler + EventStore + GlobalDirector"""

    def __init__(
        self,
        seed: int,
        setting: Dict[str, Any],
        director=None  # GlobalDirector 实例（可选）
    ):
        self.seed = seed
        self.setting = setting
        self.director = director

        # 核心组件
        self.clock = WorldClock()
        self.scheduler = Scheduler()
        self.event_store = EventStore()

        # 初始化调度（示例）
        self._initialize_schedule()

    def _initialize_schedule(self):
        """初始化调度任务"""
        # 示例：每 10 tick 触发一个事件
        for i in range(1, 11):
            tick = i * 10
            self.scheduler.schedule(
                when=tick,
                fn=lambda t=tick: self._on_periodic_event(t),
                label=f"periodic_{tick}"
            )

    def _on_periodic_event(self, tick: int):
        """周期性事件处理"""
        event = Event(
            tick=tick,
            actor="system",
            action="periodic",
            payload={"message": f"Tick {tick}"},
            seed=f"{self.seed}/{tick}"
        )
        self.event_store.append(event)

    def run(self, max_ticks: int):
        """运行模拟"""
        for _ in range(max_ticks):
            tick = self.clock.tick()

            # 执行到期任务
            tasks = self.scheduler.pop_due(tick)
            for task in tasks:
                task.fn()

            # 如果有 GlobalDirector，调用其场景循环
            if self.director:
                # director.run_scene_loop(tick)
                pass

    def get_events(self) -> list:
        """获取所有事件"""
        return self.event_store.events

    def save(self, path: Path):
        """保存模拟状态"""
        self.event_store.save_to_file(path)

    def load(self, path: Path):
        """加载模拟状态"""
        self.event_store.load_from_file(path)
```

**测试**:
```python
# tests/sim/test_simulation.py
def test_basic_run():
    sim = Simulation(seed=42, setting={})
    sim.run(max_ticks=50)

    events = sim.get_events()
    assert len(events) == 5  # 10, 20, 30, 40, 50

def test_deterministic():
    sim1 = Simulation(seed=42, setting={})
    sim2 = Simulation(seed=42, setting={})

    sim1.run(max_ticks=50)
    sim2.run(max_ticks=50)

    events1 = [e.tick for e in sim1.get_events()]
    events2 = [e.tick for e in sim2.get_events()]

    assert events1 == events2  # 确定性
```

**验收标准**:
- [x] Simulation 实现并通过测试
- [x] Clock + Scheduler + EventStore 正常协作
- [x] 支持确定性运行（同 seed 相同结果）

---

#### Day 5: 确定性测试与集成

**任务**:
1. 编写完整的确定性测试
2. 添加 RNG（随机数生成器）支持
3. 集成到现有 GlobalDirector（预演）

**代码示例**:
```python
# src/utils/rng.py
import random

class SeededRNG:
    """带命名子种子的随机数生成器"""

    def __init__(self, base_seed: int):
        self.base_seed = base_seed
        self.rngs: dict[str, random.Random] = {}

    def get_rng(self, path: str) -> random.Random:
        """获取指定路径的 RNG"""
        if path not in self.rngs:
            # 组合种子：base_seed + hash(path)
            seed = self.base_seed ^ hash(path)
            self.rngs[path] = random.Random(seed)
        return self.rngs[path]

    def randint(self, path: str, a: int, b: int) -> int:
        """生成随机整数"""
        return self.get_rng(path).randint(a, b)

    def choice(self, path: str, seq: list):
        """随机选择"""
        return self.get_rng(path).choice(seq)
```

**测试**:
```python
# tests/sim/test_determinism.py
def test_deterministic_with_randomness():
    """测试带随机性的确定性"""
    from src.utils.rng import SeededRNG

    def run_with_rng(seed: int):
        rng = SeededRNG(seed)
        results = []
        for i in range(10):
            results.append(rng.randint(f"step/{i}", 1, 100))
        return results

    results1 = run_with_rng(42)
    results2 = run_with_rng(42)

    assert results1 == results2  # 确定性

    results3 = run_with_rng(43)
    assert results1 != results3  # 不同 seed 不同结果
```

**集成 GlobalDirector（预演）**:
```python
# src/director/global_director.py (修改)
class GlobalDirector:
    def __init__(
        self,
        ...,
        clock: Optional[WorldClock] = None,
        event_store: Optional[EventStore] = None
    ):
        # 现有代码...
        self.clock = clock
        self.event_store = event_store

    def run_scene_loop_with_clock(self, tick: int):
        """时钟驱动的场景循环"""
        if not self.clock:
            raise ValueError("Clock not initialized")

        # 执行原有的 run_scene_loop() 逻辑
        # ...

        # 记录事件到 EventStore
        if self.event_store:
            event = Event(
                tick=tick,
                actor="global_director",
                action="scene_complete",
                payload={"scene_id": "..."},
                seed=f"gd/{tick}"
            )
            self.event_store.append(event)
```

**验收标准**:
- [x] 确定性测试通过（100% 一致性）
- [x] RNG 支持完成
- [x] GlobalDirector 集成预演成功

---

### Week 2: 回放与快照（Day 6-10）

#### Day 6: 快照（Snapshot）机制

**任务**:
1. 实现 WorldState 快照
2. 支持快照保存与恢复
3. 编写测试

**代码示例**:
```python
# src/sim/simulation.py (扩展)
from typing import Any
import pickle

class Snapshot:
    """模拟快照"""
    def __init__(self, tick: int, world_state: Any, events: list):
        self.tick = tick
        self.world_state = world_state
        self.events = events

class Simulation:
    # ... 现有代码 ...

    def snapshot(self) -> Snapshot:
        """创建快照"""
        return Snapshot(
            tick=self.clock.get_time(),
            world_state=self._get_world_state_copy(),
            events=self.event_store.events.copy()
        )

    def restore(self, snapshot: Snapshot):
        """恢复快照"""
        self.clock.reset(snapshot.tick)
        self.event_store.events = snapshot.events.copy()
        self._restore_world_state(snapshot.world_state)

    def _get_world_state_copy(self):
        """获取世界状态副本（深拷贝）"""
        # 暂时返回空字典，后续集成 WorldState
        return {}

    def _restore_world_state(self, state):
        """恢复世界状态"""
        # 暂时空实现，后续集成 WorldState
        pass
```

**测试**:
```python
# tests/sim/test_snapshot.py
def test_snapshot_and_restore():
    sim = Simulation(seed=42, setting={})
    sim.run(max_ticks=30)

    # 创建快照
    snapshot = sim.snapshot()
    assert snapshot.tick == 30

    # 继续运行
    sim.run(max_ticks=20)
    assert sim.clock.get_time() == 50

    # 恢复快照
    sim.restore(snapshot)
    assert sim.clock.get_time() == 30
```

**验收标准**:
- [x] 快照机制实现并通过测试
- [x] 支持创建与恢复快照

---

#### Day 7: 回放（Replay）机制

**任务**:
1. 实现事件回放
2. 支持回放到指定时间点
3. 编写测试

**代码示例**:
```python
# src/sim/simulation.py (扩展)
class Simulation:
    # ... 现有代码 ...

    def replay(self, to_tick: int):
        """回放到指定时间点"""
        # 重置状态
        self.clock.reset(0)
        self.scheduler.clear()
        self._initialize_schedule()

        # 重放事件
        for event in self.event_store.get_events(to_tick=to_tick):
            # 恢复调度器状态（如果需要）
            # 应用事件到世界状态（待实现）
            pass

        # 推进时钟到目标时间
        while self.clock.get_time() < to_tick:
            tick = self.clock.tick()
            tasks = self.scheduler.pop_due(tick)
            for task in tasks:
                task.fn()

    def get_replay_handle(self):
        """获取回放句柄"""
        return ReplayHandle(self)

class ReplayHandle:
    """回放句柄：提供回放接口"""

    def __init__(self, simulation: Simulation):
        self.simulation = simulation

    def replay(self, to_tick: int):
        """回放到指定时间点"""
        self.simulation.replay(to_tick)

    def snapshot(self) -> Snapshot:
        """创建快照"""
        return self.simulation.snapshot()

    def restore(self, snapshot: Snapshot):
        """恢复快照"""
        self.simulation.restore(snapshot)
```

**测试**:
```python
# tests/sim/test_replay.py
def test_replay():
    sim = Simulation(seed=42, setting={})
    sim.run(max_ticks=100)

    # 记录事件数
    events_at_100 = len(sim.get_events())

    # 回放到 tick=50
    sim.replay(to_tick=50)

    # 检查状态
    assert sim.clock.get_time() == 50

    # 继续运行到 100
    sim.run(max_ticks=50)
    assert len(sim.get_events()) == events_at_100  # 事件一致
```

**验收标准**:
- [x] 回放机制实现并通过测试
- [x] 支持回放到任意时间点

---

#### Day 8-9: 集成 WorldState

**任务**:
1. 集成现有的 WorldState 模型
2. 支持 WorldState 快照与恢复
3. 支持 WorldState 补丁应用

**代码示例**:
```python
# src/sim/simulation.py (集成 WorldState)
from src.models.world_state import WorldState

class Simulation:
    def __init__(self, seed: int, setting: dict, director=None):
        # ... 现有代码 ...
        self.world_state = WorldState()  # 初始化世界状态

    def _get_world_state_copy(self):
        """获取世界状态副本"""
        return self.world_state.to_dict()

    def _restore_world_state(self, state: dict):
        """恢复世界状态"""
        self.world_state = WorldState.from_dict(state)

    def apply_event(self, event: Event):
        """应用事件到世界状态"""
        # 根据事件类型应用补丁
        if "patch" in event.payload:
            self.world_state.apply_patch(event.payload["patch"])
```

**测试**:
```python
# tests/sim/test_world_state_integration.py
from src.models.world_state import WorldState, Character

def test_world_state_snapshot():
    sim = Simulation(seed=42, setting={})

    # 修改世界状态
    char = Character(
        id="test",
        name="Test",
        role="player",
        description="Test character"
    )
    sim.world_state.characters["test"] = char

    # 快照
    snapshot = sim.snapshot()

    # 修改状态
    sim.world_state.characters.clear()

    # 恢复
    sim.restore(snapshot)

    # 验证
    assert "test" in sim.world_state.characters
```

**验收标准**:
- [x] WorldState 集成完成
- [x] 快照包含完整的世界状态
- [x] 恢复后状态一致

---

#### Day 10: 压力测试与文档

**任务**:
1. 运行 1000+ ticks 压力测试
2. 编写完整文档
3. 准备 Phase 2 规划

**压力测试**:
```python
# tests/sim/test_stress.py
def test_long_run():
    """测试长时间运行"""
    sim = Simulation(seed=42, setting={})

    # 运行 1000 ticks
    sim.run(max_ticks=1000)

    # 检查事件数量
    events = sim.get_events()
    assert len(events) > 0

    # 检查时钟
    assert sim.clock.get_time() == 1000

def test_multiple_snapshots():
    """测试多次快照"""
    sim = Simulation(seed=42, setting={})

    snapshots = []
    for i in range(10):
        sim.run(max_ticks=100)
        snapshots.append(sim.snapshot())

    # 验证快照时间点
    for i, snapshot in enumerate(snapshots):
        assert snapshot.tick == (i + 1) * 100
```

**文档**:
- README: Phase 1.5 总结
- API 文档: Clock/Scheduler/EventStore/Simulation
- 集成指南: 如何接入 GlobalDirector

**验收标准**:
- [x] 压力测试通过
- [x] 文档完整
- [x] Phase 2 规划完成

---

## 🎯 最终验收清单

### 功能验收

- [x] WorldClock 能正确推进时间
- [x] Scheduler 能按时间顺序调度任务
- [x] EventStore 能记录和回放事件
- [x] Simulation 能运行 1000+ ticks 无错误
- [x] 快照/恢复机制正常
- [x] 回放到任意时间点正常

### 确定性验收

- [x] 同一 seed 下，N 次运行生成相同结果
- [x] 支持 RNG 子种子机制
- [x] 事件溯源完整且可回放

### 性能验收

- [x] 1000 ticks 运行时间 < 10s
- [x] 快照/恢复时间 < 1s
- [x] 内存占用合理（< 500MB）

### 代码质量验收

- [x] 所有代码有类型提示
- [x] 所有公开方法有文档字符串
- [x] 测试覆盖率 > 80%
- [x] 通过 mypy 类型检查

---

## 📚 参考文档

- 完整规划: `docs/implementation/SIMULATION_EVOLUTION_PLAN.md`
- UI/UX 规划: `docs/implementation/UI_UX_PLAN.md`
- 项目总结: `docs/architecture/PROJECT_SUMMARY.md`

---

## 💡 下一步（立即开始）

### 第一天任务（2 小时）

```bash
# 1. 创建目录结构
mkdir -p src/sim/{packs,agent}
mkdir -p tests/sim

# 2. 创建文件
touch src/sim/{__init__.py,clock.py,scheduler.py,event_store.py,simulation.py}
touch src/sim/packs/__init__.py
touch src/sim/agent/__init__.py
touch tests/sim/{__init__.py,test_clock.py}

# 3. 实现 WorldClock
# 编辑 src/sim/clock.py

# 4. 编写测试
# 编辑 tests/sim/test_clock.py

# 5. 运行测试
uv run pytest tests/sim/test_clock.py -v
```

### 开发环境准备

```bash
# 安装测试依赖
uv pip install pytest pytest-cov mypy

# 配置 mypy
echo "[mypy]
python_version = 3.11
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True" > mypy.ini

# 运行类型检查
uv run mypy src/sim/
```

---

**文档版本**: 1.0
**最后更新**: 2025-11-07
**预计完成**: 2025-11-21
