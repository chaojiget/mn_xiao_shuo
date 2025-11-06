# WorldPack 快速上手指南

> 5分钟了解并使用 WorldPack 预生成世界系统
> 更新时间: 2025-11-06

## 📖 什么是 WorldPack?

WorldPack 是**预生成完整世界**的系统，一次性生成所有地点、NPC、任务、掉落表和遭遇表，适合结构化冒险和预设剧本。

**与世界脚手架的区别:**

| | 世界脚手架 | WorldPack |
|---|---|---|
| **路径** | `/world` | `/worlds` ⭐ |
| **生成方式** | 动态渐进式 | 一次性预生成 |
| **内容** | 区域、派系 | 完整世界包 |
| **适用场景** | 开放探索 | 预设剧本 |

## 🚀 快速开始

### 1. 启动服务

```bash
# 一键启动（推荐）
./scripts/start/start_all_with_agent.sh

# 或手动启动
cd web/backend && uv run uvicorn main:app --reload --port 8000
cd web/frontend && npm run dev
```

### 2. 访问世界管理页面

打开浏览器访问: **http://localhost:3000/worlds**

### 3. 生成新世界

1. 点击右上角 **"生成新世界"** 按钮
2. 填写表单:
   - **标题**: 世界名称（例如："暗影森林"）
   - **基调**: epic/dark/cozy/mystery/whimsical
   - **难度**: story/normal/hard
   - **地点数**: 5-50（推荐15）
   - **NPC数**: 3-30（推荐20）
   - **任务数**: 3-20（推荐8）
3. 点击 **"开始生成"**
4. 等待进度条完成（约40-70秒）
5. 自动跳转到世界详情页

### 4. 查看世界详情

世界详情页包含5个Tab:

**📊 概览** - 统计数据、世界信息
```
┌─────────────┬─────────────┬─────────────┐
│ 15 地点     │ 20 NPC      │ 8 任务      │
└─────────────┴─────────────┴─────────────┘

基调: dark | 难度: hard | 种子: 42
```

**🗺️ 地点** - 所有地点列表
```
迷雾森林 [forest]
坐标: (10, 20) | 3个POI | 2个NPC
━━━━━━━━━━━━━━━━━━━━━━━━━━
古老神殿 [ruins]
坐标: (25, 15) | 5个POI | 1个NPC
```

**👥 NPC** - 所有角色信息
```
神秘商人 [merchant]
位置: 广场
欲望: 收集稀有物品
秘密: 前盗贼头目
```

**📜 任务** - 主线和支线任务
```
【主线】寻找遗物
 ☑ 探索古老神殿
 ○ 解开谜题
 ○ 击败守护者
奖励: 100 exp, 50金币
```

**📖 Lore** - 世界设定百科

## 🛠️ 管理功能

### 校验世界

点击 **"校验世界"** 按钮检查:
- ✅ 引用完整性（NPC→地点）
- ✅ 任务依赖DAG无环
- ✅ 数据质量

结果示例:
```
✅ 世界校验通过！无错误。

或

⚠️ 发现 3 个问题
[error] NPC merchant_01 引用不存在的地点 unknown_loc
[warning] Quest quest_02 存在循环依赖
```

### 创建快照

点击 **"创建快照"** 保存版本:
```
输入标签: v1.0-初版
→ 保存成功，可随时回滚
```

### 发布世界

点击 **"发布"** 将世界设为可用状态。

## 📡 API使用

### 生成世界

```bash
curl -X POST http://localhost:8000/api/worlds/generate \
  -H "Content-Type: application/json" \
  -d '{
    "title": "暗影森林",
    "tone": "dark",
    "difficulty": "hard",
    "num_locations": 15,
    "num_npcs": 20,
    "num_quests": 10
  }'

# 返回
{
  "job_id": "job_abc123",
  "world_id": "world_xyz789",
  "status": "QUEUED"
}
```

### 查询生成状态

```bash
curl http://localhost:8000/api/worlds/world_xyz789/status

# 返回
{
  "phase": "NPCS",
  "progress": 0.375,
  "message": "正在生成NPC..."
}
```

### 获取世界详情

```bash
curl http://localhost:8000/api/worlds/world_xyz789

# 返回完整的WorldPack JSON
{
  "meta": {...},
  "locations": [...],
  "npcs": [...],
  "quests": [...],
  "loot_tables": [...],
  "encounter_tables": [...],
  "lore": {...}
}
```

### 校验世界

