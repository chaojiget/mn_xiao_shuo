# 游戏系统功能文档

## 📖 概述

这是一个基于 AI 驱动的单人文字冒险游戏系统,采用现代 Web 技术栈和 LLM (DeepSeek V3) 提供沉浸式的游戏体验。

**技术栈:**
- 前端: Next.js 14 + TypeScript + Tailwind CSS + shadcn/ui + Framer Motion
- 后端: FastAPI + Python
- AI: LiteLLM + DeepSeek V3
- 数据: SQLite + Pydantic

---

## ✨ 核心功能

### 1. 流式文本显示 ⚡

**特性:**
- 逐字显示 AI 生成的旁白,提升沉浸感
- 打字机效果,速度可调(默认 20ms/字)
- 流畅的动画过渡
- 光标闪烁效果

**实现位置:**
- `web/frontend/components/chat/StreamingText.tsx`
- 使用 Framer Motion 实现动画

**用户体验:**
```
你缓缓走进森林... → 你缓缓走进森林,四周...
(逐字显示,不是瞬间出现)
```

---

### 2. 增强的视觉界面 🎨

#### 2.1 叙事区域
- 渐变背景(深蓝-紫色)
- 玩家输入高亮显示(青色,带边框)
- AI 旁白以琥珀色显示,使用 serif 字体
- 自动滚动到最新内容
- 卷轴图标标题

#### 2.2 角色状态卡片
**实时显示:**
- 生命值:带进度条(红色渐变)
- 体力值:带进度条(绿色渐变)
- 当前位置:带地图图标
- 金币数量:带硬币图标

**视觉特效:**
- 渐变背景(玫瑰-紫色)
- 平滑的进度条动画
- 图标化的属性展示
- 实时更新(无需刷新)

#### 2.3 交互建议
- Chip 样式的快捷按钮
- 点击自动填充输入框
- 根据场景动态更新
- 最多显示 5 个建议

---

### 3. 地图可视化系统 🗺️

**功能:**
- SVG 渲染的交互式地图
- 节点状态显示:
  - 🟡 当前位置(黄色,脉冲动画)
  - 🟠 已探索(橙色)
  - ⚫ 未知(灰色,显示 "???")
  - 🔒 锁定(需要钥匙)
  - ✅ 已访问标记

**路径显示:**
- 实线:已探索路径
- 虚线:未知路径
- 路径发现动画

**实现细节:**
- 组件:`web/frontend/components/chat/SimpleMap.tsx`
- 自动布局:网格算法计算节点位置
- 响应式:适配不同屏幕尺寸

---

### 4. 游戏状态管理 💾

#### 4.1 自动保存
- 每 30 秒自动保存到 LocalStorage
- 状态变化时立即保存
- 包含完整游戏状态快照

#### 4.2 手动存档
- 保存按钮:即时存档
- 读取按钮:恢复游戏
- 导出按钮:下载 JSON 文件
- 导入功能(计划中)

#### 4.3 状态包含内容
```json
{
  "version": "1.0.0",
  "player": {
    "hp": 100,
    "maxHp": 100,
    "stamina": 100,
    "inventory": [...],
    "location": "start",
    "money": 50,
    "traits": ["勇敢", "好奇"]
  },
  "world": {
    "time": 5,
    "flags": {...},
    "discoveredLocations": ["start", "forest"]
  },
  "quests": [...],
  "map": {...},
  "log": [...]
}
```

---

### 5. AI 工具调用系统 🛠️

后端提供 9 个核心工具供 AI 使用:

| 工具名 | 功能 | 示例 |
|--------|------|------|
| `get_player_state` | 获取玩家状态 | 查看生命值、背包 |
| `add_item` | 添加物品 | 拾起剑、收集钥匙 |
| `remove_item` | 移除物品 | 使用药水、丢弃物品 |
| `update_hp` | 更新生命 | 受伤-10、治疗+20 |
| `update_stamina` | 更新体力 | 奔跑-15、休息+30 |
| `set_location` | 改变位置 | 进入森林、回到城镇 |
| `set_flag` | 设置标志 | 记录事件状态 |
| `roll_check` | 技能检定 | 潜行、说服、感知 |
| `update_quest` | 更新任务 | 激活、完成任务 |

**工作流程:**
```
玩家输入 → LLM 理解意图 → 调用工具修改状态 → 生成旁白 → 更新 UI
```

---

### 6. 技能检定系统 🎲

**支持的检定类型:**
- `survival`:野外生存
- `stealth`:潜行
- `persuasion`:说服
- `perception`:感知
- `strength`:力量
- `intelligence`:智力
- `luck`:运气

