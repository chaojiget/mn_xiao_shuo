# 节奏调控系统使用指南

## 概述

节奏调控系统允许你在创建世界时精确控制叙事节奏,从句法层面到场景层面,再到事件层面,全方位影响小说的生成风格。

## 核心概念

### 1. 节奏层次

节奏调控分为三个层次:

```
┌─────────────────────────────────────┐
│  全局节奏（Global Pace）             │
│  - slow/moderate/fast/varied        │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  句法节奏（Syntax Pacing）           │
│  - 句长、语态、段落节奏              │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  场景节奏（Scene Pacing）            │
│  - 描写占比、动作密度、对话频率      │
└───────────┬─────────────────────────┘
            │
┌───────────▼─────────────────────────┐
│  事件节奏（Event Pacing）            │
│  - 事件频率、冲突曲线、时间压缩      │
└─────────────────────────────────────┘
```

### 2. 节奏参数详解

#### 全局节奏 (global_pace)

- **slow**: 舒缓节奏,重视细节描写和氛围营造
- **moderate**: 适中节奏,描写和动作平衡
- **fast**: 紧凑节奏,聚焦关键事件和行动
- **varied**: 富有变化,张弛有度

#### 句法节奏

- **avg_sentence_len** (8-40): 平均句长（字数）
  - `< 15`: 短句,简洁有力
  - `15-25`: 中等句长,平衡
  - `> 25`: 长句,营造流畅感

- **sentence_len_variance** (0.0-1.0): 句长变化度
  - `0.0`: 句长统一
  - `0.3`: 适度变化
  - `1.0`: 极度多变

- **prefer_active_voice**: 优先使用主动语态
  - `true`: 动作感强
  - `false`: 文学性强

- **paragraph_rhythm**: 段落节奏
  - `staccato`: 短促有力,制造紧张感
  - `varied`: 长短结合,富有节奏变化
  - `flowing`: 流畅舒展,营造沉浸感
  - `mixed`: 根据场景灵活调整

#### 场景节奏

- **description_ratio** (0.1-0.8): 描写占比
  - `< 0.3`: 描写简洁,聚焦动作
  - `0.3-0.6`: 平衡
  - `> 0.6`: 描写丰富,营造画面感

- **action_density** (0.1-1.0): 动作密度
  - `< 0.3`: 舒缓,留出思考空间
  - `0.3-0.7`: 平衡
  - `> 0.7`: 密集,保持紧张感

- **dialogue_frequency** (0.0-0.7): 对话频率
  - `0.0`: 无对话
  - `0.3`: 适量对话
  - `0.7`: 对话密集

- **scene_transition_speed**: 场景切换速度
  - `gradual`: 渐进式切换
  - `moderate`: 适中
  - `abrupt`: 突然切换

#### 事件节奏

- **event_frequency** (0.1-1.0): 事件频率
  - `< 0.3`: 事件稀疏,注重日常
  - `0.3-0.7`: 平衡
  - `> 0.7`: 事件频繁,情节密集

- **conflict_intensity_curve**: 冲突强度曲线
  - `steady`: 冲突强度稳定
  - `escalating`: 冲突逐步升级
  - `wave`: 冲突呈波浪式起伏
  - `burst`: 冲突突发爆发

- **exposition_pace**: 信息揭示节奏
  - `upfront`: 前置揭示
  - `gradual`: 逐步揭示
  - `minimal`: 最小化

- **time_compression** (0.1-10.0): 时间压缩比
  - `< 1.0`: 时间浓缩（快进）
  - `1.0`: 实时
  - `> 1.0`: 时间拉长（慢镜头）

- **skip_mundane**: 跳过日常琐事
  - `true`: 聚焦关键情节
  - `false`: 保留日常细节

## 预设配置

系统提供 7 种预设节奏配置:

### 1. action (动作快节奏)

**适用场景**: 动作冒险、战斗、追逐

**特点**:
- 短句密集（平均 12 字）
- 动作紧凑（密度 0.9）
- 描写简洁（占比 0.2）
- 时间浓缩（压缩比 0.3）

**示例**:
```json
{
  "global_pace": "fast",
  "avg_sentence_len": 12,
  "action_density": 0.9,
  "description_ratio": 0.2
}
```

### 2. literary (文学慢节奏)

**适用场景**: 文艺小说、心理描写、氛围营造

**特点**:
- 长句流畅（平均 28 字）
- 描写细腻（占比 0.7）
- 动作舒缓（密度 0.2）
- 时间拉长（压缩比 3.0）

