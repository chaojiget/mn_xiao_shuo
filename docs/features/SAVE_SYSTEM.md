# 游戏存档系统

## 概述

完整的游戏存档管理系统，支持保存、加载、删除游戏进度。

## 功能特性

### 1. 存档槽位

- **10个手动存档槽位** (slot_id 1-10)
- **自动保存** (slot_id 0，每回合自动保存)
- 每个槽位独立存储完整游戏状态

### 2. 存档信息

每个存档包含：
- **基础信息**: 槽位ID、存档名称、创建/更新时间
- **游戏状态**: 完整的 GameState (玩家、世界、任务、地图等)
- **元数据**: 回合数、位置、等级、HP、游戏时长
- **截图** (可选): 保存时的游戏画面

### 3. 存档快照

- 每次手动保存时自动创建快照
- 支持回滚到特定回合
- 快照包含完整游戏状态

## 数据库表结构

### game_saves 表
```sql
CREATE TABLE game_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL DEFAULT 'default_user',
    slot_id INTEGER NOT NULL CHECK(slot_id >= 0 AND slot_id <= 10),
    save_name TEXT NOT NULL,
    game_state TEXT NOT NULL,           -- JSON格式
    metadata TEXT,                      -- JSON格式元数据
    screenshot_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, slot_id)
);
```

### save_snapshots 表
```sql
CREATE TABLE save_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    save_id INTEGER NOT NULL,
    turn_number INTEGER NOT NULL,
    snapshot_data TEXT NOT NULL,        -- JSON格式
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (save_id) REFERENCES game_saves(id) ON DELETE CASCADE
);
```

### auto_saves 表
```sql
CREATE TABLE auto_saves (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    game_state TEXT NOT NULL,           -- JSON格式
    turn_number INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## API 端点

### 后端 API (FastAPI)

所有端点位于 `/api/game/` 下：

#### 保存游戏
```http
POST /api/game/save
Content-Type: application/json

{
  "user_id": "default_user",
  "slot_id": 1,
  "save_name": "第10回合 - 森林探险",
  "game_state": { ... }
}

Response:
{
  "success": true,
  "save_id": 123,
  "message": "游戏保存成功"
}
```

#### 获取存档列表
```http
GET /api/game/saves/{user_id}

Response:
{
  "success": true,
  "saves": [
    {
      "save_id": 123,
      "slot_id": 1,
      "save_name": "第10回合 - 森林探险",
      "metadata": {
        "turn_number": 10,
        "location": "迷雾森林",
        "level": 5,
        "hp": 80,
        "max_hp": 100
      },
      "created_at": "2025-11-06T10:30:00",
      "updated_at": "2025-11-06T12:45:00"
    }
  ]
}
```

#### 加载存档
```http
GET /api/game/save/{save_id}

Response:
{
  "success": true,
  "game_state": { ... },
  "metadata": { ... },
  "save_info": {
    "save_id": 123,
    "slot_id": 1,
    "save_name": "第10回合 - 森林探险",
    "created_at": "2025-11-06T10:30:00"
  }
}
```

#### 删除存档
```http
DELETE /api/game/save/{save_id}

Response:
{
  "success": true,
  "message": "存档已删除"
}
```

#### 获取快照列表
```http
GET /api/game/save/{save_id}/snapshots

Response:
{
  "success": true,
  "snapshots": [
    {
      "snapshot_id": 456,
      "turn_number": 10,
      "created_at": "2025-11-06T12:45:00"
    }
  ]
}
```

#### 加载快照
```http
GET /api/game/snapshot/{snapshot_id}

Response:
{
  "success": true,
  "game_state": { ... }
}
```

#### 获取最新自动保存
```http
GET /api/game/auto-save/{user_id}

Response:
{
  "success": true,
  "auto_save_id": 789,
  "game_state": { ... },
  "turn_number": 15,
  "created_at": "2025-11-06T13:00:00"
}
```

## 前端组件

### 1. 存档列表页面

**位置**: `web/frontend/app/saves/page.tsx`

**功能**:
- 展示所有存档（网格布局）
- 显示存档元数据（位置、HP、回合数、游戏时长）
- 加载存档到游戏
- 删除存档（带确认对话框）
- 槽位使用提示（10个槽位已满时提示）

**路由**: `/saves`

### 2. SaveGameDialog 组件

**位置**: `web/frontend/components/game/SaveGameDialog.tsx`

**功能**:
- 选择存档槽位（1-10）
- 输入存档名称
- 预览当前游戏状态（位置、回合、HP）
- 自动生成默认存档名称

**使用示例**:
```tsx
import { SaveGameDialog } from '@/components/game/SaveGameDialog'

<SaveGameDialog
  gameState={gameState}
  onSaveSuccess={() => {
    toast({ title: "保存成功" })
  }}
