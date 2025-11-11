# 风格系统总览

## 🎯 概述

风格系统由**节奏调控**和**文风选择**两部分组成，让你全方位控制小说的生成风格。

## 🎨 双系统架构

```
┌─────────────────────────────────────────┐
│         风格系统 (Style System)          │
├─────────────────┬───────────────────────┤
│  节奏调控 ⚡     │    文风选择 ✍️         │
│  (Pacing)       │    (Writing Style)    │
├─────────────────┼───────────────────────┤
│ 控制"说多快"    │    控制"怎么说"       │
│                 │                       │
│ • 句长          │    • 用词             │
│ • 动作密度      │    • 句式             │
│ • 描写占比      │    • 修辞             │
│ • 事件频率      │    • 视角             │
│ • 时间压缩      │    • 描写风格         │
└─────────────────┴───────────────────────┘
```

## 📊 快速对比

| 维度 | 节奏调控 ⚡ | 文风选择 ✍️ |
|-----|-----------|------------|
| **控制内容** | 快慢、密度 | 风格、韵味 |
| **预设数量** | 7 个 | 9 个 |
| **主要参数** | 句长、动作密度、事件频率 | 用词、句式、修辞 |
| **影响范围** | 叙事节奏 | 语言风格 |
| **使用时机** | 控制紧张感、阅读速度 | 确定文学风格 |

## 🎯 推荐组合

### 玄幻仙侠小说

**推荐**: 史诗节奏 + 网文爽文
```
pacing: epic
writing_style: web_novel_cool
```

**效果**: 变化丰富、气势磅礴、四字成语多、装逼打脸

**示例**:
```
他缓缓抬头，剑指苍穹。
"区区金丹，也敢在本座面前造次？"
剑气纵横三万里，一剑破万法！
天地失色，群山震颤。
```

### 都市温馨小说

**推荐**: 日常节奏 + 网文温情
```
pacing: slice_of_life
writing_style: web_novel_warm
```

**效果**: 温馨舒缓、对话丰富、第一人称、接地气

**示例**:
```
我推开咖啡厅的门，一股咖啡香扑面而来。
"来了啊。"她朝我笑了笑，眼睛弯成月牙。
窗外阳光正好，洒在她的发梢上。
我心里一暖，这就是平凡生活中的小确幸吧。
```

### 末世黑暗小说

**推荐**: 动作快节奏 + 网文黑暗
```
pacing: action
writing_style: web_novel_dark
```

**效果**: 紧张刺激、画面感强、压抑残酷

**示例**:
```
枪声响起。他翻滚。
血肉横飞。变异体倒下。
又是一只！躲开！
刀刃划过颈部。鲜血喷涌。
```

### 传统武侠小说

**推荐**: 史诗节奏 + 古典雅致
```
pacing: epic
writing_style: classical_elegant
```

**效果**: 古韵悠长、典雅庄重、使用典故

**示例**:
```
月华如水，洒满庭前。
少年白衣胜雪，立于梅下，手持长剑。
剑光一闪，恍若惊鸿，倏忽已至眉间。
"好剑法！"众人齐声赞道。
```

### 悬疑惊悚小说

**推荐**: 恐怖悬疑节奏 + 镜头感惊悚
```
pacing: horror
writing_style: cinematic_thriller
```

**效果**: 舒缓压抑、镜头感强、极简风格

**示例**:
```
门缓缓打开。
吱呀——
黑暗中，一双眼睛。
盯着他。
他的手，在颤抖。
```

### 轻松搞笑小说

**推荐**: 日常节奏 + 口语化幽默
```
pacing: slice_of_life
writing_style: vernacular_humorous
```

**效果**: 口语化、幽默诙谐、接地气

**示例**:
```
我跟你讲啊，这事儿真不赖我。
你信不信？反正我是信了。
结果呢？结果就被老板逮个正着。
完蛋，这下彻底凉凉了。
```

## 📋 完整预设列表

### 节奏预设 (7种)

| 预设 | 适合场景 | 句长 | 动作密度 |
|-----|---------|------|---------|
| ⚖️ balanced | 通用 | 18字 | 50% |
| 🏃 action | 战斗追逐 | 12字 | 90% |
| 🏔️ epic | 史诗仙侠 | 22字 | 60% |
| 📚 literary | 文艺心理 | 28字 | 20% |
| 😱 horror | 恐怖悬疑 | 16字 | 40% |
| 🔍 detective | 侦探推理 | 20字 | 50% |
| ☀️ slice_of_life | 日常温馨 | 18字 | 30% |

