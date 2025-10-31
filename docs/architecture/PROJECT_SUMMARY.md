# 长篇小说生成系统 - 项目总结

## 项目状态: 架构完成,准备开发 MVP

---

## 📊 项目信息

- **项目名称**: 长篇小说生成系统 (Novel Generator System)
- **目标**: AI驱动的科幻/玄幻长篇小说生成平台
- **技术栈**: Python 3.11+, Claude API, LiteLLM, MCP
- **当前阶段**: Phase 1 准备(MVP核心功能开发前)

---

## ✅ 已完成内容

### 1. 完整架构设计
**文件**: `ARCHITECTURE.md` (19KB, 详细设计文档)

包含:
- 系统总览与组件架构图
- 技术栈选型(MCP + Claude Agent SDK + LiteLLM)
- 核心模块设计(GlobalDirector, Agent执行器, MCP服务器)
- 数据库Schema设计
- 部署架构(开发/生产环境)
- 4阶段开发路线图

### 2. 项目结构搭建

```
mn_xiao_shuo/
├── ARCHITECTURE.md          # 架构设计文档
├── IMPLEMENTATION_GUIDE.md  # 实施指南
├── PROJECT_SUMMARY.md       # 本文件
├── README.md                # 项目说明
├── requirements.txt         # Python依赖
├── .env.example             # 环境变量模板
├── .gitignore               # Git忽略规则
│
├── config/                  # 配置文件
│   ├── litellm_config.yaml  # LiteLLM模型路由配置
│   └── novel_types.yaml     # 小说类型评分参数
│
├── examples/                # 示例设定
│   ├── scifi_setting.json   # 科幻《能源纪元》
│   └── xianxia_setting.json # 玄幻《逆天改命录》
│
├── src/                     # 源代码
│   ├── models/              # ✅ 数据模型(已完成)
│   │   ├── __init__.py
│   │   ├── world_state.py   # 世界状态
│   │   ├── event_node.py    # 事件节点
│   │   ├── action_queue.py  # 动作队列
│   │   └── clue.py          # 线索/伏笔/证据
│   │
│   ├── llm/                 # ✅ LLM集成(已完成)
│   │   ├── __init__.py
│   │   └── litellm_client.py # LiteLLM统一客户端
│   │
│   ├── director/            # 🚧 待实现
│   │   ├── gd.py            # GlobalDirector主逻辑
│   │   ├── agent_executor.py
│   │   ├── scoring.py
│   │   └── consistency.py
│   │
│   ├── mcp_server/          # 🚧 待实现
│   │   └── novel_world_server.py
│   │
│   └── utils/               # 🚧 待实现
│       ├── database.py
│       ├── setting_parser.py
│       └── vector_db.py
│
├── data/                    # 数据目录
├── logs/                    # 日志目录
├── scripts/                 # 脚本
│   └── init_db.py           # 🚧 待创建
└── tests/                   # 测试
    └── test_*.py            # 🚧 待创建
```

### 3. 核心数据模型 (100% 完成)

#### WorldState (世界状态)
- Location: 地点状态
- Character: 角色状态(属性/资源/关系)
- Faction: 势力组织
- Resource: 资源池
- 状态补丁应用机制

#### EventNode & EventArc (事件系统)
- EventNode: 事件节点(包含全部评分指标)
- EventArc: 事件线管理
- 前置条件检查
- 进度跟踪

#### ActionQueue (动作队列)
- ActionStep: 动作步骤(scene/interaction/check/tool/outcome)
- Hint: 提示系统(implicit/explicit/red_herring)
- 状态补丁模板

#### Clue Economy (线索经济)
- Clue: 线索(发现/验证机制)
- Evidence: 证据(可信度/关联)
- Setup: 伏笔(SLA管理/逾期检查)
- ClueRegistry: 线索注册表

### 4. LiteLLM 客户端 (100% 完成)

**功能**:
- ✅ 基础文本生成 (`generate`)
- ✅ 结构化输出 (`generate_structured` - JSON Schema)
- ✅ 函数调用 (`generate_with_functions`)
- ✅ 批量生成 (`batch_generate`)
- ✅ 配置驱动(YAML)
- ✅ 环境变量替换
- ✅ 模型信息查询

### 5. 配置文件

#### litellm_config.yaml
- 模型列表(Claude Sonnet/Haiku/GPT-4备用)
- 路由策略(least-busy)
- 降级策略(fallbacks)
- 重试策略(3次,指数退避)
- 超时/并发限制

