#!/bin/bash
# 目录结构迁移脚本 V2
# 智能处理git和非git文件

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

# 智能移动函数：自动判断使用git mv还是mv
smart_move() {
    local src="$1"
    local dest="$2"
    local desc="$3"

    if [ ! -f "$src" ] && [ ! -d "$src" ]; then
        return 0  # 文件不存在，跳过
    fi

    # 检查文件是否在git版本控制中
    if git ls-files --error-unmatch "$src" > /dev/null 2>&1; then
        # 使用git mv
        git mv "$src" "$dest" 2>/dev/null && echo "    ✓ $desc (git mv)"
    else
        # 使用普通mv
        mv "$src" "$dest" 2>/dev/null && echo "    ✓ $desc (mv)"
    fi
}

echo -e "${GREEN}开始执行目录重组迁移（V2智能版本）...${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 第二步：重组docs目录
echo -e "${GREEN}步骤1: 重组docs目录${NC}"

# 功能文档
echo "  移动功能文档..."
smart_move "docs/WORLD_SCAFFOLD_GUIDE.md" "docs/features/WORLD_SCAFFOLD_GUIDE.md" "WORLD_SCAFFOLD_GUIDE.md"
smart_move "docs/QUEST_SYSTEM.md" "docs/features/QUEST_SYSTEM.md" "QUEST_SYSTEM.md"
smart_move "docs/GAME_FEATURES.md" "docs/features/GAME_FEATURES.md" "GAME_FEATURES.md"
smart_move "docs/QUICK_START_WORLD.md" "docs/features/QUICK_START_WORLD.md" "QUICK_START_WORLD.md"

# 设置文档
echo "  移动设置文档..."
smart_move "docs/SETUP_COMPLETE.md" "docs/setup/SETUP_COMPLETE.md" "SETUP_COMPLETE.md"
smart_move "docs/LITELLM_PROXY_SETUP.md" "docs/setup/LITELLM_PROXY_SETUP.md" "LITELLM_PROXY_SETUP.md"
smart_move "docs/CLAUDE_AGENT_SDK_SETUP.md" "docs/setup/CLAUDE_AGENT_SDK_SETUP.md" "CLAUDE_AGENT_SDK_SETUP.md"
smart_move "docs/LLM_BACKEND_INTEGRATION.md" "docs/setup/LLM_BACKEND_INTEGRATION.md" "LLM_BACKEND_INTEGRATION.md"
smart_move "docs/WORLD_SYSTEM_INTEGRATION_COMPLETE.md" "docs/setup/WORLD_SYSTEM_INTEGRATION_COMPLETE.md" "WORLD_SYSTEM_INTEGRATION_COMPLETE.md"
smart_move "docs/LITELLM_PROXY_MIGRATION_COMPLETE.md" "docs/setup/LITELLM_PROXY_MIGRATION_COMPLETE.md" "LITELLM_PROXY_MIGRATION_COMPLETE.md"

# 实现文档
echo "  移动实现文档..."
smart_move "docs/WORLD_SCAFFOLD_IMPLEMENTATION.md" "docs/implementation/WORLD_SCAFFOLD_IMPLEMENTATION.md" "WORLD_SCAFFOLD_IMPLEMENTATION.md"
smart_move "docs/CLAUDE_AGENT_SDK_IMPLEMENTATION.md" "docs/implementation/CLAUDE_AGENT_SDK_IMPLEMENTATION.md" "CLAUDE_AGENT_SDK_IMPLEMENTATION.md"
smart_move "docs/LLM_BACKEND_INTEGRATION_COMPLETE.md" "docs/implementation/LLM_BACKEND_INTEGRATION_COMPLETE.md" "LLM_BACKEND_INTEGRATION_COMPLETE.md"
smart_move "docs/UI_INTEGRATION_COMPLETE.md" "docs/implementation/UI_INTEGRATION_COMPLETE.md" "UI_INTEGRATION_COMPLETE.md"
smart_move "docs/IMPLEMENTATION_SUMMARY.md" "docs/implementation/IMPLEMENTATION_SUMMARY.md" "IMPLEMENTATION_SUMMARY.md"

# 运维文档
echo "  移动运维文档..."
smart_move "docs/START_ALL_WITH_AGENT_GUIDE.md" "docs/operations/START_ALL_WITH_AGENT_GUIDE.md" "START_ALL_WITH_AGENT_GUIDE.md"
smart_move "docs/LITELLM_AGENT_GUIDE.md" "docs/operations/LITELLM_AGENT_GUIDE.md" "LITELLM_AGENT_GUIDE.md"
smart_move "docs/LLM_BACKEND_GUIDE.md" "docs/operations/LLM_BACKEND_GUIDE.md" "LLM_BACKEND_GUIDE.md"
smart_move "docs/LLM_BACKEND_USAGE.md" "docs/operations/LLM_BACKEND_USAGE.md" "LLM_BACKEND_USAGE.md"
smart_move "docs/DEMO_EXPERIENCE_GUIDE.md" "docs/operations/DEMO_EXPERIENCE_GUIDE.md" "DEMO_EXPERIENCE_GUIDE.md"