### 文风预设 (9种)

| 预设 | 适合类型 | 视角 | 用词 |
|-----|---------|------|------|
| 🔥 web_novel_cool | 玄幻仙侠 | 第三人称 | 适中 |
| ☀️ web_novel_warm | 都市日常 | 第一人称 | 简单 |
| 🌑 web_novel_dark | 末世惊悚 | 第三人称 | 高级 |
| 📜 classical_elegant | 武侠历史 | 全知 | 古雅 |
| 🏛️ archaic_vernacular | 穿越宫斗 | 第三人称 | 适中 |
| 📖 modern_literary | 通用默认 | 第三人称 | 适中 |
| 🌸 poetic_beauty | 散文唯美 | 第一人称 | 高级 |
| 🎬 cinematic_thriller | 悬疑惊悚 | 第三人称 | 适中 |
| 😄 vernacular_humorous | 轻松搞笑 | 第一人称 | 简单 |

## 🚀 使用指南

### Web UI 操作

1. 访问 http://localhost:3000/worlds
2. 点击"生成新世界"
3. 选择"叙事节奏 ⚡"（控制快慢）
4. 选择"写作文风 ✍️"（控制风格）
5. 点击"开始生成"

### API 调用示例

```bash
curl -X POST http://localhost:8000/api/worlds/generate \
  -H "Content-Type: application/json" \
  -d '{
    "novel_id": "novel-001",
    "seed": "仙侠修炼",
    "pacing_preset": "epic",
    "writing_style_preset": "web_novel_cool"
  }'
```

## 💡 选择建议

### 按小说类型快速选择

| 小说类型 | 节奏 | 文风 |
|---------|------|------|
| 玄幻仙侠 | epic | web_novel_cool |
| 都市言情 | slice_of_life | web_novel_warm |
| 末世恐怖 | action | web_novel_dark |
| 传统武侠 | epic | classical_elegant |
| 穿越宫斗 | balanced | archaic_vernacular |
| 悬疑推理 | horror | cinematic_thriller |
| 轻松搞笑 | slice_of_life | vernacular_humorous |
| 科幻冒险 | action | modern_literary |

### 新手推荐

**保险选择**:
- 节奏: balanced（平衡节奏）
- 文风: modern_literary（现代文学）

**网文新手**:
- 节奏: epic（史诗节奏）
- 文风: web_novel_cool（网文爽文）

**追求质量**:
- 节奏: literary（文学慢节奏）
- 文风: modern_literary（现代文学）

## 🔧 高级自定义

如果预设不满足需求，可以通过 API 自定义参数：

```python
from models.world_models import PacingControl, WritingStyle

# 自定义节奏
custom_pacing = PacingControl(
    global_pace="fast",
    avg_sentence_len=15,
    action_density=0.8,
    description_ratio=0.3
)

# 自定义文风
custom_style = WritingStyle(
    style_type="modern",
    vocabulary_level="advanced",
    use_metaphor=True,
    narrative_pov="first"
)
```

## 📖 详细文档

- **节奏系统详解**: `docs/features/PACING_CONTROL_GUIDE.md`
- **节奏快速开始**: `docs/features/PACING_QUICK_START.md`
- **文风系统详解**: `docs/features/WRITING_STYLE_GUIDE.md`

## 💬 常见问题

**Q: 节奏和文风必须都选吗？**
A: 不必须。如果不选，会使用默认值（balanced节奏 + modern_literary文风）。

**Q: 可以中途更换吗？**
A: 节奏和文风在创建世界时设定，后续生成会遵循该配置。如需更换，需创建新世界。

**Q: 哪个组合最受欢迎？**
A:
- 网文: epic节奏 + web_novel_cool文风
- 文学: literary节奏 + modern_literary文风
- 新手: balanced节奏 + modern_literary文风

**Q: 文风和节奏会冲突吗？**
A: 不会。它们控制的是不同维度：
- 节奏: 快慢、密度
- 文风: 风格、用词

## 🎉 总结

- **节奏调控**: 7种预设,控制叙事快慢
- **文风选择**: 9种预设,控制语言风格
- **完美组合**: 根据小说类型选择合适搭配
- **灵活使用**: 预设满足大部分需求,高级用户可自定义

开始创作你的专属小说吧！🚀