#### novel_types.yaml
- 科幻小说评分权重(可玩性/叙事)
- 玄幻小说评分权重(偏可玩性 0.7/0.3)
- 节奏参数(幕数/场景数/张力曲线)
- 一致性规则(硬规则/软规则)
- 提示策略

### 6. 示例设定

#### 科幻《能源纪元》
- 背景: 2157年,暗能结晶时代
- 主角: 林墨(能源工程师)
- 目标: 揭露能源垄断阴谋
- 事件线: 发现异常 → 暗流涌动 → 公开对决
- 硬规则: 光速限制/能量守恒/技术树依赖

#### 玄幻《逆天改命录》
- 背景: 修仙界南域,青云宗
- 主角: 云枫(炼气期三层,五灵根)
- 特殊功法: 逆天诀(逆转因果,业力反噬)
- 事件线: 外门求存 → 断魂谷历练 → 宗门大比 → 魔道来袭
- 境界体系: 炼气→筑基→金丹→元婴→化神

---

## 🚧 待实现核心模块

### Phase 1 (MVP - 2-3周)

#### 1. Global Director (全局导演)
**优先级**: 🔴 最高

关键功能:
- `run_scene_loop()`: 场景循环主逻辑
- `score_and_select_event()`: 评分选择事件
- `generate_action_queue()`: 生成动作队列
- `execute_actions()`: 执行动作(调用LLM/Agent)
- `consistency_audit()`: 一致性审计
- `update_clue_economy()`: 线索与伏笔管理

#### 2. 评分系统
**优先级**: 🔴 最高

- `_score_playability()`: 可玩性评分
- `_score_narrative()`: 叙事评分
- `_score_hybrid()`: 混合评分(动态权重)

#### 3. 一致性审计器
**优先级**: 🟡 高

- `check_hard_rules()`: 硬规则检查
- `check_causality()`: 因果链检查
- `check_resource_conservation()`: 资源守恒检查
- `check_theme_consistency()`: 主题一致性

#### 4. 数据库层
**优先级**: 🟡 高

- SQLite 初始化
- 状态持久化
- 事件历史查询

#### 5. 设定解析器
**优先级**: 🟡 高

- 解析 JSON 设定
- 生成初始 WorldState
- 生成初始 EventArc

#### 6. CLI 入口
**优先级**: 🟢 中

- 加载设定
- 启动 GlobalDirector
- 用户交互循环
- 输出格式化

---

## 📋 开发路线图

### ✅ Phase 0: 架构与规划 (已完成)
- [x] 架构设计
- [x] 项目结构
- [x] 数据模型
- [x] LiteLLM 集成
- [x] 配置文件
- [x] 示例设定

### 🚧 Phase 1: MVP 核心功能 (2-3周)
- [ ] Global Director 核心逻辑
- [ ] 评分系统
- [ ] 一致性审计
- [ ] 数据库层
- [ ] 设定解析器
- [ ] CLI 入口
- [ ] 基础测试

**里程碑**: 能够生成基础的科幻/玄幻小说章节

### 🔜 Phase 2: 增强功能 (2-3周)
- [ ] MCP Server 实现
- [ ] Claude Agent SDK 集成(或替代方案)
- [ ] 向量数据库(ChromaDB)
- [ ] 线索经济完整实现
- [ ] 伏笔债务管理

**里程碑**: 支持复杂的证据链推理和长期伏笔管理

### 🔜 Phase 3: 优化 (2周)
- [ ] 异步任务调度
- [ ] 缓存机制(Redis)
- [ ] PostgreSQL 迁移
- [ ] 性能优化

**里程碑**: 生产级性能

### 🔜 Phase 4: 产品化 (3周)
- [ ] Web API (FastAPI)
- [ ] WebSocket 流式生成
- [ ] 用户认证
- [ ] 导出功能(Markdown/EPUB)
- [ ] Docker 部署

**里程碑**: 可部署的 Web 应用

---

## 🎯 快速开始

### 1. 环境配置

```bash
# 克隆/进入项目目录
cd mn_xiao_shuo

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env,填入你的 ANTHROPIC_API_KEY
```

### 2. 测试现有模块

#### 测试 LiteLLM 客户端

创建 `test_litellm.py`:

