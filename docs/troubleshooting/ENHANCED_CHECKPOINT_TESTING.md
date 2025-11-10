# 增强 Checkpoint 模式测试指南

**创建时间**: 2025-11-10 22:15
**Commit**: `8ca609b`
**状态**: ✅ 已实施，待测试

---

## 📝 改动摘要

增强了 LangGraph Checkpoint 模式，使其能够：
1. **捕获工具调用事件** - 从 AIMessage.tool_calls 中提取
2. **捕获工具返回结果** - 从 ToolMessage 中提取
3. **检测思考过程** - 识别 `<thinking>`, `思考：` 等标记

**核心优势**: 保留 Checkpoint 的自动对话记忆，同时获得完整的事件流可见性。

---

## 🧪 测试步骤

### 1. 确认服务运行

```bash
# 检查后端状态
curl http://localhost:8000/api/dm/health

# 预期输出
{"status":"ok","dm_agent_initialized":true}
```

### 2. 访问游戏界面

打开浏览器访问:
```
http://localhost:3000/game/play
```

### 3. 测试工具调用可见性

**测试用例 1**: 获取玩家状态
```
输入: "查看我的状态"
预期:
✅ TaskProgress 组件显示 "工具调用: get_player_state"
✅ 状态从 "in_progress" 变为 "completed"
✅ DM 回复显示玩家的 HP、物品等信息
```

**测试用例 2**: 添加物品
```
输入: "我找到了一把剑"
预期:
✅ TaskProgress 显示 "工具调用: add_item"
✅ 工具参数显示 {"item_name": "剑", ...}
✅ DM 确认物品已添加到背包
```

**测试用例 3**: 投掷检定
```
输入: "我尝试破解这个机关(力量检定)"
预期:
✅ TaskProgress 显示 "工具调用: roll_check"
✅ 显示骰子结果
✅ DM 根据检定结果描述成功或失败
```

### 4. 测试思考过程可见性

**前提条件**: 使用支持思考标记的模型（如 Kimi K2）

```
输入: "这个房间有什么可疑之处？"
预期:
✅ ThinkingProcess 组件显示
✅ 显示 "思考步骤 1", "思考步骤 2" 等
✅ 思考完成后组件消失
✅ DM 给出分析结果
```

### 5. 测试对话记忆

```
第1轮输入: "我的名字是张三"
第2轮输入: "我叫什么名字？"
预期:
✅ DM 回复 "你是张三"
✅ 证明 Checkpoint 记忆功能正常
```

---

## 🐛 已知问题检查

### 问题 1: JSON 解析错误
**症状**:
```
[系统错误] 无法处理你的行动。请重试。
错误: 无法解析 JSON 响应: Unterminated string starting at: line 10 column 9
```

**原因**: LLM 返回的工具参数 JSON 格式不完整

**解决**:
- 点击前端的"重试"按钮
- 或切换到更稳定的模型（DeepSeek V3.1）

### 问题 2: 工具调用不显示
**症状**: TaskProgress 组件始终为空

**检查**:
1. 打开浏览器控制台
2. 查看 WebSocket 消息是否包含 `{"type": "tool_call"}`
3. 如果没有，检查后端日志:
   ```bash
   tail -f logs/app.log | grep "检测到工具调用"
   ```

**预期日志**:
```
[agents.dm_agent_langchain] INFO - 🔧 检测到工具调用: get_player_state
```

### 问题 3: 思考过程不显示
**症状**: ThinkingProcess 组件始终为空

**原因**: 当前模型不输出思考标记

**解决**:
1. 检查 `.env` 中的 `DEFAULT_MODEL`
2. 切换到支持思考过程的模型:
   ```bash
   DEFAULT_MODEL=moonshotai/kimi-k2-thinking
   ```
3. 重启后端

---

## 📊 测试检查清单

- [ ] 后端服务健康检查通过
- [ ] 前端页面可访问
- [ ] 工具调用可见（至少3种工具）
- [ ] 工具返回结果显示正确
- [ ] 思考过程可见（如果模型支持）
- [ ] 对话历史记忆正常
- [ ] 错误重试功能正常
- [ ] WebSocket 连接稳定

---

## 🔍 调试技巧

### 查看后端事件流

```bash
# 实时查看 DM Agent 日志
tail -f logs/app.log | grep -E "(检测到工具|思考过程|叙事片段)"
```

### 查看前端 WebSocket 消息

在浏览器控制台执行:
```javascript
// 监听所有 WebSocket 消息
const ws = new WebSocket('ws://localhost:8000/api/dm/ws/test-session');
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('[WS Message]', data.type, data);
};
```

### 检查 Checkpoint 数据库

```bash
sqlite3 data/checkpoints/dm.db "SELECT * FROM checkpoints ORDER BY checkpoint_id DESC LIMIT 5;"
```

---

## ✅ 成功标准

测试通过的标准:

1. **工具调用可见性**: 至少能看到 3 种不同工具的调用过程
2. **思考过程显示**: 如果模型支持，能看到思考步骤
3. **对话记忆**: 连续对话能正确引用之前的内容
4. **错误恢复**: JSON 错误后可以重试成功
5. **UI 响应**: TaskProgress 和 ThinkingProcess 组件动画流畅

---

## 🎯 下一步

测试通过后，可以考虑:

1. **性能优化**: 减少 Checkpoint 数据库查询
2. **UI 增强**: 添加工具参数展示动画
3. **模型调优**: 优化 System Prompt 以获得更好的思考标记输出
4. **文档完善**: 根据测试结果补充边界情况处理

---

**更新时间**: 2025-11-10 22:15
**作者**: Claude Code
**版本**: 1.0
**相关 Commit**: `8ca609b`