### 3. epic (史诗节奏)

**适用场景**: 仙侠、奇幻史诗、大场景

**特点**:
- 变化丰富
- 场景宏大
- 冲突逐步升级
- 时间适度拉长（压缩比 1.5）

### 4. horror (恐怖悬疑)

**适用场景**: 恐怖、悬疑、惊悚

**特点**:
- 节奏舒缓但紧张
- 气氛压抑
- 冲突呈波浪式
- 保留日常细节营造反差

### 5. detective (推理节奏)

**适用场景**: 侦探、推理、解谜

**特点**:
- 节奏平稳
- 逻辑清晰
- 对话丰富（频率 0.5）
- 不跳过日常细节

### 6. slice_of_life (日常节奏)

**适用场景**: 日常、校园、温馨

**特点**:
- 舒缓温馨
- 对话丰富（频率 0.6）
- 事件稀疏（频率 0.3）
- 保留日常琐事

### 7. balanced (平衡节奏，默认)

**适用场景**: 通用场景、混合类型

**特点**:
- 各项均衡
- 通用性强
- 适合大多数场景

## 使用方法

### 方法 1: 使用预设配置 (推荐)

#### API 调用

```bash
# 1. 列出所有预设
curl http://localhost:8000/api/worlds/pacing/presets

# 2. 获取特定预设
curl http://localhost:8000/api/worlds/pacing/presets/action

# 3. 使用预设创建世界
curl -X POST http://localhost:8000/api/worlds/generate \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "novel-001",
    "seed": "dark survival",
    "pacing_preset": "action"
  }'
```

#### Python 代码

```python
from services.pacing_presets import PacingPresets
from models.world_models import WorldGenerationRequest

# 获取预设
pacing = PacingPresets.get_preset("action")

# 创建请求
request = WorldGenerationRequest(
    novel_id="novel-001",
    theme="dark survival",
    tone="冷冽压抑",
    novel_type="xianxia",
    pacing_config=pacing
)
```

### 方法 2: 自定义配置

```python
from models.world_models import PacingControl, WorldGenerationRequest

# 自定义节奏配置
custom_pacing = PacingControl(
    global_pace="fast",
    avg_sentence_len=15,
    sentence_len_variance=0.4,
    prefer_active_voice=True,
    paragraph_rhythm="staccato",
    description_ratio=0.3,
    action_density=0.8,
    dialogue_frequency=0.2,
    scene_transition_speed="abrupt",
    event_frequency=0.7,
    conflict_intensity_curve="escalating",
    exposition_pace="minimal",
    time_compression=0.5,
    skip_mundane=True
)

# 创建请求
request = WorldGenerationRequest(
    novel_id="novel-001",
    theme="dark survival",
    tone="冷冽压抑",
    novel_type="xianxia",
    pacing_config=custom_pacing
)
```

### 方法 3: 修改预设配置

```python
from services.pacing_presets import PacingPresets

# 基于预设修改
pacing = PacingPresets.get_preset("action")
pacing.avg_sentence_len = 10  # 更短的句子
pacing.dialogue_frequency = 0.3  # 增加对话

request = WorldGenerationRequest(
    novel_id="novel-001",
    theme="dark survival",
    tone="冷冽压抑",
    novel_type="xianxia",
    pacing_config=pacing
)
```

## 节奏配置的效果

### 示例对比

#### 快节奏 (action)

```
门破了。
他冲进去。枪声响起。
躲！翻滚。起身。射击。
敌人倒下。
```

**特点**: 短句、动作密集、几乎无描写

#### 慢节奏 (literary)

```
木门在夜风中发出低沉的呻吟,仿佛预示着某种不祥的命运。
他缓缓推开门,锈蚀的铰链发出刺耳的尖叫,划破了死寂的夜空。
空气中弥漫着陈腐的霉味和铁锈的腥甜,那是岁月在这个被遗忘的角落留下的痕迹。
```

**特点**: 长句、描写丰富、氛围浓厚

#### 平衡节奏 (balanced)

```
门已经破损,铰链锈迹斑斑。
他推开门,木门发出刺耳的声音。房间里一片漆黑,只有微弱的月光透过破窗照进来。
他警惕地四处张望,手按在腰间的枪柄上。
```

**特点**: 中等句长、描写与动作平衡

## 节奏与类型的匹配建议

