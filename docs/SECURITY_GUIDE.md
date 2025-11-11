# 秘钥与配置安全指南

本项目已统一通过 `web/backend/config/settings.py` 读取配置，避免在代码中直接使用 `os.getenv`。同时 `.env` 已加入 `.gitignore`，请勿将密钥提交到仓库。

## 1. 正确管理密钥

- 本地开发：
  - 复制 `.env.example` 为 `.env`，填入实际值（例如 `OPENROUTER_API_KEY`）。
  - `.env` 不会提交到 Git（已在 `.gitignore` 中）。
- 生产/CI：
  - 使用运行环境的 Secret/Env 注入（CI Secrets、容器环境变量、云厂商密钥管理）。
  - 不在仓库或磁盘上落盘明文密钥。

核心配置（节选）：

- `OPENROUTER_API_KEY`、`OPENROUTER_BASE_URL`
- `DEFAULT_MODEL`、`WORLD_GENERATION_MODEL`
- `DM_AGENT_BACKEND`（`langchain` 或 `langgraph`）

统一入口：`Settings` 会从 `.env` / 环境变量读取这些值。

## 2. 如果误把 `.env` 提交到仓库

即使随后删除，历史记录中依然可见。请执行：

1) 立即轮换已泄露的密钥（生成新 Key，禁用旧 Key）。

2) 清理 Git 历史（建议安装 Git 官方工具 `git-filter-repo` 或使用 BFG）：

```bash
# 推荐：git-filter-repo（需安装）
# 移除历史中的 .env 与其他敏感文件（示例）
python -m pip install git-filter-repo  # 或参照官方安装方式

# 在仓库根目录执行：
git filter-repo --path .env --invert-paths --force
# 其他敏感文件可追加多个 --path 参数

# 强制推送（谨慎！）
git push --force origin <your-branch>
```

3) 通知协作者重新克隆或运行 `git fetch --all && git reset --hard origin/<branch>`。

> 注意：历史改写是破坏性的操作，仅在确认需要时进行，并与团队同步。

## 3. 快速自检清单

- [ ] `.env` 未被 Git 跟踪（`git ls-files | grep -E '^\.env$'` 无输出）
- [ ] 仅 `.env.example` 随仓库分发，供他人参考
- [ ] 生产环境使用 Secret 注入，未落盘
- [ ] 发生密钥泄露时，已完成：密钥轮换 + 历史清理 + 强制推送 + 通知

