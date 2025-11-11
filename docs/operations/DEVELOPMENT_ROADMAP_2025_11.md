# 开发路线图 - 2025年11月

**创建时间**: 2025-11-10 22:40
**当前版本**: Week 3 完成，Week 4 规划中
**核心目标**: TRPG 游戏体验完善与性能优化

---

## ✅ 已完成 (Week 1-3)

### Week 1: 基础架构
- ✅ LangChain 1.0 迁移
- ✅ OpenRouter 集成
- ✅ SQLite 数据库设计
- ✅ 15个游戏工具实现

### Week 2: DM Agent 升级
- ✅ LangGraph Checkpoint 记忆系统
- ✅ 流式输出支持
- ✅ WebSocket 实时通信
- ✅ 游戏状态管理

### Week 3: UI 优化
- ✅ shadcn/ui AI Elements 集成
- ✅ 专业聊天界面
- ✅ 打字机效果
- ✅ 错误处理与重试
- ✅ Logger 系统升级
- ✅ Kimi K2 Thinking 模型集成
- ✅ 增强 Checkpoint 模式（工具调用可视化）

---

## 🚀 进行中 (Week 4)

### 优先级 1: 功能验证 (Day 1-2)

#### 任务 1.1: 测试增强 Checkpoint 模式
**状态**: 待测试
**文件**: `dm_agent_langchain.py:340-386`

**测试项**:
- [ ] 工具调用事件捕获（get_player_state, add_item, roll_check）
- [ ] 工具返回结果显示
- [ ] 思考过程可视化（Kimi K2）
- [ ] 对话记忆功能
- [ ] 前端 TaskProgress 组件响应

**验收标准**:
```
输入: "查看我的状态"
预期:
✅ TaskProgress 显示 "工具调用: get_player_state"
✅ 状态从 in_progress → completed
✅ DM 正确描述玩家状态
```

**文档**: `docs/troubleshooting/ENHANCED_CHECKPOINT_TESTING.md`

#### 任务 1.2: 验证 Kimi K2 思考过程
**状态**: 待验证
**前提**: 确认 `.env` 中 `DEFAULT_MODEL=moonshotai/kimi-k2-thinking`

**测试项**:
- [ ] `<thinking>` 标记检测
- [ ] ThinkingProcess 组件显示
- [ ] 思考步骤折叠/展开
- [ ] 思考时长统计

**验收标准**:
```
输入: "这个房间有什么可疑之处？"
预期:
✅ ThinkingProcess 组件出现
✅ 显示思考步骤
✅ 思考完成后自动隐藏
✅ DM 给出推理结果
```

---

### 优先级 2: UI/UX 增强 (Day 3-4)

#### 任务 2.1: 工具调用参数可视化
**目标**: 在 TaskProgress 中显示工具参数

**实现**:
```typescript
// TaskProgress.tsx
{task.type === 'tool_call' && task.toolInput && (
  <details className="mt-2">
    <summary className="text-xs text-muted-foreground cursor-pointer">
      查看参数
    </summary>
    <pre className="text-xs mt-1 p-2 bg-muted rounded">
      {JSON.stringify(task.toolInput, null, 2)}
    </pre>
  </details>
)}
```

**验收**: 点击工具调用任务可展开查看完整参数

#### 任务 2.2: 流式输出控制增强
**目标**: 优化暂停/继续/停止按钮

**改进点**:
- 添加快捷键（Space: 暂停/继续, Esc: 停止）
- 显示流式进度（已生成字符数）
- 添加"跳过动画"选项（直接显示完整文本）

#### 任务 2.3: 响应式布局优化
**目标**: 移动端友好

**测试设备**:
- iPhone (375px)
- iPad (768px)
- Desktop (1920px)

**改进**:
- 消息气泡宽度自适应
- ThinkingProcess 在移动端默认折叠
- TaskProgress 横向滚动支持

---

### 优先级 3: 游戏功能完善 (Day 5-6)

#### 任务 3.1: 任务系统增强
**当前状态**: 基础任务工具已实现 (create_quest, get_quests, etc.)
**缺失**: 前端任务面板

**实现**:
1. 创建 `QuestPanel.tsx` 组件
2. 显示当前任务列表
3. 任务目标进度条
4. 任务完成动画

**数据流**:
```
DM Agent → create_quest → game_state.quests → WebSocket → QuestPanel
```

#### 任务 3.2: NPC 关系可视化
**目标**: 显示 NPC 关系图谱

**实现**:
1. 创建 `RelationshipGraph.tsx`
2. 使用 D3.js 或 React Flow
3. 显示 NPC 节点 + 关系边
4. 关系值颜色编码（好感/敌意）

**数据源**: `game_state.characters[].relationships`

#### 任务 3.3: 场景描述优化
**目标**: 更丰富的场景展示

