# 世界生成系统实现文档

> 更新时间：2025-11-05
> 状态：已实现核心组件

## 📋 已完成组件

### 1. WorldGenerationJob 类

**文件**: `web/backend/services/world_generation_job.py`

**功能**:
- ✅ 分阶段世界生成流水线
- ✅ 进度跟踪与数据库持久化
- ✅ 错误处理与状态管理
- ✅ 可扩展的回调系统

**生成流程**:
```
QUEUED → OUTLINE → LOCATIONS → NPCS → QUESTS →
LOOT_TABLES → ENCOUNTER_TABLES → INDEXING → READY
```

**关键方法**:
- `run()` - 执行完整生成流程
- `_generate_outline()` - 生成世界框架
- `_generate_locations()` - 生成地点与 POI
- `_generate_npcs()` - 生成 NPC
- `_generate_quests()` - 生成任务
- `_save_world_pack()` - 保存到数据库（gzip 压缩）

### 2. WorldValidator 类

**文件**: `web/backend/services/world_validator.py`

**功能**:
- ✅ 引用完整性校验
- ✅ 任务依赖 DAG 检测（环路检测）
- ✅ 业务规则校验
- ✅ 数据质量检查

**校验类型**:

1. **引用完整性**:
   - NPC home_location 引用
   - NPC 关系引用
   - Location NPCs 引用
   - POI 掉落表/遭遇表引用
   - 任务目标依赖引用

2. **DAG 检测**:
   - 任务前置依赖无环
   - 任务目标依赖无环

3. **业务规则**:
   - 地点数量 ≥ 3
   - 至少 1 个主线任务
   - 地点/NPC 名称不重复
   - 坐标在地图范围内
   - 每个地点至少 1 个 POI

4. **数据质量**:
   - 名称非空
   - 必填字段完整
   - 任务至少有目标

**问题分级**:
- `error` - 必须修复的错误
- `warning` - 建议修复的警告
- `info` - 提示信息

### 3. 测试脚本

**文件**: `tests/integration/test_world_generation.py`

**功能**:
- ✅ 端到端世界生成测试
- ✅ 进度可视化（进度条）
- ✅ 生成结果展示
- ✅ 自动校验

## 🎯 使用示例

### 命令行测试

```bash
# 运行世界生成测试
uv run python tests/integration/test_world_generation.py
```

### 代码示例

```python
from models.world_pack import WorldGenerationRequest
from services.world_generation_job import create_world_generation_job
from services.world_validator import WorldValidator

# 创建生成请求
request = WorldGenerationRequest(
    title="魔法学院世界",
    seed=12345,
    tone="epic",
    difficulty="normal",
    num_locations=10,
    num_npcs=15,
    num_quests=8
)

# 创建并运行任务
job = await create_world_generation_job(
    request=request,
    llm_client=llm_client,
    db_path="data/sqlite/novel.db",
    progress_callback=lambda phase, prog, msg: print(f"{phase}: {msg}")
)

world_pack = await job.run()

# 校验
validator = WorldValidator()
problems = validator.validate_all(world_pack)

if validator.has_errors():
    print("❌ 世界存在错误")
    for problem in problems:
        print(problem)
else:
    print("✅ 世界生成成功")
```

## 📊 数据流

```
WorldGenerationRequest
    ↓
create_world_generation_job()
    ↓
WorldGenerationJob.run()
    ↓
┌────────────────────────────────┐
│ 1. OUTLINE                     │
│    - LLM 生成世界框架          │
│    - 创建 WorldMeta            │
│    - 提取 Lore                 │
├────────────────────────────────┤
│ 2. LOCATIONS                   │
│    - LLM 生成地点列表          │
│    - 自动生成 POI              │
├────────────────────────────────┤
│ 3. NPCS                        │
│    - LLM 生成 NPC              │
│    - 分配到地点                │
├────────────────────────────────┤
│ 4. QUESTS                      │
│    - LLM 生成任务              │
│    - 构建目标依赖              │
├────────────────────────────────┤
│ 5. LOOT_TABLES                 │
│    - 生成掉落表                │
├────────────────────────────────┤
│ 6. ENCOUNTER_TABLES            │
│    - 按 biome 生成遭遇表       │
├────────────────────────────────┤
│ 7. INDEXING                    │
│    - 校验引用完整性            │
│    - 检测 DAG 环路             │
│    - 保存到数据库（gzip）      │
└────────────────────────────────┘
    ↓
WorldPack (READY)
```

