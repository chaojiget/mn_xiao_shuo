# LiteLLM Proxy 迁移完成报告

## 迁移概述

成功将项目从直接调用 litellm 库迁移到使用 **LiteLLM Proxy** 架构。

**迁移日期**: 2025-11-02
**状态**: ✅ 完成

## 主要变更

### 1. 架构变更

**之前**:
```
后端 → litellm库 → OpenRouter API
```

**现在**:
```
后端 → LiteLLM Proxy (HTTP) → OpenRouter API
         ↑
         └─ 使用 Authorization: Bearer $LITELLM_MASTER_KEY
```

### 2. 文件变更列表

#### 新增文件
- `start_litellm_proxy.sh` - LiteLLM Proxy 启动脚本
- `test_litellm_api.py` - API 测试脚本
- `test_proxy_e2e.sh` - 端到端测试脚本
- `docs/LITELLM_PROXY_SETUP.md` - 完整设置文档

#### 修改文件
- `web/backend/llm/litellm_backend.py` - 完全重写为 HTTP 客户端模式
- `config/litellm_config.yaml` - 更新为 Proxy 配置
  - 使用 `os.environ/OPENROUTER_API_KEY` 语法
  - 添加 `master_key: os.environ/LITELLM_MASTER_KEY`
  - 启用 `allow_requests_on_db_unavailable: true`
- `.env` - 新增 `LITELLM_MASTER_KEY` 环境变量

#### 删除文件
- `test_litellm_proxy.sh` (冗余)
- `test_proxy_api.sh` (冗余)

### 3. 关键配置

#### 环境变量（.env）
```bash
# OpenRouter API Key (已有)
OPENROUTER_API_KEY=sk-or-v1-xxxxx

# LiteLLM Proxy Master Key (新增)
LITELLM_MASTER_KEY=sk-litellm-xxxxx  # 由启动脚本自动生成
```

#### LiteLLM Proxy 配置
```yaml
# config/litellm_config.yaml

litellm_settings:
  master_key: os.environ/LITELLM_MASTER_KEY  # Proxy 认证
  allow_requests_on_db_unavailable: true     # 允许无数据库运行

general_settings:
  database_url: null                         # 禁用数据库
  store_model_in_db: false
  disable_spend_logs: true
```

#### 后端代码
```python
# web/backend/llm/litellm_backend.py

class LiteLLMBackend(LLMBackend):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        # 从环境变量读取 Master Key
        self.api_key = os.environ.get("LITELLM_MASTER_KEY", "")

        # 创建 HTTP 客户端，自动添加 Authorization header
        self.http_client = httpx.AsyncClient(
            base_url=self.proxy_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=120.0
        )
```

## 问题解决过程

### 问题1: 环境变量替换失败

**现象**: 配置中的 `${OPENROUTER_API_KEY}` 未被替换

**解决方案**: 使用 LiteLLM 的 `os.environ/` 语法
```yaml
# ❌ 错误
api_key: ${OPENROUTER_API_KEY}

# ✅ 正确
api_key: os.environ/OPENROUTER_API_KEY
```

### 问题2: 认证失败 (401 Unauthorized)

**现象**: 请求返回 "No api key passed in"

**解决方案**:
1. 设置环境变量 `LITELLM_MASTER_KEY`
2. 在所有 HTTP 请求中添加 `Authorization: Bearer $LITELLM_MASTER_KEY`

### 问题3: 数据库连接错误

**现象**: "No connected db" 错误

**解决方案**: 在配置中添加
```yaml
litellm_settings:
  allow_requests_on_db_unavailable: true

general_settings:
  database_url: null
  disable_spend_logs: true
```

### 问题4: allowed_ips 企业功能

**现象**: "allowed_ips is an Enterprise Feature"

**解决方案**: 从配置中移除 `allowed_ips` 参数

## 使用指南

### 快速启动

```bash
# 1. 启动 LiteLLM Proxy
./start_litellm_proxy.sh

# 2. (在另一个终端) 测试 API
./test_proxy_e2e.sh

# 3. 启动 Web 服务
./web/start-web.sh
```

### 测试 API

```bash
# 方式1: 使用测试脚本
python test_litellm_api.py

# 方式2: 使用 curl
export LITELLM_MASTER_KEY=$(grep LITELLM_MASTER_KEY .env | cut -d '=' -f2-)

curl -X POST http://localhost:4000/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{
    "model": "deepseek",
    "messages": [{"role": "user", "content": "你好"}]
  }'
```

## 优势

### 1. 架构优势

- ✅ **解耦**: 后端通过标准 HTTP API 调用，不依赖 litellm 库的具体实现
- ✅ **标准化**: 使用 OpenAI 兼容的 API 格式
- ✅ **独立性**: LiteLLM Proxy 可以独立重启/升级，不影响后端
- ✅ **可监控**: 可以在 Proxy 层添加日志、监控、限流等功能

### 2. Claude Agent SDK 兼容

现在可以通过环境变量直接使用 Claude Agent SDK:

```bash
# 设置环境变量
export ANTHROPIC_BASE_URL=http://localhost:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=deepseek  # 或其他模型别名

# Claude Agent SDK 会自动使用这些环境变量
```

### 3. 多客户端支持

同一个 LiteLLM Proxy 可以服务多个客户端：
- Python 后端
- Node.js 前端
- CLI 工具
- Claude Agent SDK
- 任何支持 OpenAI API 的工具

## 验证清单

- [x] LiteLLM Proxy 成功启动
- [x] 环境变量正确配置
- [x] API 认证工作正常
- [x] 普通文本生成测试通过
- [x] 流式输出测试通过
- [x] 后端代码更新完成
- [x] 文档创建完成
- [x] 测试脚本创建完成

## 下一步

### 可选优化

1. **添加日志记录**: 在 Proxy 层添加请求/响应日志
2. **监控面板**: 使用 LiteLLM 的内置监控功能
3. **限流控制**: 配置 rate limiting
4. **缓存优化**: 启用响应缓存

### Claude Agent SDK 集成

参考用户提供的配置：

```bash
export ANTHROPIC_BASE_URL=http://0.0.0.0:4000
export ANTHROPIC_AUTH_TOKEN=$LITELLM_MASTER_KEY
export ANTHROPIC_MODEL=openrouter/deepseek/deepseek-chat-v3-0324
```

## 相关文档

- [LiteLLM Proxy 设置指南](./LITELLM_PROXY_SETUP.md)
- [Claude Agent SDK 集成](./CLAUDE_AGENT_SDK_INTEGRATION.md) (待创建)
- [项目主 README](../README.md)
- [快速启动](./QUICK_START.md)

## 总结

本次迁移成功实现了：

1. ✅ **完全使用 LiteLLM Proxy 模式**，不再直接调用 litellm 库
2. ✅ **配置文件和环境变量管理**优化
3. ✅ **认证机制**正确实现 (使用 LITELLM_MASTER_KEY)
4. ✅ **完整的测试和文档**

系统现在可以：
- 稳定运行 LiteLLM Proxy
- 通过 HTTP API 调用多种 LLM 模型
- 支持流式输出
- 兼容 Claude Agent SDK

**状态**: ✅ **生产就绪**