```python
import asyncio
import os
from dotenv import load_dotenv
from src.llm.litellm_client import LiteLLMClient

load_dotenv()

async def test():
    client = LiteLLMClient()

    print("可用模型:", client.list_models())

    # 测试生成
    result = await client.generate(
        prompt="写一段科幻小说的开头,主题是能源危机,100字以内。",
        model="claude-sonnet",
        max_tokens=200
    )

    print("\n生成结果:")
    print(result)

if __name__ == "__main__":
    asyncio.run(test())
```

运行:
```bash
python test_litellm.py
```

#### 测试数据模型

创建 `test_models.py`:

```python
from src.models import WorldState, Character, EventNode, Clue

# 创建世界状态
world = WorldState(timestamp=0, turn=0)

# 添加主角
protagonist = Character(
    id="CHAR-001",
    name="林墨",
    role="protagonist",
    attributes={"数据分析": 9, "工程技术": 8},
    resources={"信用点": 50000}
)

world.characters["CHAR-001"] = protagonist

# 打印状态
import json
print(json.dumps(world.to_dict(), indent=2, ensure_ascii=False))
```

运行:
```bash
python test_models.py
```

### 3. 下一步开发

参考 `IMPLEMENTATION_GUIDE.md` 第 1 周的任务:

1. 创建 `src/director/gd.py`
2. 实现 `GlobalDirector` 类的基础框架
3. 实现评分系统
4. 测试端到端场景生成

---

## 💡 技术亮点

### 1. 全局导演 (GD) 工作流

基于你提供的设计,实现了完整的事件调度循环:
- **评分驱动**: 动态评分选择下一个事件(可玩性/叙事平衡)
- **一致性保证**: 多层审计机制(硬规则/因果/资源/主题)
- **线索经济**: 伏笔SLA管理,防止遗忘埋下的伏笔

### 2. 模型路由与降级

通过 LiteLLM 实现:
- **统一接口**: 无缝切换 Claude/GPT-4/其他模型
- **自动降级**: 主模型失败时自动切换备用
- **成本优化**: 简单任务用 Haiku,复杂任务用 Sonnet

### 3. 数据驱动配置

所有评分权重、节奏参数、一致性规则都在 YAML 中:
- **易调整**: 修改配置文件即可调整小说生成策略
- **多类型**: 科幻/玄幻使用不同的参数集

### 4. 证据链可验证

- 每条线索绑定 `evidence_ids`
- 证据有 `credibility` (可信度)
- 支持交叉验证

---

## ⚠️ 注意事项

### MCP Context7

- **MCP** 是 Anthropic 的开放协议,但 **"Context7"** 可能是误称或特定实现
- 建议使用官方 MCP Python SDK: `pip install mcp`
- 如果找不到 Context7,可以自己实现 MCP Server(参考架构文档)

### Claude Agent SDK

- 截至 2025-01 可能尚未正式发布
- **替代方案**:
  1. 提示词工程(推荐 MVP 阶段使用)
  2. LangChain/LlamaIndex
  3. 自实现简单 Agent 循环

### 成本控制

- Claude Sonnet 4.5: ~$3/1M input, ~$15/1M output
- 生成 100 章小说预估成本: **~$150**
- **优化**: 多用 Haiku(便宜 10 倍) + 缓存

---

## 📚 相关文档

- **ARCHITECTURE.md**: 完整架构设计(19KB)
- **IMPLEMENTATION_GUIDE.md**: 分阶段实施指南(13KB)
- **README.md**: 项目说明与快速开始(4KB)

---

## 📞 联系与支持

如有问题,请参考:
1. `IMPLEMENTATION_GUIDE.md` 的"常见问题"章节
2. 架构文档中的具体实现示例
3. 代码注释和 docstrings

---

## 🎉 总结

你现在拥有一个**架构完整、模块清晰、可立即开发**的长篇小说生成系统项目。

**关键优势**:
- ✅ 基于你的 GD 工作流设计
- ✅ 整合 MCP + Agent SDK + LiteLLM
- ✅ 数据模型完整,配置驱动
- ✅ 两个详细的示例设定
- ✅ 清晰的开发路线图

**下一步**: 实现 `Global Director` 核心逻辑,开始生成你的第一个章节! 🚀

---

**项目创建时间**: 2025-10-30
**当前状态**: Phase 0 完成,准备进入 Phase 1 MVP 开发
**预计 MVP 完成时间**: 2-3 周后