## 🔧 技术细节

### 1. LLM 调用策略

**模型选择**:
- 所有生成阶段使用 `deepseek`
- Temperature: 0.8-0.9（高创造性）
- Max Tokens: 1500-3000

**Prompt 工程**:
- 严格的 JSON 格式要求
- 明确的约束条件
- 示例输出格式

### 2. 数据库存储

**压缩策略**:
```python
# 序列化并压缩
json_str = world_pack.model_dump_json(indent=2)
json_gz = gzip.compress(json_str.encode('utf-8'))

# 存储
cursor.execute("""
    INSERT INTO worlds (id, title, seed, json_gz, status)
    VALUES (?, ?, ?, ?, 'draft')
""", (world_id, title, seed, json_gz))
```

**读取**:
```python
# 从数据库读取
json_gz = cursor.fetchone()[0]

# 解压
json_str = gzip.decompress(json_gz).decode('utf-8')
world_pack = WorldPack.model_validate_json(json_str)
```

### 3. 进度跟踪

**数据库记录**:
```sql
INSERT INTO world_generation_jobs (id, world_id, phase, progress)
VALUES ('job-xxx', 'world-yyy', 'LOCATIONS', 0.3)
ON CONFLICT(id) DO UPDATE SET
    phase = excluded.phase,
    progress = excluded.progress
```

**回调机制**:
```python
async def progress_callback(phase: str, progress: float, message: str):
    print(f"[{phase}] {progress*100:.0f}% - {message}")

job = WorldGenerationJob(..., progress_callback=progress_callback)
```

### 4. 校验算法

**DAG 环路检测**（拓扑排序）:
```python
def has_cycle(node: str, path: List[str]) -> bool:
    visited.add(node)
    rec_stack.add(node)
    path.append(node)

    for neighbor in graph.get(node, []):
        if neighbor not in visited:
            if has_cycle(neighbor, path):
                return True
        elif neighbor in rec_stack:
            # 找到环
            return True

    path.pop()
    rec_stack.remove(node)
    return False
```

## ⚙️ 配置与参数

### WorldGenerationRequest 参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | str | - | 世界标题 |
| seed | int | random | 随机种子 |
| tone | str | "epic" | 基调（dark/epic/cozy/mystery/whimsical） |
| difficulty | str | "normal" | 难度（story/normal/hard） |
| num_locations | int | 20 | 地点数量（5-50） |
| num_npcs | int | 15 | NPC 数量（3-30） |
| num_quests | int | 10 | 任务数量（3-20） |

### 生成时间估算

| 阶段 | 时间 | 说明 |
|------|------|------|
| OUTLINE | 5-10s | 世界框架 |
| LOCATIONS | 10-20s | 地点生成 |
| NPCS | 8-15s | NPC 生成 |
| QUESTS | 10-18s | 任务生成 |
| LOOT_TABLES | 1-2s | 掉落表 |
| ENCOUNTER_TABLES | 1-2s | 遭遇表 |
| INDEXING | 1-3s | 校验与保存 |
| **总计** | **40-70s** | 完整流程 |

## 🐛 已知问题与限制

### 1. LLM 生成质量不稳定
**问题**: LLM 可能生成格式错误的 JSON
**解决方案**:
- 添加 JSON 清理逻辑
- 重试机制（最多 3 次）
- 更严格的 Prompt

### 2. 无增量恢复
**问题**: 生成失败后需要重新开始
**后续优化**:
- 保存每个阶段的中间结果
- 支持从任意阶段恢复

### 3. 向量索引未实现
**状态**: 待实现
**计划**: WorldIndexer 类（下一个任务）

## 📝 下一步计划

### 短期（本周）
- [ ] 实现 WorldIndexer 类（向量索引）
- [ ] 添加 API 端点
- [ ] 运行完整测试

### 中期（2周内）
- [ ] 前端编辑器
- [ ] 快照管理
- [ ] Fog of War

## 📚 相关文档

- **数据模型**: `web/backend/models/world_pack.py`
- **数据库 Schema**: `database/schema/world_generation.sql`
- **迭代规划**: `docs/implementation/V1_ITERATION_PLAN.md`

---

**创建者**: Claude Code
**更新时间**: 2025-11-05
**版本**: 1.0
