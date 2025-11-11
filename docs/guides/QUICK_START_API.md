# Phase 2 游戏 API 快速启动指南
<!-- moved to docs/guides on 2025-11-11 -->

本指南帮助你快速启动和测试新实现的游戏 API。

---

## 1. 启动后端服务

```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动后端（包含所有新 API）
cd web/backend
uvicorn main:app --reload --port 8000
```

**预期输出**:
```
✅ LLM 后端已初始化 (类型: litellm_proxy)
✅ 数据库已连接 (路径: .../data/sqlite/novel.db)
✅ 游戏引擎已初始化
✅ 世界管理服务已初始化
✅ DM Agent 已初始化
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 2. 访问 API 文档

启动后打开浏览器访问：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

你将看到以下新增的 API 分组：
- `game` - 游戏相关 API（存档、任务、NPC）
- `dm` - DM Agent API

---

## 3. 测试基础功能

### 3.1 健康检查

```bash
curl http://localhost:8000/api/dm/health
```

**预期响应**:
```json
{
  "status": "ok",
  "dm_agent_initialized": true
}
```

---

### 3.2 创建任务

```bash
curl -X POST http://localhost:8000/api/game/quests \
  -H "Content-Type: application/json" \
  -d '{
    "title": "新手试炼",
    "description": "完成基础训练",
    "objectives": [
      {
        "id": "obj_1",
        "description": "击败训练假人",
        "current": 0,
        "required": 3
      }
    ],
    "rewards": {
      "exp": 50,
      "gold": 20
    }
  }'
```

---

### 3.3 获取任务列表

```bash
curl http://localhost:8000/api/game/quests
```

---

### 3.4 更新任务进度

```bash
# 假设任务 ID 为 quest_1234
curl -X PUT http://localhost:8000/api/game/quests/quest_1234/progress \
  -H "Content-Type: application/json" \
  -d '{
    "objective_id": "obj_1",
    "amount": 1
  }'
```

---

### 3.5 创建 NPC

```bash
curl -X POST http://localhost:8000/api/game/npcs \
  -H "Content-Type: application/json" \
  -d '{
    "npc_id": "npc_guard",
    "name": "守卫队长",
    "role": "守卫",
    "location": "城门",
    "personality_traits": ["严肃", "尽职"]
  }'
```

---

### 3.6 获取 NPC 列表

```bash
curl "http://localhost:8000/api/game/npcs?location=城门"
```

---

### 3.7 DM 处理行动

```bash
curl -X POST http://localhost:8000/api/dm/action \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_player",
    "player_action": "我查看周围的环境",
    "game_state": {
      "player": {
        "hp": 100,
        "max_hp": 100,
        "location": "起始村庄"
      },
      "world": {
        "current_location": "起始村庄",
        "theme": "奇幻世界"
      },
      "turn_number": 1
    }
  }'
```

---

## 4. WebSocket 测试

### 使用 websocat（命令行工具）

```bash
# 安装 websocat（如果还没有）
# macOS: brew install websocat
# Linux: cargo install websocat

# 连接到 DM WebSocket
websocat ws://localhost:8000/api/dm/ws/test_player
```

然后发送消息：
```json
{
  "type": "action",
  "player_action": "我向北走",
  "game_state": {
    "player": {"hp": 100, "location": "村庄"},
    "world": {"current_location": "村庄"},
    "turn_number": 1
  }
}
```

---

### 使用 Python

创建 `test_websocket.py`:

```python
import asyncio
import websockets
import json

async def test_dm_websocket():
    uri = "ws://localhost:8000/api/dm/ws/test_player"

    async with websockets.connect(uri) as websocket:
        # 发送玩家行动
        message = {
            "type": "action",
            "player_action": "我拔出剑，准备迎战",
            "game_state": {
                "player": {"hp": 100, "location": "森林"},
                "world": {"current_location": "森林"},
                "turn_number": 5
            }
        }

        await websocket.send(json.dumps(message))
        print("已发送:", message["player_action"])

        # 接收所有响应
        async for response in websocket:
            data = json.loads(response)
            print(f"\n[{data['type']}]")

            if data['type'] == 'narration_chunk':
                print(data['data']['text'], end='', flush=True)
            elif data['type'] == 'tool_call':
                print(f"工具调用: {data['data']['tool']}")
            elif data['type'] == 'complete':
                print("\n完成，回合:", data['data']['turn'])
                break

