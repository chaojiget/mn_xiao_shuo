# 世界脚手架系统快速启动指南

## 前置条件

- Python 3.10+
- Node.js 18+
- 已配置 LLM 后端（DeepSeek/Claude/etc.）

## 快速启动步骤

### 1. 启动后端服务

```bash
# 进入项目根目录
cd /Users/lijianyong/mn_xiao_shuo

# 激活虚拟环境
source .venv/bin/activate

# 进入后端目录
cd web/backend

# 启动FastAPI服务器
uvicorn main:app --reload --port 8000
```

**验证**: 访问 http://localhost:8000/docs 查看API文档

### 2. 启动前端服务

```bash
# 新开一个终端
cd /Users/lijianyong/mn_xiao_shuo/web/frontend

# 如果是首次运行，清理缓存
rm -rf .next node_modules package-lock.json
npm install

# 启动开发服务器
npm run dev
```

**验证**: 访问 http://localhost:3000

### 3. 访问世界管理页面

打开浏览器，访问：http://localhost:3000/world

## 使用流程

### 方式A：通过Web界面

1. **创建世界**
   - 访问 http://localhost:3000/world
   - 填写表单：
     - 小说ID: `test-novel-001`
     - 主题: `deep sea survival`
     - 基调: `压抑、未知、孤独`
     - 小说类型: `科幻`
     - 区域数量: `5`
   - 点击"生成世界"
   - 等待约1-2分钟（生成5个区域+派系）

2. **浏览世界**
   - 左侧：世界树导航（World → Regions → Locations）
   - 点击区域，查看区域信息
   - 点击"生成地点"按钮，为区域生成地点

3. **细化场景**
   - 点击某个地点
   - 中间显示地点详情
   - 点击"细化场景"按钮
   - 等待约10-15秒
   - 查看：
     - 叙事文本
     - 感官节点（视听嗅触温）
     - 可供性chips（可做之事）

4. **查看派系**
   - 右侧面板，切换到"派系"标签
   - 查看派系列表、势力值、状态

### 方式B：通过API测试

```bash
# 激活虚拟环境
source .venv/bin/activate

# 运行测试脚本
python test_world_scaffold.py
```

这个脚本会：
1. 初始化LLM后端和数据库
2. 生成一个测试世界（3个区域）
3. 为第一个区域生成2个地点
4. 细化第一个地点（4个Pass）
5. 提取可供性

**预计耗时**: 2-3分钟

### 方式C：直接调用API

#### 1. 生成世界

```bash
curl -X POST http://localhost:8000/api/world/generate \
  -H "Content-Type: application/json" \
  -d '{
    "novelId": "my-novel-001",
    "theme": "cyberpunk survival",
    "tone": "dark, gritty, neon-lit",
    "novelType": "scifi",
    "numRegions": 5,
    "locationsPerRegion": 8,
    "poisPerLocation": 5
  }'
```

#### 2. 查看世界列表

```bash
curl http://localhost:8000/api/world/by-novel/my-novel-001
```

#### 3. 查看区域列表

```bash
# 先获取world_id
WORLD_ID="world-my-novel-001"

curl http://localhost:8000/api/world/scaffold/${WORLD_ID}/regions
```

#### 4. 细化地点

```bash
# 替换为实际的location_id
LOCATION_ID="world-my-novel-001-region-01-loc-01"

curl -X POST http://localhost:8000/api/world/location/${LOCATION_ID}/refine \
  -H "Content-Type: application/json" \
  -d '{
    "location_id": "'${LOCATION_ID}'",
    "turn": 0,
    "target_detail_level": 2,
    "passes": ["structure", "sensory", "affordance", "cinematic"]
  }'
```

## 故障排查

### 问题1：前端报错 "Invariant: missing bootstrap script"

**解决**：
```bash
cd web/frontend
rm -rf .next node_modules package-lock.json
npm install
npm run dev
```

### 问题2：端口被占用

**解决**：
```bash
# 关闭占用3000端口的进程
lsof -ti:3000 | xargs kill -9

# 关闭占用8000端口的进程
lsof -ti:8000 | xargs kill -9
```

### 问题3：后端报错 "Module not found"

**解决**：
```bash
# 确保在虚拟环境中
source .venv/bin/activate

# 重新安装依赖
pip install -r requirements.txt
```

### 问题4：数据库表不存在

**解决**：
```bash
# 执行Schema
sqlite3 data/sqlite/novel.db < schema_world_scaffold.sql
```

### 问题5：LLM生成失败

**检查**：
- `.env` 文件中是否配置了 `OPENROUTER_API_KEY`
- `config/llm_backend.yaml` 中的模型配置是否正确
- 网络连接是否正常

## 性能优化建议

### 1. 调整生成数量

首次测试时，建议减少数量：
- `numRegions: 3`（而非5）
- `locationsPerRegion: 5`（而非8）
- `poisPerLocation: 3`（而非5）

### 2. 使用更快的模型

在 `config/llm_backend.yaml` 中：
```yaml
default_model: "deepseek-chat"  # 最快最便宜
# default_model: "claude-3-5-haiku-20241022"  # 更快但稍贵
```

### 3. 批量生成

如果需要生成大量地点，使用批量接口：
```bash
curl -X POST http://localhost:8000/api/world/scaffold/${WORLD_ID}/generate-all \
  -H "Content-Type: application/json" \
  -d '{
    "locations_per_region": 8,
    "pois_per_location": 5
  }'
```

## 查看生成的数据

### 使用SQLite命令行

```bash
sqlite3 data/sqlite/novel.db

# 查看所有世界
SELECT id, name, theme, tone FROM world_scaffolds;

# 查看区域
SELECT id, name, biome, danger_level FROM regions WHERE world_id = 'world-xxx';

# 查看地点
SELECT id, name, type, detail_level FROM locations WHERE region_id = 'xxx-region-01';

# 查看细化层
SELECT target_id, layer_type, status FROM detail_layers WHERE target_id = 'xxx-loc-01';

# 退出
.quit
```

### 使用Python脚本

```python
from web.backend.world_db import WorldDatabase

db = WorldDatabase("data/sqlite/novel.db")

# 查看世界
world = db.get_world_by_novel("my-novel-001")
print(f"世界: {world.name}")
print(f"主题: {world.theme}")
print(f"基调: {world.tone}")

# 查看区域
regions = db.get_regions_by_world(world.id)
for region in regions:
    print(f"区域: {region.name} - {region.biome} - 危险等级{region.danger_level}")

# 查看地点
locations = db.get_locations_by_region(regions[0].id)
for loc in locations:
    print(f"地点: {loc.name} - 细化等级{loc.detail_level}")
```

## 下一步

1. ✅ **测试完整流程**：运行 `python test_world_scaffold.py`
2. ✅ **体验Web界面**：访问 http://localhost:3000/world
3. ⬜ **集成到聊天**：在聊天界面中触发场景细化
4. ⬜ **自定义风格**：修改世界的 `style_bible`
5. ⬜ **导出数据**：将世界导出为JSON/Markdown

## 相关文档

- **完整指南**: `docs/WORLD_SCAFFOLD_GUIDE.md`
- **实现总结**: `docs/WORLD_SCAFFOLD_IMPLEMENTATION.md`
- **数据库Schema**: `schema_world_scaffold.sql`
- **测试脚本**: `test_world_scaffold.py`

## 联系与反馈

如有问题或建议，请查看相关文档或提交issue。