| 小说类型 | 推荐预设 | 备选预设 |
|---------|---------|---------|
| 玄幻仙侠 | epic | action (战斗), literary (修炼) |
| 科幻冒险 | action | epic (宇宙级), balanced |
| 恐怖惊悚 | horror | literary (心理) |
| 侦探推理 | detective | literary (深度) |
| 都市言情 | slice_of_life | literary |
| 历史战争 | epic | action (战斗) |
| 游戏竞技 | action | balanced |

## 高级用法

### 1. 动态调整节奏

在不同章节使用不同节奏:

```python
# 第1-5章：世界观介绍，使用慢节奏
pacing_intro = PacingPresets.get_preset("literary")

# 第6-10章：冲突升级，使用快节奏
pacing_conflict = PacingPresets.get_preset("action")

# 第11-15章：高潮，使用史诗节奏
pacing_climax = PacingPresets.get_preset("epic")
```

### 2. 混合配置

结合多个预设的优点:

```python
# 基础使用 epic
pacing = PacingPresets.get_preset("epic")

# 但战斗场景要更快
pacing.action_density = 0.9  # 提高到 action 级别
pacing.time_compression = 0.3  # 时间浓缩
```

### 3. 场景特定调整

```python
# 战斗场景
def get_combat_pacing():
    pacing = PacingPresets.get_preset("action")
    pacing.dialogue_frequency = 0.1  # 战斗时少说话
    return pacing

# 感情戏
def get_romance_pacing():
    pacing = PacingPresets.get_preset("literary")
    pacing.dialogue_frequency = 0.6  # 多对话
    return pacing

# 悬疑推理
def get_mystery_pacing():
    pacing = PacingPresets.get_preset("detective")
    pacing.exposition_pace = "gradual"  # 逐步揭示
    return pacing
```

## 最佳实践

### 1. 选择预设的建议

- **新手**: 使用 `balanced` 预设,稳妥可靠
- **明确类型**: 选择对应类型的预设（如仙侠用 `epic`）
- **实验性**: 尝试不同预设,找到最适合的风格

### 2. 调整参数的建议

- **微调**: 基于预设微调 1-2 个参数,不要大改
- **测试**: 生成样本章节,观察效果再决定
- **一致性**: 同一部小说保持节奏配置的一致性

### 3. 避免的陷阱

- ❌ 节奏过快导致读者疲劳
- ❌ 节奏过慢导致拖沓
- ❌ 频繁切换节奏导致混乱
- ❌ 所有参数都调到极值

### 4. 推荐组合

**快节奏小说**:
```python
pacing = PacingControl(
    global_pace="fast",
    avg_sentence_len=12-15,
    action_density=0.8-0.9,
    event_frequency=0.7-0.9,
    time_compression=0.3-0.5
)
```

**慢节奏小说**:
```python
pacing = PacingControl(
    global_pace="slow",
    avg_sentence_len=25-30,
    description_ratio=0.6-0.7,
    action_density=0.2-0.3,
    time_compression=2.0-3.0
)
```

## 故障排查

### 问题1: 生成内容节奏不符合预期

**可能原因**:
- LLM 没有正确理解节奏提示
- 节奏配置与主题/基调冲突

**解决方法**:
1. 检查 `world_generator.py` 中的 `_get_pacing_hints()` 输出
2. 确保节奏配置与小说类型匹配
3. 尝试调整 temperature 参数

### 问题2: 节奏过于单一

**解决方法**:
- 提高 `sentence_len_variance`
- 使用 `paragraph_rhythm="varied"` 或 `"mixed"`
- 使用 `conflict_intensity_curve="wave"`

### 问题3: 动作场景仍然拖沓

**解决方法**:
```python
pacing.action_density = 0.9
pacing.description_ratio = 0.2
pacing.avg_sentence_len = 10
pacing.time_compression = 0.3
```

## API 参考

### GET /api/worlds/pacing/presets

列出所有预设配置

**响应**:
```json
{
  "action": {
    "name": "动作快节奏",
    "description": "短句密集、动作紧凑",
    "tags": ["快节奏", "动作", "紧张"]
  },
  ...
}
```

### GET /api/worlds/pacing/presets/{preset_name}

获取特定预设的详细配置

**参数**:
- `preset_name`: 预设名称

**响应**:
```json
{
  "global_pace": "fast",
  "avg_sentence_len": 12,
  "sentence_len_variance": 0.5,
  ...
}
```

## 相关文档

- `models/world_models.py`: PacingControl 数据模型定义
- `services/pacing_presets.py`: 预设配置实现
- `services/world_generator.py`: 节奏配置应用逻辑
- `docs/features/WORLD_SCAFFOLD_GUIDE.md`: 世界脚手架系统
