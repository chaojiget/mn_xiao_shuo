# 阶段 1 实现总结：自动生成系统

## 🎯 实现目标

创建一个"输入标题 → 自动生成完整设定"的 AI 跑团小说生成系统。

## ✅ 已完成功能

### 1. 后端 API (优先使用 Claude Agent SDK)

**文件位置**:
- `web/backend/generation_api.py` - FastAPI 路由和 LiteLLM 降级实现
- `web/backend/agent_generation.py` - Claude Agent SDK 实现（带自定义工具）
- `web/backend/main.py` - 注册路由

**核心功能**:
- ✅ `/api/generate-setting` - 自动生成小说设定
- ✅ `/api/optimize-setting` - 优化已有设定
- ✅ 双模式：优先 Agent SDK,降级 LiteLLM
- ✅ 自定义 Agent 工具（角色名称生成、一致性检查）

**技术亮点**:
```python
# 优先使用 Claude Agent SDK
from agent_generation import generate_with_agent

result = await generate_with_agent(
    title="星际迷航",
    novel_type="scifi"
)

# 降级到 LiteLLM
if not result.success:
    setting = await generate_novel_setting(...)
```

### 2. 前端界面 (全新设计)

**文件位置**: `web/frontend/app/chat/page.tsx`

**核心改进**:
- ✅ 突出标题输入（大字体、醒目样式）
- ✅ 一键生成按钮（渐变紫粉色，带动画）
- ✅ 实时显示生成进度（Loader2 动画）
- ✅ 生成结果展示（主角、世界观、NPC卡片）
- ✅ "开始创作"按钮进入跑团模式

**界面布局**:
```
┌─────────────────────────────────────────┐
│  ✨ AI 跑团小说                          │
│  输入标题，一键生成完整的世界观和角色设定  │
│                                         │
│  📖 小说标题: [输入框]                   │
│  🎨 类型: [🚀 科幻] [⚔️ 玄幻]           │
│  [✨ 一键生成完整设定] <- 超大按钮        │
│                                         │
│  生成的设定:                             │
│  ├─ 👤 主角卡片                         │
│  ├─ 🌍 世界观                           │
│  └─ 🎭 NPC 列表                         │
│                                         │
│  [✨ 开始创作] <- 进入跑团模式            │
└─────────────────────────────────────────┘
```

### 3. Claude Agent SDK 集成

**自定义工具示例**:

```python
@tool("generate_character_name", "生成符合类型的角色名称", {
    "novel_type": str,
    "role": str
})
async def generate_character_name(args):
    """根据小说类型和角色定位生成名称"""
    # ... 实现逻辑

@tool("check_consistency", "检查设定一致性", {
    "world_setting": str,
    "character_description": str
})
async def check_consistency(args):
    """检查角色设定是否与世界观一致"""
    # ... 实现逻辑
```

**使用自定义工具**:

```python
from agent_generation import create_novel_generation_tools

novel_tools = create_novel_generation_tools()

options = ClaudeAgentOptions(
    max_turns=5,
    mcp_servers={"novel_tools": novel_tools},
    allowed_tools=[
        "mcp__novel_tools__generate_character_name",
        "mcp__novel_tools__check_consistency"
    ]
)

async for message in query(prompt=prompt, options=options):
    # Agent 会自动调用工具生成更好的结果
    ...
```

## 📊 生成流程

### 用户视角流程:

```
1. 输入标题: "星际迷航"
2. 选择类型: 🚀 科幻
3. 点击 "✨ 一键生成完整设定"
   ↓
4. 显示加载动画: "AI 正在创作中..."
   ↓
5. 后端自动生成:
   - 世界观设定 (300-500字)
   - 主角信息 (姓名、角色、性格、背景、能力)
   - 3+ NPC (各有姓名、定位、性格、背景)
   ↓
6. 前端展示结果:
   - 👤 主角卡片（蓝色）
   - 🌍 世界观详情（紫色）
   - 🎭 NPC 列表（绿色）
   ↓
7. 点击 "开始创作" → 进入跑团聊天界面
```

### 技术流程:

```
前端请求
    ↓
POST /api/generate-setting
    {
        "title": "星际迷航",
        "novel_type": "scifi"
    }
    ↓
尝试 Claude Agent SDK
    ├─ 成功 → 返回结果
    └─ 失败/未安装 → 降级到 LiteLLM
        ↓
    LiteLLM + DeepSeek V3
        ↓
    生成 JSON 格式设定
        ↓
    解析并返回
        ↓
前端接收并展示
    {
        "success": true,
        "setting": {
            "world_setting": "...",
            "protagonist": {...},
            "npcs": [...]
        }
    }
```

## 🔧 关键技术

### 1. 提示词工程

**科幻类型模板**:
```
核心元素：星际旅行、高科技、外星文明、人工智能、太空探索
主角可选角色：飞行员、科学家、军官、赏金猎人、殖民者
世界观包含：时间设定、科技水平、星际格局、主要势力、核心冲突
```

**玄幻类型模板**:
```
核心元素：修炼体系、门派势力、灵兽法宝、秘境宝藏、天道轮回
主角可选角色：修仙者、散修、宗门弟子、魔道修士、炼器师
世界观包含：修炼等级、门派势力、地理格局、修炼资源、天道规则
```