/>
```

### 3. API 客户端方法

**位置**: `web/frontend/lib/api-client.ts`

新增方法：
- `apiClient.saveGame()`
- `apiClient.getSaves()`
- `apiClient.loadSave()`
- `apiClient.deleteSave()`
- `apiClient.getSaveSnapshots()`
- `apiClient.loadSnapshot()`

## 使用流程

### 保存游戏

1. 在游戏页面点击"保存"按钮
2. 弹出 SaveGameDialog
3. 选择存档槽位（1-10）
4. 输入存档名称（可留空使用默认名称）
5. 点击"保存"
6. 后端创建存档并创建快照

### 加载存档

#### 方式1：从存档列表页
1. 访问 `/saves` 页面
2. 浏览所有存档
3. 点击"加载"按钮
4. 自动跳转到游戏页面并恢复进度

#### 方式2：从游戏页面
1. 点击"存档管理"按钮
2. 跳转到 `/saves` 页面
3. 选择存档加载

### 自动保存

游戏每回合自动保存到 `auto_saves` 表：
- 游戏启动时自动检测最新自动保存
- 如果存在，恢复进度
- 如果不存在或用户选择"重新开始"，初始化新游戏

## UI 设计

### 存档列表页

```
┌────────────────────────────────────────┐
│  ← 游戏存档                 9/10 槽位   │
├────────────────────────────────────────┤
│  ┌──────┐  ┌──────┐  ┌──────┐         │
│  │存档1 │  │存档2 │  │存档3 │         │
│  │截图  │  │截图  │  │截图  │         │
│  │第10回│  │第15回│  │第20回│         │
│  │森林  │  │城堡  │  │地牢  │         │
│  │加载 删│  │加载 删│  │加载 删│       │
│  └──────┘  └──────┘  └──────┘         │
└────────────────────────────────────────┘
```

### SaveGameDialog

```
┌──────────────────────────┐
│  保存游戏           ✕   │
├──────────────────────────┤
│  存档槽位: [选择槽位 ▼] │
│  存档名称: [__________ ] │
│                          │
│  当前状态:               │
│  位置: 迷雾森林          │
│  回合: 第10回合          │
│  HP: 80/100             │
│                          │
│      [取消]  [保存]      │
└──────────────────────────┘
```

## 主页入口

主页新增"存档管理"卡片：

```tsx
<Card onClick={() => router.push("/saves")}>
  <CardContent>
    <Save className="w-8 h-8" />
    <h3>存档管理</h3>
    <p>查看和管理游戏存档，加载之前的冒险进度</p>
  </CardContent>
</Card>
```

## 文件清单

### 新增文件
- `web/frontend/app/saves/page.tsx` - 存档列表页面
- `web/frontend/components/game/SaveGameDialog.tsx` - 保存对话框
- `docs/features/SAVE_SYSTEM.md` - 本文档

### 修改文件
- `web/frontend/lib/api-client.ts` - 添加存档API方法
- `web/frontend/app/page.tsx` - 添加存档管理入口
- `web/frontend/app/game/play/page.tsx` - 集成SaveGameDialog

### 已存在的后端文件
- `web/backend/services/save_service.py` - 存档服务逻辑
- `web/backend/api/game_api.py` - 存档API端点
- `database/schema/core.sql` - 数据库表定义

## 测试清单

### 功能测试

- [ ] 保存游戏到不同槽位
- [ ] 加载存档并恢复游戏状态
- [ ] 删除存档
- [ ] 覆盖已存在的存档
- [ ] 槽位已满提示
- [ ] 自动保存工作正常
- [ ] 快照创建正常

### UI 测试

- [ ] 存档列表正确显示
- [ ] SaveGameDialog 交互流畅
- [ ] 元数据显示正确（HP、位置、回合数）
- [ ] 响应式布局（手机/平板/桌面）
- [ ] 加载状态显示正常
- [ ] 错误提示友好

### 边界测试

- [ ] 数据库不存在时的错误处理
- [ ] 网络错误时的重试机制
- [ ] 无效的 save_id 处理
- [ ] 空存档列表显示
- [ ] 槽位范围验证（1-10）

## 未来改进

### 短期
- [ ] 添加存档截图功能
- [ ] 支持存档导出/导入（JSON文件）
- [ ] 添加存档搜索和过滤
- [ ] 显示存档大小

### 长期
- [ ] 云端存档同步
- [ ] 多设备存档共享
- [ ] 存档版本控制（Git-style）
- [ ] 存档对比工具
- [ ] 成就系统集成

## 相关文档

- [游戏引擎文档](./GAME_ENGINE.md)
- [数据库Schema](../../database/schema/core.sql)
- [API文档](../operations/API_REFERENCE.md)
