# WorldPack到游戏UI端到端测试

## 测试目的
验证从WorldPack生成到游戏UI的完整流程

## 前置条件
1. 后端服务运行在 `http://localhost:8000`
2. 前端服务运行在 `http://localhost:3000`
3. 数据库中至少有一个已生成的世界

## 测试步骤

### 步骤1: 访问世界列表
1. 打开浏览器，访问 `http://localhost:3000/worlds`
2. **预期**: 看到世界列表，显示已生成的世界

### 步骤2: 查看世界详情
1. 点击任意一个世界卡片
2. **预期**: 跳转到世界详情页 `/worlds/[id]`
3. **验证**:
   - 看到世界标题、种子、基调、难度
   - 看到5个Tab: 概览、地点、NPC、任务、Lore
   - 右上角有"开始冒险"按钮

### 步骤3: 点击"开始冒险"
1. 点击右上角的"开始冒险"按钮
2. **预期**:
   - URL变为 `/game/play?worldId=world-xxx`
   - 显示"正在初始化游戏..."加载界面
   - 几秒后进入游戏界面

### 步骤4: 验证游戏状态
1. 游戏界面加载完成后
2. **验证以下内容**:

#### 4.1 开场白
- [ ] Toast通知显示定制的开场白
- [ ] 开场白包含世界标题
- [ ] 开场白符合世界基调（epic/dark/cozy/mystery/whimsical）
- [ ] 开场白提到起始地点名称

#### 4.2 游戏状态面板（左侧）
- [ ] 显示玩家HP（根据难度不同）
  - Story: 150/150
  - Normal: 100/100
  - Hard: 80/80
- [ ] 显示体力（与HP相同）
- [ ] 显示位置（应该是WorldPack的第一个地点）
- [ ] 显示金币数量（根据难度不同）

#### 4.3 DM界面（中间）
- [ ] 显示系统消息（开场白）
- [ ] 显示建议行动：
  - 环顾四周
  - 查看背包
  - 查看任务
  - 探索[起始地点名称]

#### 4.4 任务追踪（右侧上）
- [ ] 显示激活的主线任务
- [ ] 任务标题来自WorldPack
- [ ] 显示任务目标列表
- [ ] 显示其他未激活任务

#### 4.5 地图状态
打开浏览器控制台，检查 `gameState`:
```javascript
// 在控制台输入
JSON.parse(localStorage.getItem('game-store'))
```

验证:
- [ ] `map.nodes` 数量与WorldPack地点数相同
- [ ] `map.nodes[0].discovered === true`（第一个地点已发现）
- [ ] 其他地点 `discovered === false`
- [ ] `map.edges` 包含地点之间的连接
- [ ] `map.currentNodeId` 等于第一个地点ID

#### 4.6 元数据
在控制台继续检查:
- [ ] `metadata.worldPackId` 等于URL中的worldId
- [ ] `metadata.worldPackTitle` 等于世界标题
- [ ] `world.variables.world_tone` 等于世界基调
- [ ] `world.variables.world_difficulty` 等于世界难度

### 步骤5: 测试游戏交互
1. 在DM输入框中输入: "我环顾四周"
2. 发送消息
3. **预期**:
   - DM回复应该与WorldPack的内容相关
   - 可能提到起始地点的描述
   - 可能提到附近的POI
   - 可能提到附近的NPC

### 步骤6: 验证任务系统
1. 输入: "查看任务"
2. **预期**:
   - DM显示当前激活的主线任务
   - 任务内容来自WorldPack
   - 显示任务目标

### 步骤7: 验证地图探索
1. 输入: "我想探索其他地方"
2. **预期**:
   - DM提到可以前往的地点（基于edges连接）
   - 建议的地点来自WorldPack

## 对比测试

### A. 使用WorldPack初始化
URL: `/game/play?worldId=world-xxx`
- 应该加载WorldPack的地点、NPC、任务
- 开场白应该定制化
- 地图应该有多个地点（WorldPack中定义的）

### B. 不使用WorldPack初始化
URL: `/game/play`（无参数）
- 加载默认世界
- 使用通用开场白
- 地图只有基础地点

## 成功标准

所有以下条件必须满足：
- ✅ 从世界详情页点击"开始冒险"能正确跳转
- ✅ URL包含正确的worldId参数
- ✅ 游戏初始化使用WorldPack数据
- ✅ 开场白是定制化的（包含世界标题和起始地点）
- ✅ 地图包含WorldPack的所有地点
- ✅ 任务来自WorldPack
- ✅ 玩家初始属性根据难度设置
- ✅ 元数据正确记录WorldPack信息
- ✅ DM的回复与WorldPack内容相关

## 调试技巧

### 查看网络请求
1. 打开浏览器开发者工具 → Network
2. 筛选XHR/Fetch
3. 查看 `/api/game/init` 请求
4. 检查请求体是否包含 `worldId`
5. 检查响应是否包含正确的state数据

### 查看控制台日志
```javascript
// 应该看到这个日志
[GamePlay] 使用WorldPack初始化: world-xxx
```

### 检查游戏状态
```javascript
// 获取当前游戏状态
const store = JSON.parse(localStorage.getItem('game-store'))
console.log('Game State:', store.state.gameState)

// 检查地图
console.log('Map Nodes:', store.state.gameState.map.nodes)

// 检查任务
console.log('Quests:', store.state.gameState.quests)

// 检查元数据
console.log('Metadata:', store.state.gameState.metadata)
```

## 已知问题

无（所有问题已修复）

## 修复历史

**2025-11-06**:
- 修复了导入错误（NPC类不存在）
- 添加了缺失的数据模型字段
- 修复了对象访问方式
- 实现了URL参数传递worldId
- 修改了游戏页面支持worldId初始化

---

**测试版本**: 1.0
**最后更新**: 2025-11-06
**测试状态**: ✅ 通过
