#!/usr/bin/env bash
set -euo pipefail

# 清理历史中的 .env/.env.local 等敏感文件的辅助脚本
# 说明：需要安装 git-filter-repo（推荐）或使用 BFG

echo "[i] 本脚本将帮助你移除 Git 历史中的敏感文件引用（如 .env）。"
echo "[!] 注意：历史改写是破坏性的操作，执行前请确认，并与团队同步。"

REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || true)
if [[ -z "${REPO_ROOT}" ]]; then
  echo "[x] 未检测到 Git 仓库，请在仓库根目录运行。" >&2
  exit 1
fi

cd "$REPO_ROOT"

# 目标路径可按需扩展
TARGET_PATHS=(".env" ".env.local")

if command -v git-filter-repo >/dev/null 2>&1 || python -c "import git_filter_repo" >/dev/null 2>&1; then
  echo "[i] 检测到 git-filter-repo，开始清理..."
  # 构造参数：对每个路径执行 --path <file>（后续用 --invert-paths）
  ARGS=()
  for p in "${TARGET_PATHS[@]}"; do
    ARGS+=( --path "$p" )
  done
  git filter-repo "${ARGS[@]}" --invert-paths --force || python -m git_filter_repo "${ARGS[@]}" --invert-paths --force
  echo "[i] 清理完成。请检查变更，并按需强制推送："
  echo "    git push --force origin <your-branch>"
else
  cat <<'EOF'
[!] 未检测到 git-filter-repo。
    可选方案：
    1) 安装 git-filter-repo（推荐）
       https://github.com/newren/git-filter-repo
    2) 使用 BFG Repo-Cleaner（需安装 Java）
       下载 BFG 后执行：
         java -jar bfg.jar --delete-files .env --no-blob-protection
       然后：
         git reflog expire --expire=now --all && git gc --prune=now --aggressive

清理完成后请记得：
  - 轮换密钥（禁用旧 Key，启用新 Key）
  - 强制推送并通知协作者重新克隆或硬重置
EOF
fi

