# 下一步行动指南 🚀

## 现在就做 (5-10分钟)

### 1️⃣ 配置开发环境

```bash
# 进入项目目录
cd /Users/lijianyong/mn_xiao_shuo

# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 编辑 .env,填入你的 Anthropic API key
# 使用你喜欢的编辑器,例如:
# nano .env
# 或 vim .env
# 或 code .env (VS Code)
```

在 `.env` 中设置:
```
ANTHROPIC_API_KEY=sk-ant-xxx...  # 你的真实 API key
```

### 2️⃣ 验证环境

```bash
# 运行环境测试脚本
python test_setup.py
```

如果所有测试通过,你就可以开始开发了! 🎉

---

## 今天可以开始的开发任务

### 选项 A: 快速原型(推荐新手)

创建一个最简单的小说生成器,验证整体流程:

**创建 `minimal_generator.py`:**

```python
"""最简单的小说生成器 - 验证概念"""

import asyncio
import json
from dotenv import load_dotenv
from src.llm import LiteLLMClient

load_dotenv()

async def generate_chapter(client, setting, chapter_num):
    """生成一章"""
    prompt = f"""
你是一个科幻小说作家。

设定:
{setting["setting_text"]}

主角: {setting["主角设定"]["姓名"]}

任务: 写第 {chapter_num} 章的内容(800字左右)。

要求:
1. 符合设定中的硬规则
2. 推进剧情
3. 有具体的场景描写
4. 包含对话
"""

    result = await client.generate(
        prompt=prompt,
        model="claude-sonnet",
        max_tokens=2000,
        temperature=0.8
    )

    return result

async def main():
    # 加载设定
    with open("examples/scifi_setting.json", "r", encoding="utf-8") as f:
        setting = json.load(f)

    # 创建 LLM 客户端
    client = LiteLLMClient()

    print("=" * 60)
    print(f"开始生成小说: {setting['title']}")
    print("=" * 60)

    # 生成 3 章
    for i in range(1, 4):
        print(f"\n正在生成第 {i} 章...")
        chapter = await generate_chapter(client, setting, i)

        print(f"\n{'=' * 60}")
        print(f"第 {i} 章")
        print("=" * 60)
        print(chapter)

        # 保存
        with open(f"chapter_{i}.txt", "w", encoding="utf-8") as f:
            f.write(chapter)

        print(f"\n✅ 第 {i} 章已保存到 chapter_{i}.txt")

if __name__ == "__main__":
    asyncio.run(main())
```

**运行:**
```bash
python minimal_generator.py
```

这个简单版本可以帮你:
- ✅ 验证 LLM 集成工作正常
- ✅ 理解提示词工程的重要性
- ✅ 看到初步的生成效果
- ✅ 为后续开发建立信心

### 选项 B: 实现 Global Director (推荐有经验的开发者)

按照 `CHECKLIST.md` 第 1 周的任务:

**1. 创建 Global Director 框架**

```bash
# 创建目录
mkdir -p src/director

# 创建文件
touch src/director/__init__.py
touch src/director/gd.py
touch src/director/scoring.py
```

**2. 在 `src/director/gd.py` 中实现基础框架:**

```python
"""Global Director - 全局导演核心逻辑"""

from typing import List, Dict, Optional
from enum import Enum

from ..models import WorldState, EventNode, EventArc, ActionQueue
from ..llm import LiteLLMClient


class NovelType(Enum):
    SCIFI = "scifi"
    XIANXIA = "xianxia"


class Preference(Enum):
    PLAYABILITY = "playability"
    NARRATIVE = "narrative"
    HYBRID = "hybrid"


class GlobalDirector:
    """全局导演 - 系统核心调度器"""

    def __init__(
        self,
        setting: Dict,
        novel_type: NovelType,
        preference: Preference
    ):
        self.setting = setting
        self.novel_type = novel_type
        self.preference = preference

        # 初始化状态
        self.world_state = self._init_world_state()
        self.event_arcs = self._init_event_arcs()
        self.completed_events = []
        self.stall_rounds = 0

        # LLM 客户端
        self.llm_client = LiteLLMClient()

    def _init_world_state(self) -> WorldState:
        """从设定初始化世界状态"""
        # TODO: 实现设定解析
        return WorldState(timestamp=0, turn=0)

    def _init_event_arcs(self) -> List[EventArc]:
        """从设定初始化事件线"""
        # TODO: 实现事件线生成
        return []

    async def run_scene_loop(self):
        """场景循环主逻辑"""
        while not self.is_story_complete():
            # 1. 评分并选择下一个事件
            next_event = await self.score_and_select_event()

            if next_event is None:
                print("没有可用事件,故事结束。")
                break

            # 2. 生成动作队列
            action_queue = await self.generate_action_queue(next_event)

            # 3. 执行动作
            result = await self.execute_actions(action_queue)

            # 4. 一致性审计(TODO)

            # 5. 更新状态(TODO)

            # 6. 记录完成的事件
            self.completed_events.append(next_event.id)

            yield result

    def is_story_complete(self) -> bool:
        """检查故事是否完成"""
        # 简单实现: 所有事件都完成
        return len(self.completed_events) >= 10  # 暂定 10 个事件

    async def score_and_select_event(self) -> Optional[EventNode]:
        """评分并选择下一个事件"""
        # TODO: 实现评分逻辑
        # 现在返回第一个可用事件
        for arc in self.event_arcs:
            event = arc.get_next_event(self.world_state, self.completed_events)
            if event:
                return event
        return None

    async def generate_action_queue(self, event: EventNode) -> ActionQueue:
        """生成动作队列"""
        # TODO: 使用 LLM 生成详细动作
        return ActionQueue(
            event_id=event.id,
            goal=event.goal
        )

    async def execute_actions(self, queue: ActionQueue) -> Dict:
        """执行动作队列"""
        # TODO: 实现完整的动作执行
        # 现在简单生成场景
        prompt = f"为小说生成一个场景,目标: {queue.goal}"

        content = await self.llm_client.generate(
            prompt=prompt,
            model="claude-sonnet",
            max_tokens=1000
        )

        return {
            "event_id": queue.event_id,
            "content": content,
            "success": True
        }
```