**新增工具**:
```python
@tool
def describe_scene(
    location: str,
    focus: str = "general"  # general, visual, audio, interactive
) -> Dict[str, str]:
    """
    生成场景描述（视觉、听觉、互动元素）

    Returns:
        {
            "visual": "场景视觉描述",
            "audio": "环境音效描述",
            "interactive": "可交互对象列表"
        }
    """
```

**前端展示**: 分区域显示场景要素

---

### 优先级 4: 性能优化 (Day 7)

#### 任务 4.1: Checkpoint 数据库性能
**问题**: 每次查询都读取整个对话历史

**优化**:
- 添加索引（thread_id, checkpoint_id）
- 限制加载消息数量（最近20条）
- 实现分页加载历史消息

**测试**: 100轮对话性能压测

#### 任务 4.2: WebSocket 连接池
**问题**: 并发连接时可能超载

**优化**:
- 限制单用户最大连接数
- 添加连接队列
- 心跳优化（减少频率）

**指标**: 支持 100 并发 WebSocket 连接

#### 任务 4.3: 前端状态管理优化
**问题**: DmInterface 组件状态过多

**重构**:
- 使用 Zustand 创建 `gameStore`
- 分离消息、任务、思考过程到不同 slice
- 减少不必要的 re-render

---

## 📋 积压功能 (Backlog)

### 游戏机制
- [ ] 战斗系统（回合制 vs 实时）
- [ ] 物品装备系统
- [ ] 技能树
- [ ] 多人协作模式

### AI 增强
- [ ] 多模态支持（图片生成场景）
- [ ] 语音输入/输出
- [ ] 情感分析（调整 DM 语气）
- [ ] 自定义 DM 人格

### 世界生成
- [ ] 程序化地牢生成
- [ ] 动态事件系统
- [ ] 天气与时间流逝
- [ ] 经济系统（商店、货币）

### 社交功能
- [ ] 分享冒险记录
- [ ] 冒险模板市场
- [ ] 玩家成就系统
- [ ] 排行榜

---

## 🎯 Week 4 里程碑

**截止日期**: 2025-11-17
**核心目标**: 完整的 TRPG 游戏体验

**必须完成**:
1. ✅ 工具调用和思考过程完全可见
2. ✅ 任务系统前端展示
3. ✅ NPC 关系可视化
4. ✅ 性能压测通过（100 并发）

**次要目标**:
- 场景描述增强
- 移动端适配
- 多语言支持

---

## 📊 技术债务

### 高优先级
1. **类型安全**: 添加完整的 TypeScript 类型定义
2. **错误边界**: 前端添加 Error Boundary 组件
3. **单元测试**: 覆盖率提升到 60%+

### 中优先级
1. **API 文档**: 使用 OpenAPI/Swagger 自动生成
2. **Docker 化**: 添加 Dockerfile 和 docker-compose
3. **CI/CD**: GitHub Actions 自动测试和部署

### 低优先级
1. **国际化**: i18n 支持
2. **主题切换**: 自定义主题配色
3. **无障碍**: ARIA 标签和键盘导航

---

## 🔄 迭代计划

### Sprint 1 (本周)
**主题**: 功能验证与 UI 完善

- Day 1-2: 测试增强 Checkpoint 模式
- Day 3-4: UI/UX 增强
- Day 5-6: 游戏功能完善
- Day 7: 性能优化

### Sprint 2 (下周)
**主题**: 游戏机制深化

- 战斗系统设计
- 物品装备实现
- 技能树原型

### Sprint 3 (两周后)
**主题**: AI 能力提升

- 多模态集成
- 语音支持
- 情感分析

---

## 📈 成功指标

### 技术指标
- [ ] API 响应时间 < 500ms (P95)
- [ ] WebSocket 消息延迟 < 100ms
- [ ] 前端首屏加载 < 2s
- [ ] 单元测试覆盖率 > 60%

### 用户体验
- [ ] 工具调用可见率 100%
- [ ] 思考过程可见率 100% (Kimi K2)
- [ ] 错误恢复成功率 > 95%
- [ ] 对话记忆准确率 > 99%

### 游戏性
- [ ] 平均对话轮次 > 10
- [ ] 任务完成率 > 70%
- [ ] NPC 互动频率 > 3次/冒险
- [ ] 用户满意度 > 4.5/5

---

## 🛠 开发工具

### 新增工具
```bash
# 快速测试工具调用
./scripts/dev/test_tool_calls.sh

# 性能基准测试
./scripts/dev/benchmark.sh

# 生成 API 文档
./scripts/dev/generate_docs.sh
```

### 调试技巧
```bash
# 实时查看 DM Agent 日志
tail -f logs/app.log | grep -E "(检测到工具|思考过程)"

# 监控 WebSocket 连接
wscat -c ws://localhost:8000/api/dm/ws/test

# 查看 Checkpoint 数据
sqlite3 data/checkpoints/dm.db "SELECT * FROM checkpoints"
```

---

**更新时间**: 2025-11-10 22:40
**负责人**: Claude Code
**下次评审**: 2025-11-11