```bash
curl -X POST http://localhost:8000/api/worlds/world_xyz789/validate

# 返回
{
  "ok": true,
  "summary": {"total": 0, "errors": 0, "warnings": 0},
  "problems": []
}
```

### 语义搜索

```bash
curl "http://localhost:8000/api/worlds/world_xyz789/search?query=森林中的秘密&kind=lore&top_k=5"

# 返回相关的5条Lore
```

## 🎯 典型工作流

### 场景1: 创建一个中型暗黑冒险世界

```bash
1. 访问 /worlds
2. 点击 "生成新世界"
3. 配置:
   - 标题: "暗影深渊"
   - 基调: dark
   - 难度: hard
   - 地点: 15
   - NPC: 20
   - 任务: 10
4. 等待生成（约70秒）
5. 查看详情 → 校验 → 调整（如需）→ 发布
```

### 场景2: 快速生成测试世界

```bash
配置:
- 地点: 5
- NPC: 8
- 任务: 6
生成时间: 约40秒
```

### 场景3: 大型史诗世界

```bash
配置:
- 标题: "永恒帝国"
- 基调: epic
- 地点: 30
- NPC: 30
- 任务: 20
生成时间: 约2分钟
```

## 🔍 生成阶段详解

8个生成阶段:

1. **QUEUED** (0%) - 排队中
2. **OUTLINE** (12.5%) - 生成世界框架
3. **LOCATIONS** (25%) - 生成地点和POI
4. **NPCS** (37.5%) - 生成NPC并分配到地点
5. **QUESTS** (50%) - 生成任务和目标DAG
6. **LOOT_TABLES** (62.5%) - 生成掉落表
7. **ENCOUNTER_TABLES** (75%) - 生成遭遇表
8. **INDEXING** (87.5%) - 构建向量索引
9. **READY** (100%) - 完成

每个阶段调用LLM生成结构化数据，最后保存为gzip压缩的JSON。

## 💾 数据存储

**本地数据库**: `data/sqlite/novel.db`

**主要表:**
- `worlds` - 世界主表（含gzip压缩的JSON）
- `world_snapshots` - 快照版本
- `world_generation_jobs` - 生成任务记录
- `world_kb` - 向量索引

**查看数据:**
```bash
sqlite3 data/sqlite/novel.db
.tables
SELECT id, title, status FROM worlds;
```

## ⚡ 性能参考

**生成时间:**
- 小型 (5地点, 8NPC, 6任务): 40秒
- 中型 (15地点, 20NPC, 12任务): 70秒
- 大型 (30地点, 30NPC, 20任务): 120秒

**存储空间:**
- WorldPack JSON: ~100KB
- gzip 压缩后: ~20KB (5:1)

**向量索引:**
- 当前: MD5 hash (32字节/条目)
- 可扩展: OpenAI Embeddings (1536维)

## 🐛 故障排除

### Q: 生成卡在某个阶段不动？

**A:** 检查后端日志:
```bash
# 查看是否有错误
tail -f logs/backend.log
```

可能原因:
- API限流（OpenRouter）
- LLM响应超时
- 数据库锁定

解决: 重启后端服务

### Q: 校验失败显示很多错误？

**A:** 常见问题:
- NPC引用不存在的地点 → 检查地点ID
- 任务循环依赖 → 检查任务DAG
- 数据质量问题 → 重新生成

### Q: 前端显示"加载失败"？

**A:** 检查:
1. 后端是否运行 (http://localhost:8000/health)
2. API端点是否正确
3. 浏览器控制台错误信息

### Q: 生成的世界质量不好？

**A:** 调整参数:
- 减少地点/NPC/任务数量
- 更换基调和难度
- 尝试不同的种子（自动生成）

## 📚 相关文档

- **完整文档**: `docs/PROJECT_OVERVIEW.md`
- **实现细节**: `docs/implementation/WORLD_GENERATION_IMPLEMENTATION.md`
- **迭代计划**: `docs/implementation/V1_ITERATION_PLAN.md`
- **进度总结**: `docs/implementation/PROGRESS_SUMMARY.md`

## 🎉 开始使用

现在你已经了解了WorldPack的基础知识，开始创建你的第一个世界吧！

```bash
1. ./scripts/start/start_all_with_agent.sh
2. 访问 http://localhost:3000/worlds
3. 点击 "生成新世界"
4. 享受自动生成的完整世界！
```

---

**文档版本**: 1.0
**更新时间**: 2025-11-06
**作者**: Claude Code