**检定机制:**
- 基础:1d20 + 修正值
- 优势:投两次取高值
- 劣势:投两次取低值
- 特质加成:相关特质+2 修正

**检定流程:**
```python
# 示例:尝试潜行穿过守卫(难度15)
{
  "type": "stealth",
  "dc": 15,
  "modifier": 0,
  "advantage": False
}

# 返回结果
{
  "success": True,
  "roll": 17,
  "total": 17,
  "dc": 15,
  "margin": 2,
  "critical": False
}
```

---

### 7. 背包系统 🎒

**物品属性:**
- `id`:唯一标识
- `name`:名称
- `description`:描述
- `quantity`:数量
- `type`:类型(weapon/armor/consumable/key/quest/misc)
- `properties`:自定义属性(攻击力、防御力等)

**功能:**
- 自动堆叠相同物品
- 按类型分类显示
- 实时同步到 UI
- 支持物品使用和丢弃

---

### 8. 任务系统 📜

**任务状态:**
- `inactive`:未激活
- `active`:进行中
- `completed`:已完成
- `failed`:已失败

**任务结构:**
```typescript
{
  "id": "quest_001",
  "title": "寻找失落的钥匙",
  "description": "村长要求你找到古老洞穴的钥匙",
  "status": "active",
  "hints": ["钥匙可能在森林深处"],
  "objectives": [
    {
      "id": "obj_1",
      "description": "探索迷雾森林",
      "completed": true,
      "required": true
    }
  ]
}
```

---

### 9. 日志与历史 📋

**记录内容:**
- 玩家每次输入
- AI 生成的旁白
- 工具调用结果
- 重要事件触发

**用途:**
- 回顾游戏历程
- 调试和分析
- 生成游戏总结
- 提供上下文给 AI

---

## 🎮 用户操作指南

### 开始游戏
1. 访问 http://localhost:3000/game
2. 点击"开始游戏"按钮
3. 等待初始化完成
4. 阅读欢迎旁白

### 输入行动
```
方式1: 输入框键入文字 → 点击"执行"
方式2: 输入框键入文字 → 按 Enter 键
方式3: 点击建议 Chip → 自动填充 → 执行
```

### 常用命令示例
```
探索类:
- 环顾四周
- 向北走
- 进入森林
- 检查洞穴入口

交互类:
- 拾起剑
- 和村长对话
- 打开宝箱

战斗类:
- 攻击敌人
- 使用治疗药水
- 躲避攻击

检定类:
- 尝试潜行穿过守卫
- 说服商人降价
- 感知周围危险
```

---

## 🔧 开发者信息

### 启动服务
```bash
# 一键启动(推荐)
./start_all_with_agent.sh

# 手动启动
# 终端1 - 后端
cd web/backend && source ../../.venv/bin/activate && uvicorn main:app --reload --port 8000

# 终端2 - 前端
cd web/frontend && npm run dev
```

### API 端点
```
POST /api/game/init          - 初始化游戏
POST /api/game/turn          - 处理回合(非流式)
POST /api/game/turn/stream   - 处理回合(流式,SSE)
GET  /api/game/tools         - 获取可用工具列表
GET  /health                 - 健康检查
```

### 环境变量
```bash
OPENROUTER_API_KEY=your_api_key_here   # OpenRouter API 密钥
DATABASE_URL=data/sqlite/novel.db      # SQLite 数据库路径
```

### 性能指标
- 初始化时间:< 1 秒
- 简单回合:3-8 秒(取决于 LLM)
- 复杂回合:8-15 秒
- Token 消耗:500-1500 (prompt) + 200-500 (response)
- 成本(DeepSeek V3):~$0.001 USD/回合

---

## 🚀 未来功能计划

### Phase 2 (进行中)
- [x] 流式文本输出
- [x] 增强视觉界面
- [x] 地图可视化
- [ ] 实时 SSE 流式响应
- [ ] NPC 系统增强
- [ ] 战斗系统

### Phase 3 (规划中)
- [ ] 多结局系统
- [ ] 成就系统
- [ ] 音效与背景音乐
- [ ] 角色自定义
- [ ] 多语言支持
- [ ] 移动端适配

---

## 📚 相关文档

- [测试指南](./TESTING_GUIDE.md) - 完整测试流程
- [架构设计](../CLAUDE.md) - 技术架构说明
- [快速开始](./guides/QUICK_START.md) - 新手入门

---

**最后更新**: 2025-11-01
**当前版本**: Phase 2 - Enhanced UI & Visualization
