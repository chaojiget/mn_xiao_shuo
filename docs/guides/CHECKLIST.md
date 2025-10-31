# 开发检查清单

## 立即可做的事情

### 🎯 Step 1: 环境配置 (5分钟)

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env,填入你的 ANTHROPIC_API_KEY

# 4. 运行测试
python test_setup.py
```

### 🎯 Step 2: 验证现有模块 (10分钟)

创建 `quick_test.py`:

```python
import asyncio
from dotenv import load_dotenv
from src.llm import LiteLLMClient
from src.models import WorldState, Character

load_dotenv()

async def test_llm():
    """测试 LLM 客户端"""
    client = LiteLLMClient()

    result = await client.generate(
        prompt="用一句话介绍什么是全局导演(Global Director)系统。",
        model="claude-sonnet",
        max_tokens=100
    )

    print("LLM 生成结果:")
    print(result)

def test_models():
    """测试数据模型"""
    world = WorldState(timestamp=0, turn=0)

    protagonist = Character(
        id="CHAR-001",
        name="测试角色",
        role="protagonist",
        attributes={"智力": 8},
        resources={"金币": 1000}
    )

    world.characters["CHAR-001"] = protagonist

    print("\n世界状态:")
    print(f"- 回合: {world.turn}")
    print(f"- 角色数: {len(world.characters)}")
    print(f"- 主角: {world.get_protagonist().name}")

if __name__ == "__main__":
    print("=" * 60)
    print("测试 LLM 客户端")
    print("=" * 60)
    asyncio.run(test_llm())

    print("\n" + "=" * 60)
    print("测试数据模型")
    print("=" * 60)
    test_models()
```

运行:
```bash
python quick_test.py
```

---

## 第 1 周开发任务 (MVP Phase 1)

### Day 1-2: Global Director 框架

- [ ] 创建 `src/director/__init__.py`
- [ ] 创建 `src/director/gd.py`
- [ ] 实现 `GlobalDirector` 类的基础框架
  - [ ] `__init__()`
  - [ ] `run_scene_loop()` (简化版)
  - [ ] `get_available_events()`
  - [ ] `is_story_complete()`

### Day 3-4: 评分系统

- [ ] 创建 `src/director/scoring.py`
- [ ] 实现评分函数:
  - [ ] `score_playability(event, world_state)`
  - [ ] `score_narrative(event, world_state)`
  - [ ] `score_hybrid(event, world_state, stall_rounds)`
- [ ] 在 `GlobalDirector` 中集成评分系统

### Day 5: 动作队列生成

- [ ] 实现 `generate_action_queue(event)` (使用 LLM)
- [ ] 编写生成动作队列的提示词模板
- [ ] 测试 JSON 结构化输出

### Day 6: 动作执行

- [ ] 实现 `execute_actions(action_queue)` (使用 LLM)
- [ ] 编写场景生成的提示词模板
- [ ] 测试场景生成输出

### Day 7: 端到端测试

- [ ] 编写简单的测试事件线
- [ ] 测试完整的 `run_scene_loop()`
- [ ] 调试和优化

---

## 第 2 周开发任务

### Day 8-9: 一致性审计

- [ ] 创建 `src/director/consistency.py`
- [ ] 实现 `ConsistencyAuditor` 类
- [ ] 实现各种检查函数

### Day 10-11: 数据持久化

- [ ] 创建 `src/utils/database.py`
- [ ] 设计数据库 Schema
- [ ] 实现状态保存/加载

### Day 12-13: 设定解析

- [ ] 创建 `src/utils/setting_parser.py`
- [ ] 实现 JSON 设定解析
- [ ] 从设定生成初始世界状态和事件线

### Day 14: CLI 入口

- [ ] 创建 `src/cli.py`
- [ ] 实现用户交互循环
- [ ] 美化输出(使用 rich 库)

---

## 第 3 周开发任务

### Day 15-17: 线索经济

- [ ] 实现线索发现机制
- [ ] 实现伏笔 SLA 管理
- [ ] 实现证据验证

### Day 18-19: 提示策略

- [ ] 实现隐性/显性提示生成
- [ ] 实现提示触发逻辑
- [ ] 实现红鲱鱼机制

### Day 20-21: 完整测试

- [ ] 用科幻设定生成 5 章
- [ ] 用玄幻设定生成 5 章
- [ ] 收集问题和优化点

---

## 检查点

### ✅ 环境配置检查点
- [ ] 虚拟环境已创建
- [ ] 依赖已安装
- [ ] .env 文件已配置
- [ ] test_setup.py 全部通过

### ✅ MVP Week 1 检查点
- [ ] GlobalDirector 类可运行
- [ ] 评分系统正常工作
- [ ] 能生成简单的场景
- [ ] 代码有基础测试

### ✅ MVP Week 2 检查点
- [ ] 一致性审计可用
- [ ] 数据可持久化
- [ ] 能从 JSON 加载设定
- [ ] CLI 可交互使用

### ✅ MVP Week 3 检查点
- [ ] 线索经济完整实现
- [ ] 提示系统正常工作
- [ ] 能生成连贯的多章节小说
- [ ] 有端到端测试

---

## 常见问题速查

### Q: 缺少某个 Python 包?
```bash
pip install <package-name>
# 或更新 requirements.txt 后
pip install -r requirements.txt
```

### Q: API 调用失败?
1. 检查 .env 中的 API key 是否正确
2. 检查网络连接
3. 查看 LiteLLM 日志

### Q: 如何调整评分权重?
编辑 `config/novel_types.yaml` 中对应小说类型的 `scoring_weights`

### Q: 如何添加新的小说类型?
在 `config/novel_types.yaml` 中添加新的配置块,参考 scifi/xianxia

### Q: 如何切换到不同的 LLM?
编辑 `config/litellm_config.yaml`,添加新模型或修改 fallbacks

---

## 推荐开发工具

- **IDE**: VS Code / PyCharm
- **Python 版本管理**: pyenv
- **虚拟环境**: venv (标准库) 或 conda
- **代码格式化**: black
- **类型检查**: mypy
- **测试**: pytest

---

## 性能优化建议 (后期)

1. **缓存 LLM 响应** (相同提示词重复调用)
2. **批量生成** (多个独立任务并发)
3. **使用更快的模型** (Haiku 处理简单任务)
4. **向量数据库索引优化**
5. **数据库查询优化** (索引、连接池)

---

## 部署清单 (Phase 4)

- [ ] Docker 镜像构建
- [ ] 环境变量管理(生产环境)
- [ ] 数据库迁移脚本
- [ ] 监控和日志收集
- [ ] API 文档(Swagger)
- [ ] CI/CD 流水线
- [ ] 负载测试

---

最后更新: 2025-10-30
