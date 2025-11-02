# 游戏系统测试指南

## 🚀 快速开始

### 1. 启动服务

```bash
# 方法1: 使用一键启动脚本
./start_all_with_agent.sh

# 方法2: 手动启动
# 终端1 - 后端
cd web/backend
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8000

# 终端2 - 前端
cd web/frontend
npm run dev
```

### 2. 访问测试页面

打开浏览器访问: **http://localhost:3000/game**

---

## 🎮 测试流程

### Step 1: 初始化游戏

1. 点击"**开始游戏**"按钮
2. 应该看到初始化旁白：
   ```
   欢迎来到这个充满冒险的世界！你站在广场中央，前方是未知的旅程...
   ```
3. 右侧栏应显示：
   - 生命: 100/100
   - 体力: 100/100
   - 位置: start
   - 金钱: 50

### Step 2: 测试玩家行动

输入以下命令测试不同功能：

#### 场景描述
```
环顾四周
```
**预期**: 详细的场景描述，可能包含环境细节

#### 物品拾取
```
拾起地上的剑
```
**预期**:
- 旁白描述拾取过程
- 右侧"背包"区显示新物品
- 可能触发`add_item`工具

#### 移动
```
向北走
```
**预期**:
- 位置变更
- 右侧"位置"更新
- 触发`set_location`工具

#### 检定测试
```
尝试潜行穿过守卫
```
**预期**:
- 触发`roll_check`工具
- 旁白说明成功/失败
- 可能影响状态

### Step 3: 测试存档功能

1. 进行几个回合后，点击"**保存**"
2. 刷新页面
3. 点击"**读取**"
4. 游戏状态应恢复

### Step 4: 测试导出

1. 点击"**导出**"按钮
2. 应下载JSON文件
3. 打开文件查看完整状态

---

## 🔍 验证点

### 前端验证

- [ ] 初始化成功，显示欢迎旁白
- [ ] 玩家输入能正常发送
- [ ] 旁白流畅显示
- [ ] 状态栏实时更新
- [ ] 建议chips可点击
- [ ] 存档/读档功能正常

### 后端验证

查看后端日志（如果使用脚本启动）:
```bash
tail -f logs/backend.log
```

应看到：
```
✅ LLM 客户端已初始化
✅ 数据库已连接
✅ 游戏引擎已初始化
INFO: ... POST /api/game/init ... 200 OK
INFO: ... POST /api/game/turn ... 200 OK
```

### LLM输出验证

每次玩家行动应返回JSON格式：
```json
{
  "narration": "你的旁白文本...",
  "tool_calls": [
    {"name": "add_item", "arguments": {...}}
  ],
  "hints": ["提示1", "提示2"],
  "suggestions": ["建议1", "建议2"]
}
```

---

## 🐛 常见问题

### 问题1: 后端500错误

**症状**: 前端显示"API请求失败: 500"

**排查**:
```bash
# 查看后端日志
tail -20 logs/backend.log

# 或手动运行后端查看错误
cd web/backend
source ../../.venv/bin/activate
uvicorn main:app --reload --port 8000
```

**可能原因**:
- LiteLLM配置错误
- OPENROUTER_API_KEY未设置
- 模型调用失败

### 问题2: 前端TypeError

**症状**: 浏览器控制台报类型错误

**排查**:
1. 打开浏览器开发者工具 (F12)
2. 查看Console标签
3. 检查Network标签的请求/响应

**可能原因**:
- gameState包含无法序列化的对象
- API响应格式不匹配

### 问题3: 工具调用失败

**症状**: 旁白正常，但状态不更新

**可能原因**:
- LLM未调用工具（检查prompt）
- 工具参数格式错误
- 后端工具执行异常

**验证**:
```python
# 运行测试脚本
python3 test_game_turn.py
```

---

## 📊 性能测试

### 响应时间

正常情况下：
- 初始化: < 1秒
- 简单回合: 3-8秒（取决于LLM）
- 复杂回合: 8-15秒

### token使用

每回合大约消耗：
- Prompt: 500-1500 tokens
- Response: 200-500 tokens

成本估算（DeepSeek V3）:
- 每回合 ~$0.001 USD

---

## 🧪 单元测试

### 测试工具系统

```bash
cd web/backend
python3 -c "
from game_tools import GameTools, GameState, PlayerState, WorldState, GameMap
state = GameState(
    version='1.0.0',
    player=PlayerState(),
    world=WorldState(),
    map=GameMap(nodes=[], edges=[], currentNodeId='start'),
    quests=[],
    log=[]
)
tools = GameTools(state)
print('✅ GameTools初始化成功')
print(f'玩家HP: {tools.get_player_state().hp}')
result = tools.roll_check(type='perception', dc=10)
print(f'检定结果: {result}')
"
```

### 测试游戏引擎

```bash
python3 test_game_turn.py
```

---

## ✅ 测试清单

完整测试前请确认：

**环境准备**:
- [ ] `.env`文件已配置`OPENROUTER_API_KEY`
- [ ] 虚拟环境已激活
- [ ] 依赖已安装(`pip install -r requirements.txt`)
- [ ] 前端依赖已安装(`npm install`)

**服务运行**:
- [ ] 后端运行在8000端口
- [ ] 前端运行在3000端口
- [ ] `/health`端点返回OK

**核心功能**:
- [ ] 游戏初始化
- [ ] 玩家输入处理
- [ ] 状态更新
- [ ] 工具调用
- [ ] 存档/读档

**高级功能**:
- [ ] 流式输出（Phase 2）
- [ ] 任务系统（Phase 2）
- [ ] 地图显示（Phase 2）

---

## 📝 问题反馈

测试过程中遇到问题，请记录：

1. **复现步骤**
2. **预期行为**
3. **实际行为**
4. **错误信息**（后端日志/前端控制台）
5. **环境信息**（OS、浏览器、Node版本等）

---

**最后更新**: 2025-01-31
**测试版本**: Phase 1 - 核心协议