asyncio.run(test_dm_websocket())
```

运行：
```bash
python test_websocket.py
```

---

### 使用 JavaScript（浏览器）

创建 `test_websocket.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>DM WebSocket 测试</title>
</head>
<body>
    <h1>DM Agent WebSocket 测试</h1>
    <input type="text" id="action" placeholder="输入行动" style="width: 300px;">
    <button onclick="sendAction()">发送</button>
    <div id="output" style="margin-top: 20px; white-space: pre-wrap;"></div>

    <script>
        const ws = new WebSocket('ws://localhost:8000/api/dm/ws/browser_player');
        const output = document.getElementById('output');

        ws.onopen = () => {
            output.textContent += '已连接到 DM Agent\n\n';
        };

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);

            if (data.type === 'narration_chunk') {
                output.textContent += data.data.text;
            } else if (data.type === 'tool_call') {
                output.textContent += `\n[工具调用: ${data.data.tool}]\n`;
            } else if (data.type === 'complete') {
                output.textContent += `\n\n--- 回合 ${data.data.turn} 完成 ---\n\n`;
            }
        };

        function sendAction() {
            const action = document.getElementById('action').value;
            const message = {
                type: 'action',
                player_action: action,
                game_state: {
                    player: { hp: 100, location: '村庄' },
                    world: { current_location: '村庄' },
                    turn_number: 1
                }
            };
            ws.send(JSON.stringify(message));
            output.textContent += `你: ${action}\n\n`;
            document.getElementById('action').value = '';
        }
    </script>
</body>
</html>
```

在浏览器中打开此文件进行测试。

---

## 5. 存档系统测试

### 5.1 保存游戏

```bash
curl -X POST http://localhost:8000/api/game/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "slot_id": 1,
    "save_name": "测试存档",
    "game_state": {
      "player": {"hp": 80, "max_hp": 100},
      "world": {"current_location": "森林"},
      "turn_number": 10
    }
  }'
```

---

### 5.2 获取存档列表

```bash
curl http://localhost:8000/api/game/saves/test_user
```

---

### 5.3 加载存档

```bash
# 假设存档 ID 为 1
curl http://localhost:8000/api/game/save/1
```

---

### 5.4 删除存档

```bash
curl -X DELETE http://localhost:8000/api/game/save/1
```

---

## 6. 完整工作流示例

下面是一个完整的游戏流程测试：

```bash
#!/bin/bash

BASE_URL="http://localhost:8000/api"

echo "=== 1. 创建任务 ==="
curl -X POST $BASE_URL/game/quests \
  -H "Content-Type: application/json" \
  -d '{
    "title": "清理森林",
    "description": "消灭森林中的狼群",
    "objectives": [{"id": "kill_wolves", "description": "消灭狼", "required": 5}],
    "rewards": {"exp": 100, "gold": 50}
  }'

echo -e "\n\n=== 2. 创建 NPC ==="
curl -X POST $BASE_URL/game/npcs \
  -H "Content-Type: application/json" \
  -d '{
    "npc_id": "village_elder",
    "name": "村长",
    "role": "村庄领导者",
    "location": "村庄"
  }'

echo -e "\n\n=== 3. DM 处理行动 ==="
curl -X POST $BASE_URL/dm/action \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "test_flow",
    "player_action": "我接受了村长的任务，前往森林",
    "game_state": {
      "player": {"hp": 100, "location": "村庄"},
      "world": {"current_location": "村庄"},
      "turn_number": 1
    }
  }'

echo -e "\n\n=== 4. 保存游戏 ==="
curl -X POST $BASE_URL/game/save \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "slot_id": 1,
    "save_name": "出发前往森林",
    "game_state": {
      "player": {"hp": 100, "location": "森林入口"},
      "world": {"current_location": "森林入口"},
      "turn_number": 2
    }
  }'

echo -e "\n\n=== 测试完成 ==="
```

保存为 `test_flow.sh`，然后运行：
```bash
chmod +x test_flow.sh
./test_flow.sh
```

---

## 7. 常见问题

### Q1: 端口被占用

**问题**: `Address already in use`

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>
```

---

### Q2: 数据库初始化

**问题**: 数据库表不存在

**解决**:
```bash
# 初始化数据库
python scripts/init_db.py

# 或手动创建
sqlite3 data/sqlite/novel.db < database/schema/core.sql
```

---

### Q3: DM Agent 未初始化

**问题**: `DM Agent 未初始化`

**解决**:
- 检查启动日志中是否有 `✅ DM Agent 已初始化`
- 确认 `web/backend/agents/` 目录下有所有必需文件
- 检查导入错误

---

### Q4: WebSocket 连接失败

**问题**: WebSocket 无法连接

**解决**:
- 确认后端已启动
- 检查防火墙设置
- 使用 `ws://` 而非 `wss://`（本地开发）

---

## 8. 下一步

完成测试后，你可以：

1. **集成到前端**: 在 Next.js 中创建 API 客户端
2. **添加认证**: 实现 JWT 认证
3. **优化性能**: 添加缓存和速率限制
4. **扩展功能**: 基于 API 构建游戏 UI

---

## 相关文档

- [API 端点文档](../implementation/PHASE2_API_ENDPOINTS.md)
- [实现总结](../implementation/API_IMPLEMENTATION_SUMMARY.md)
- [技术实现计划](docs/TECHNICAL_IMPLEMENTATION_PLAN.md)
- [Claude Agent SDK 集成指南](docs/implementation/CLAUDE_AGENT_SDK_IMPLEMENTATION.md)

---

## 支持

如有问题，请查看：
- 后端日志: 终端输出
- API 文档: http://localhost:8000/docs
- 错误响应: 检查 `detail` 字段
