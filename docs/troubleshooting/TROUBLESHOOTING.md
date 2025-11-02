# 故障排查指南

## 快速诊断

运行检查脚本：
```bash
./check_services.sh
```

## 常见错误及解决方案

### 错误1: 端口被占用

**症状**:
```
ERROR: [Errno 48] Address already in use
```

**原因**: 端口 4000/8000/3000 已被其他进程占用

**解决方案**:
```bash
# 方式1: 使用 stop_all.sh 清理
./stop_all.sh

# 方式2: 手动清理端口
lsof -ti:4000 | xargs kill -9  # LiteLLM
lsof -ti:8000 | xargs kill -9  # Backend
lsof -ti:3000 | xargs kill -9  # Frontend

# 方式3: start_all_with_agent.sh 已自动清理（最新版本）
./start_all_with_agent.sh
```

### 错误2: LiteLLM健康检查失败

**症状**:
```
INFO: 127.0.0.1:51339 - "GET /health HTTP/1.1" 401 Unauthorized
```

**原因**: `/health` 端点需要认证，但脚本未传递 API key

**状态**: ✅ 已修复 - 现在使用 `/v1/models` 端点检查

**验证**:
```bash
# 不需要认证
curl http://localhost:4000/v1/models

# 需要认证
curl -H "Authorization: Bearer $LITELLM_MASTER_KEY" http://localhost:4000/health
```

### 错误3: LITELLM_MASTER_KEY 未设置

**症状**:
```bash
echo $LITELLM_MASTER_KEY
# 输出为空
```

**解决方案**:
```bash
# 方式1: 重新运行启动脚本（会自动生成）
./start_all_with_agent.sh

# 方式2: 手动生成
export LITELLM_MASTER_KEY="sk-litellm-$(openssl rand -hex 16)"
echo "LITELLM_MASTER_KEY=$LITELLM_MASTER_KEY" >> .env

# 方式3: 从 .env 加载
source .env
```

### 错误4: 虚拟环境未激活

**症状**:
```
bash: uv: command not found
bash: litellm: command not found
```

**解决方案**:
```bash
# 激活虚拟环境
source .venv/bin/activate

# 或使用完整路径
./.venv/bin/uv pip list
```

### 错误5: 配置文件错误

**症状**:
```
ValueError: allowed_ips is an Enterprise Feature
```

**原因**: 配置文件包含企业功能参数

**解决方案**:
```bash
# 检查配置文件
cat config/litellm_config.yaml

# 确保已移除 allowed_ips
# 确保使用 os.environ/OPENROUTER_API_KEY 语法
```

### 错误6: OpenRouter API Key 无效

**症状**:
```
OpenRouter API 返回 401 或 403
```

**解决方案**:
```bash
# 检查 .env 文件
grep OPENROUTER_API_KEY .env

# 验证 API key
curl https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $(grep OPENROUTER_API_KEY .env | cut -d '=' -f2-)"

# 如果无效，更新 .env
# OPENROUTER_API_KEY=sk-or-v1-xxxxx（新的有效key）
```

## 日志分析

### 查看实时日志

```bash
# 所有日志
tail -f logs/*.log

# 单个服务
tail -f logs/litellm.log
tail -f logs/backend.log
tail -f logs/frontend.log
```

### 查找错误

```bash
# 查找所有错误
grep -i error logs/*.log

# 查找最近的错误
grep -i error logs/*.log | tail -10

# 查找特定错误
grep "401 Unauthorized" logs/litellm.log
grep "Address already in use" logs/backend.log
```

### 清理日志

```bash
# 清空所有日志
> logs/litellm.log
> logs/backend.log
> logs/frontend.log

# 或删除
rm logs/*.log
```

## 完整重启流程

如果遇到问题，按以下顺序操作：

```bash
# 1. 停止所有服务
./stop_all.sh

# 2. 清理端口（确保彻底）
pkill -9 -f litellm
lsof -ti:4000 | xargs kill -9 2>/dev/null
lsof -ti:8000 | xargs kill -9 2>/dev/null
lsof -ti:3000 | xargs kill -9 2>/dev/null

# 3. 清空日志
rm -f logs/*.log

# 4. 检查环境变量
source .env
echo "OPENROUTER_API_KEY: ${OPENROUTER_API_KEY:0:20}..."
echo "LITELLM_MASTER_KEY: ${LITELLM_MASTER_KEY:0:20}..."

# 5. 重新启动
./start_all_with_agent.sh

# 6. 检查状态
./check_services.sh
```

## 环境变量检查清单

确保以下环境变量已设置：

```bash
# 必需（在 .env 中）
✓ OPENROUTER_API_KEY

# 自动生成（启动脚本）
✓ LITELLM_MASTER_KEY
✓ ANTHROPIC_BASE_URL
✓ ANTHROPIC_AUTH_TOKEN
✓ ANTHROPIC_MODEL

# 验证命令
env | grep -E "OPENROUTER|LITELLM|ANTHROPIC"
```

## 性能问题

### LiteLLM Proxy 响应慢

```bash
# 检查配置中的超时设置
grep timeout config/litellm_config.yaml

# 检查并发限制
grep max_parallel_requests config/litellm_config.yaml

# 查看详细日志
# 编辑 config/litellm_config.yaml
# set_verbose: true
```

### Backend 启动慢

```bash
# 检查数据库初始化
ls -lh data/sqlite/novel.db

# 如果数据库损坏，重新初始化
rm data/sqlite/novel.db
python scripts/init_db.py
```

## 调试模式

### 启用详细日志

编辑 `config/litellm_config.yaml`:
```yaml
litellm_settings:
  set_verbose: true  # 改为 true
```

### 手动启动（用于调试）

```bash
# 1. 手动启动 LiteLLM Proxy
source .venv/bin/activate
export OPENROUTER_API_KEY=$(grep OPENROUTER_API_KEY .env | cut -d '=' -f2-)
export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)
litellm --config ./config/litellm_config.yaml --host 0.0.0.0 --port 4000 --debug

# 2. 在新终端启动 Backend
cd web/backend
uv run uvicorn main:app --reload --port 8000

# 3. 在新终端启动 Frontend
cd web/frontend
npm run dev
```

## 获取帮助

如果以上方法都无法解决问题：

1. **收集信息**:
   ```bash
   ./check_services.sh > debug_info.txt
   cat logs/*.log >> debug_info.txt
   env | grep -E "OPENROUTER|LITELLM|ANTHROPIC" >> debug_info.txt
   ```

2. **检查文档**:
   - `docs/START_ALL_WITH_AGENT_GUIDE.md`
   - `docs/LITELLM_PROXY_SETUP.md`
   - `docs/CLAUDE_AGENT_SDK_SETUP.md`

3. **查看项目 Issues**:
   - LiteLLM: https://github.com/BerriAI/litellm/issues
   - OpenRouter: https://openrouter.ai/docs

4. **常用资源**:
   - LiteLLM文档: https://docs.litellm.ai/
   - FastAPI文档: https://fastapi.tiangolo.com/
   - Next.js文档: https://nextjs.org/docs