### 2. Agent 工具系统

**优势**:
- 可以调用外部 API（如角色名称库）
- 可以执行复杂推理（一致性检查）
- 可以使用 MCP 服务器（未来扩展）
- 支持多轮对话优化设定

**工具链**:
```
generate_character_name  → 生成符合类型的角色名称
    ↓
check_consistency → 检查世界观与角色一致性
    ↓
generate_npc_relationship → 生成 NPC 之间的关系网
    ↓
create_plot_outline → 创建剧情大纲
```

### 3. 双模式架构

**优点**:
- 灵活性：Agent SDK 可选，不强制依赖
- 稳定性：Agent 失败时自动降级
- 性能：Agent 更智能，LiteLLM 更快

**选择逻辑**:
```python
if agent_sdk_available and agent_generation_success:
    use_agent_mode()  # 更智能
else:
    use_litellm_mode()  # 更稳定、更快
```

## 📦 数据模型

### NovelSettings (前端)

```typescript
interface NovelSettings {
  id?: string
  title: string
  type: "scifi" | "xianxia"
  protagonist: string
  background: string
  protagonistName?: string
  protagonistRole?: string
  protagonistAbilities?: string[]
  npcs?: NPC[]
}

interface NPC {
  id: string
  name: string
  role: string
  personality: string
  background: string
}
```

### GeneratedSetting (后端)

```python
class ProtagonistInfo(BaseModel):
    name: str
    role: str
    personality: str
    background: str
    abilities: List[str]

class NPCInfo(BaseModel):
    id: str
    name: str
    role: str
    personality: str
    background: str

class GeneratedSetting(BaseModel):
    title: str
    novel_type: str
    world_setting: str
    protagonist: ProtagonistInfo
    npcs: List[NPCInfo]
```

## 🧪 测试指南

### 1. 基础功能测试

```bash
# 启动服务
./web/start-web.sh

# 访问页面
# http://localhost:3001/chat

# 测试步骤:
1. 输入标题: "星际迷航"
2. 选择类型: 科幻
3. 点击 "一键生成"
4. 等待 10-30 秒
5. 查看生成结果
6. 点击 "开始创作"
```

### 2. API 测试

```bash
# 测试自动生成 API
curl -X POST http://localhost:8000/api/generate-setting \
  -H "Content-Type: application/json" \
  -d '{
    "title": "星际迷航",
    "novel_type": "scifi"
  }'

# 期望输出:
{
  "success": true,
  "setting": {
    "title": "星际迷航",
    "world_setting": "2350年，人类文明已经...",
    "protagonist": {
      "name": "艾伦·克拉克",
      "role": "星际飞行员",
      ...
    },
    "npcs": [...]
  },
  "method": "agent" # 或 "litellm"
}
```

### 3. Agent SDK 测试

```python
# 直接测试 Agent 生成
import asyncio
from agent_generation import generate_with_agent

result = asyncio.run(generate_with_agent(
    title="修仙者传说",
    novel_type="xianxia"
))

print(result)
```

## 📝 配置要求

### 环境变量 (.env)

```bash
# OpenRouter API Key (LiteLLM 降级模式需要)
OPENROUTER_API_KEY=sk-...

# Anthropic API Key (Agent SDK 需要)
ANTHROPIC_API_KEY=sk-ant-...
```

### 依赖安装

```bash
# 基础依赖 (已有)
pip install -r requirements.txt

# Agent SDK (可选,推荐)
pip install claude-agent-sdk

# 前端依赖 (已有)
cd web/frontend
npm install
```

## 🚀 后续优化方向

### 阶段 2: 多 Agent 跑团系统

**下一步计划**:
1. ✅ GD (Global Director) Agent - 安排剧情、触发事件
2. ✅ Narrator Agent - 旁白描述、场景渲染
3. ✅ NPC Agents - 每个 NPC 独立 AI 对话
4. ✅ 主角 Agent - 半自动/用户控制

**架构草图**:
```
用户输入
    ↓
GD Agent (协调员)
    ├─ Narrator Agent → 描述场景
    ├─ NPC Agent 1 → 莎拉博士对话
    ├─ NPC Agent 2 → 老船长反应
    └─ 主角 Agent → 等待用户选择
```

### 优化项:

**1. 更多自定义工具**
- 查询星球数据库
- 生成装备/道具
- 计算战斗结果
- 触发随机事件

**2. MCP 服务器集成**
- 向量数据库查询相似剧情
- 维基百科查询设定资料
- GitHub 查询代码示例
- Brave Search 搜索灵感

**3. 持久化**
- 保存生成的设定到数据库
- 支持继续之前的跑团
- 导出设定为 Markdown

**4. 用户体验**
- 流式显示生成进度
- 支持修改生成的设定
- 预览模式vs详细模式
- 主题切换（科幻/玄幻风格）

## 🎉 总结

阶段 1 成功实现了：

✅ **核心功能**: 输入标题 → 自动生成完整设定
✅ **技术架构**: Agent SDK + LiteLLM 双模式
✅ **界面优化**: 突出标题输入，一键生成
✅ **自定义工具**: 可扩展的 Agent 工具系统
✅ **代码质量**: 类型检查、错误处理、降级机制

**下一步**: 开始阶段 2 - 多 Agent 交互跑团系统！