**3. 测试基础框架:**

```python
# test_gd.py

import asyncio
from src.director.gd import GlobalDirector, NovelType, Preference

async def test():
    setting = {"title": "测试小说"}

    director = GlobalDirector(
        setting=setting,
        novel_type=NovelType.SCIFI,
        preference=Preference.HYBRID
    )

    async for scene in director.run_scene_loop():
        print(scene)

if __name__ == "__main__":
    asyncio.run(test())
```

---

## 本周目标

### 🎯 Week 1 目标: 能生成简单的小说章节

**Day 1-2**: 实现 Global Director 基础框架
**Day 3-4**: 实现评分系统
**Day 5-6**: 完善动作生成和执行
**Day 7**: 端到端测试

**成功标准**:
- ✅ 能从 JSON 设定启动系统
- ✅ 能生成连贯的 3-5 个场景
- ✅ 评分系统能选择合适的事件
- ✅ 代码有基础的单元测试

---

## 开发建议

### 💡 提示词工程技巧

生成高质量小说内容的关键在于提示词设计:

**好的提示词结构:**
```
你是一个{小说类型}作家。

【世界设定】
{详细设定}

【当前状态】
- 时间: {timestamp}
- 地点: {location}
- 主角状态: {character_state}

【前情提要】
{previous_events_summary}

【本章目标】
{chapter_goal}

【约束条件】
1. 必须遵守: {hard_rules}
2. 避免: {forbidden_actions}
3. 推进: {clues_to_advance}

【输出要求】
1. 字数: 800-1200字
2. 包含具体场景描写
3. 推进剧情
4. 符合人物性格
5. 埋下伏笔: {setups}

请开始创作:
```

### 🐛 调试技巧

1. **启用详细日志**
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

2. **保存中间结果**
```python
# 保存每次 LLM 调用的结果
with open(f"debug/prompt_{i}.txt", "w") as f:
    f.write(prompt)

with open(f"debug/response_{i}.txt", "w") as f:
    f.write(response)
```

3. **使用更便宜的模型测试**
```python
# 开发时用 Haiku
result = await client.generate(
    ...,
    model="claude-haiku"  # 便宜 10 倍
)
```

### 📚 参考资料

- **MCP 文档**: https://modelcontextprotocol.io/
- **LiteLLM 文档**: https://docs.litellm.ai/
- **Anthropic API 文档**: https://docs.anthropic.com/
- **本项目架构**: `ARCHITECTURE.md`
- **实施指南**: `IMPLEMENTATION_GUIDE.md`

---

## 遇到问题?

### 常见问题快速解决

**问题 1: `ModuleNotFoundError: No module named 'xxx'`**
```bash
pip install xxx
# 或
pip install -r requirements.txt
```

**问题 2: `litellm.exceptions.AuthenticationError`**
- 检查 `.env` 中的 API key 是否正确
- 确保 API key 有足够的额度

**问题 3: 生成内容质量不好**
- 调整提示词,增加更多上下文
- 提高 temperature (0.7 → 0.9)
- 使用更强的模型(haiku → sonnet)

**问题 4: 速度太慢**
- 减少 max_tokens
- 使用更快的模型(sonnet → haiku)
- 并发生成独立内容

### 获取帮助

1. 查看项目文档(`ARCHITECTURE.md`, `IMPLEMENTATION_GUIDE.md`)
2. 检查代码注释和 docstrings
3. 运行 `python test_setup.py` 诊断环境问题

---

## 🎉 开始你的开发之旅!

你现在拥有:
- ✅ 完整的项目架构
- ✅ 清晰的开发路线图
- ✅ 可运行的代码模板
- ✅ 详细的文档和指南

**立即行动:**

1. 配置环境 (5分钟)
2. 运行 test_setup.py (1分钟)
3. 选择开发路径 (选项A或B)
4. 开始编码! 🚀

记住: **先让它工作,再让它优雅,最后让它快速**

祝你开发顺利! 如有问题,参考文档或调试输出。

---

**项目创建**: 2025-10-30
**下次更新**: 完成 Week 1 任务后