# 故障排除文档
echo "  移动故障排除文档..."
smart_move "docs/TROUBLESHOOTING.md" "docs/troubleshooting/TROUBLESHOOTING.md" "TROUBLESHOOTING.md"
smart_move "docs/BUG_FIXES.md" "docs/troubleshooting/BUG_FIXES.md" "BUG_FIXES.md"
smart_move "docs/BUG_FIX_502_GATEWAY.md" "docs/troubleshooting/BUG_FIX_502_GATEWAY.md" "BUG_FIX_502_GATEWAY.md"
smart_move "docs/QUICK_FIX_CHECKLIST.md" "docs/troubleshooting/QUICK_FIX_CHECKLIST.md" "QUICK_FIX_CHECKLIST.md"

# 参考文档
echo "  移动参考文档..."
smart_move "docs/QUICK_REFERENCE.md" "docs/reference/QUICK_REFERENCE.md" "QUICK_REFERENCE.md"
smart_move "docs/IMPLEMENTATION_GAP_ANALYSIS.md" "docs/reference/IMPLEMENTATION_GAP_ANALYSIS.md" "IMPLEMENTATION_GAP_ANALYSIS.md"
smart_move "docs/PHASE1_COMPLETE.md" "docs/reference/PHASE1_COMPLETE.md" "PHASE1_COMPLETE.md"
smart_move "docs/CLAUDE_AGENT_SDK_EVALUATION.md" "docs/reference/CLAUDE_AGENT_SDK_EVALUATION.md" "CLAUDE_AGENT_SDK_EVALUATION.md"
echo ""

# 第三步：重组scripts目录
echo -e "${GREEN}步骤2: 重组scripts目录${NC}"

# 启动脚本
echo "  移动启动脚本..."
smart_move "start_all_with_agent.sh" "scripts/start/start_all_with_agent.sh" "start_all_with_agent.sh"
smart_move "start_litellm_proxy.sh" "scripts/start/start_litellm_proxy.sh" "start_litellm_proxy.sh"
smart_move "stop_all.sh" "scripts/start/stop_all.sh" "stop_all.sh"
smart_move "run.sh" "scripts/start/run.sh" "run.sh"

# 开发工具脚本
echo "  移动开发工具脚本..."
smart_move "check_services.sh" "scripts/dev/check_services.sh" "check_services.sh"
smart_move "view_logs.sh" "scripts/dev/view_logs.sh" "view_logs.sh"

# 测试脚本
echo "  移动测试脚本..."
smart_move "test_proxy_e2e.sh" "scripts/test/test_proxy_e2e.sh" "test_proxy_e2e.sh"
echo ""

# 第四步：重组tests目录
echo -e "${GREEN}步骤3: 重组tests目录${NC}"

# 端到端测试
echo "  移动端到端测试..."
smart_move "test_chat_stream.py" "tests/e2e/test_chat_stream.py" "test_chat_stream.py"
smart_move "test_litellm_api.py" "tests/e2e/test_litellm_api.py" "test_litellm_api.py"
smart_move "test_llm_backend.py" "tests/e2e/test_llm_backend.py" "test_llm_backend.py"
smart_move "test_world_scaffold.py" "tests/e2e/test_world_scaffold.py" "test_world_scaffold.py"
echo ""

# 第五步：重组web/backend目录
echo -e "${GREEN}步骤4: 重组web/backend目录${NC}"
cd web/backend

# API文件
echo "  移动API文件..."
smart_move "chat_api.py" "api/chat_api.py" "chat_api.py"
smart_move "generation_api.py" "api/generation_api.py" "generation_api.py"
smart_move "game_api.py" "api/game_api.py" "game_api.py"
smart_move "world_api.py" "api/world_api.py" "world_api.py"

# 服务文件
echo "  移动服务文件..."
smart_move "agent_generation.py" "services/agent_generation.py" "agent_generation.py"
smart_move "world_generator.py" "services/world_generator.py" "world_generator.py"
smart_move "scene_refinement.py" "services/scene_refinement.py" "scene_refinement.py"

# 游戏引擎文件
echo "  移动游戏引擎文件..."
smart_move "game_engine.py" "game/game_engine.py" "game_engine.py"
smart_move "game_tools.py" "game/game_tools.py" "game_tools.py"

# 模型文件
echo "  移动模型文件..."
smart_move "world_models.py" "models/world_models.py" "world_models.py"

# 数据库文件
echo "  移动数据库文件..."
smart_move "world_db.py" "database/world_db.py" "world_db.py"

cd "$PROJECT_ROOT"
echo ""

# 创建__init__.py文件
echo -e "${GREEN}步骤5: 创建__init__.py文件${NC}"
touch web/backend/api/__init__.py
touch web/backend/services/__init__.py
touch web/backend/models/__init__.py
touch web/backend/database/__init__.py
touch tests/e2e/__init__.py
touch docs/features/__init__.py 2>/dev/null || true
touch docs/setup/__init__.py 2>/dev/null || true
touch docs/implementation/__init__.py 2>/dev/null || true
touch docs/operations/__init__.py 2>/dev/null || true
touch docs/troubleshooting/__init__.py 2>/dev/null || true
touch docs/reference/__init__.py 2>/dev/null || true
echo "  ✓ 创建完成"
echo ""

echo -e "${GREEN}✅ 目录迁移完成！${NC}"
echo ""
echo -e "${YELLOW}下一步操作：${NC}"
echo "1. 更新 web/backend/main.py 中的导入路径"
echo "2. 更新所有API文件中的导入路径"
echo "3. 更新所有服务文件中的导入路径"
echo "4. 更新启动脚本中的路径引用"
echo "5. 运行测试验证迁移"
echo ""
echo "详细步骤请参考: docs/DIRECTORY_MIGRATION_GUIDE.md"
