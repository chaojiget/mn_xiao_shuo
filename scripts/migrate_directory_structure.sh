#!/bin/bash
# 目录结构迁移脚本
# 自动执行目录重组计划

set -e  # 遇到错误立即退出

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}开始执行目录重组迁移...${NC}"
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 确认操作
read -p "此操作将移动大量文件，建议先提交当前更改。是否继续？(y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}操作已取消${NC}"
    exit 1
fi

# 第一步：移动数据库schema文件
echo -e "${GREEN}步骤1: 移动数据库schema文件${NC}"
if [ -f "schema.sql" ]; then
    git mv schema.sql database/schema/core.sql
    echo "  ✓ schema.sql -> database/schema/core.sql"
fi
if [ -f "schema_world_scaffold.sql" ]; then
    git mv schema_world_scaffold.sql database/schema/world_scaffold.sql
    echo "  ✓ schema_world_scaffold.sql -> database/schema/world_scaffold.sql"
fi
echo ""

# 第二步：重组docs目录
echo -e "${GREEN}步骤2: 重组docs目录${NC}"

# 功能文档
echo "  移动功能文档..."
[ -f "docs/WORLD_SCAFFOLD_GUIDE.md" ] && git mv docs/WORLD_SCAFFOLD_GUIDE.md docs/features/ && echo "    ✓ WORLD_SCAFFOLD_GUIDE.md"
[ -f "docs/QUEST_SYSTEM.md" ] && git mv docs/QUEST_SYSTEM.md docs/features/ && echo "    ✓ QUEST_SYSTEM.md"
[ -f "docs/GAME_FEATURES.md" ] && git mv docs/GAME_FEATURES.md docs/features/ && echo "    ✓ GAME_FEATURES.md"
[ -f "docs/QUICK_START_WORLD.md" ] && git mv docs/QUICK_START_WORLD.md docs/features/ && echo "    ✓ QUICK_START_WORLD.md"

# 设置文档
echo "  移动设置文档..."
[ -f "docs/SETUP_COMPLETE.md" ] && git mv docs/SETUP_COMPLETE.md docs/setup/ && echo "    ✓ SETUP_COMPLETE.md"
[ -f "docs/LITELLM_PROXY_SETUP.md" ] && git mv docs/LITELLM_PROXY_SETUP.md docs/setup/ && echo "    ✓ LITELLM_PROXY_SETUP.md"
[ -f "docs/CLAUDE_AGENT_SDK_SETUP.md" ] && git mv docs/CLAUDE_AGENT_SDK_SETUP.md docs/setup/ && echo "    ✓ CLAUDE_AGENT_SDK_SETUP.md"
[ -f "docs/LLM_BACKEND_INTEGRATION.md" ] && git mv docs/LLM_BACKEND_INTEGRATION.md docs/setup/ && echo "    ✓ LLM_BACKEND_INTEGRATION.md"
[ -f "docs/WORLD_SYSTEM_INTEGRATION_COMPLETE.md" ] && git mv docs/WORLD_SYSTEM_INTEGRATION_COMPLETE.md docs/setup/ && echo "    ✓ WORLD_SYSTEM_INTEGRATION_COMPLETE.md"
[ -f "docs/LITELLM_PROXY_MIGRATION_COMPLETE.md" ] && git mv docs/LITELLM_PROXY_MIGRATION_COMPLETE.md docs/setup/ && echo "    ✓ LITELLM_PROXY_MIGRATION_COMPLETE.md"

# 实现文档
echo "  移动实现文档..."
[ -f "docs/WORLD_SCAFFOLD_IMPLEMENTATION.md" ] && git mv docs/WORLD_SCAFFOLD_IMPLEMENTATION.md docs/implementation/ && echo "    ✓ WORLD_SCAFFOLD_IMPLEMENTATION.md"
[ -f "docs/CLAUDE_AGENT_SDK_IMPLEMENTATION.md" ] && git mv docs/CLAUDE_AGENT_SDK_IMPLEMENTATION.md docs/implementation/ && echo "    ✓ CLAUDE_AGENT_SDK_IMPLEMENTATION.md"
[ -f "docs/LLM_BACKEND_INTEGRATION_COMPLETE.md" ] && git mv docs/LLM_BACKEND_INTEGRATION_COMPLETE.md docs/implementation/ && echo "    ✓ LLM_BACKEND_INTEGRATION_COMPLETE.md"
[ -f "docs/UI_INTEGRATION_COMPLETE.md" ] && git mv docs/UI_INTEGRATION_COMPLETE.md docs/implementation/ && echo "    ✓ UI_INTEGRATION_COMPLETE.md"
[ -f "docs/IMPLEMENTATION_SUMMARY.md" ] && git mv docs/IMPLEMENTATION_SUMMARY.md docs/implementation/ && echo "    ✓ IMPLEMENTATION_SUMMARY.md"

# 运维文档
echo "  移动运维文档..."
[ -f "docs/START_ALL_WITH_AGENT_GUIDE.md" ] && git mv docs/START_ALL_WITH_AGENT_GUIDE.md docs/operations/ && echo "    ✓ START_ALL_WITH_AGENT_GUIDE.md"
[ -f "docs/LITELLM_AGENT_GUIDE.md" ] && git mv docs/LITELLM_AGENT_GUIDE.md docs/operations/ && echo "    ✓ LITELLM_AGENT_GUIDE.md"
[ -f "docs/LLM_BACKEND_GUIDE.md" ] && git mv docs/LLM_BACKEND_GUIDE.md docs/operations/ && echo "    ✓ LLM_BACKEND_GUIDE.md"
[ -f "docs/LLM_BACKEND_USAGE.md" ] && git mv docs/LLM_BACKEND_USAGE.md docs/operations/ && echo "    ✓ LLM_BACKEND_USAGE.md"
[ -f "docs/DEMO_EXPERIENCE_GUIDE.md" ] && git mv docs/DEMO_EXPERIENCE_GUIDE.md docs/operations/ && echo "    ✓ DEMO_EXPERIENCE_GUIDE.md"

# 故障排除文档
echo "  移动故障排除文档..."
[ -f "docs/TROUBLESHOOTING.md" ] && git mv docs/TROUBLESHOOTING.md docs/troubleshooting/ && echo "    ✓ TROUBLESHOOTING.md"
[ -f "docs/BUG_FIXES.md" ] && git mv docs/BUG_FIXES.md docs/troubleshooting/ && echo "    ✓ BUG_FIXES.md"
[ -f "docs/BUG_FIX_502_GATEWAY.md" ] && git mv docs/BUG_FIX_502_GATEWAY.md docs/troubleshooting/ && echo "    ✓ BUG_FIX_502_GATEWAY.md"
[ -f "docs/QUICK_FIX_CHECKLIST.md" ] && git mv docs/QUICK_FIX_CHECKLIST.md docs/troubleshooting/ && echo "    ✓ QUICK_FIX_CHECKLIST.md"

# 参考文档
echo "  移动参考文档..."
[ -f "docs/QUICK_REFERENCE.md" ] && git mv docs/QUICK_REFERENCE.md docs/reference/ && echo "    ✓ QUICK_REFERENCE.md"
[ -f "docs/IMPLEMENTATION_GAP_ANALYSIS.md" ] && git mv docs/IMPLEMENTATION_GAP_ANALYSIS.md docs/reference/ && echo "    ✓ IMPLEMENTATION_GAP_ANALYSIS.md"
[ -f "docs/PHASE1_COMPLETE.md" ] && git mv docs/PHASE1_COMPLETE.md docs/reference/ && echo "    ✓ PHASE1_COMPLETE.md"
[ -f "docs/CLAUDE_AGENT_SDK_EVALUATION.md" ] && git mv docs/CLAUDE_AGENT_SDK_EVALUATION.md docs/reference/ && echo "    ✓ CLAUDE_AGENT_SDK_EVALUATION.md"
echo ""

# 第三步：重组scripts目录
echo -e "${GREEN}步骤3: 重组scripts目录${NC}"

# 启动脚本
echo "  移动启动脚本..."
[ -f "start_all_with_agent.sh" ] && git mv start_all_with_agent.sh scripts/start/ && echo "    ✓ start_all_with_agent.sh"
[ -f "start_litellm_proxy.sh" ] && git mv start_litellm_proxy.sh scripts/start/ && echo "    ✓ start_litellm_proxy.sh"
[ -f "stop_all.sh" ] && git mv stop_all.sh scripts/start/ && echo "    ✓ stop_all.sh"
[ -f "run.sh" ] && git mv run.sh scripts/start/ && echo "    ✓ run.sh"

# 开发工具脚本
echo "  移动开发工具脚本..."
[ -f "check_services.sh" ] && git mv check_services.sh scripts/dev/ && echo "    ✓ check_services.sh"
[ -f "view_logs.sh" ] && git mv view_logs.sh scripts/dev/ && echo "    ✓ view_logs.sh"

# 测试脚本
echo "  移动测试脚本..."
[ -f "test_proxy_e2e.sh" ] && git mv test_proxy_e2e.sh scripts/test/ && echo "    ✓ test_proxy_e2e.sh"
echo ""

# 第四步：重组tests目录
echo -e "${GREEN}步骤4: 重组tests目录${NC}"

# 端到端测试
echo "  移动端到端测试..."
[ -f "test_chat_stream.py" ] && git mv test_chat_stream.py tests/e2e/ && echo "    ✓ test_chat_stream.py"
[ -f "test_litellm_api.py" ] && git mv test_litellm_api.py tests/e2e/ && echo "    ✓ test_litellm_api.py"
[ -f "test_llm_backend.py" ] && git mv test_llm_backend.py tests/e2e/ && echo "    ✓ test_llm_backend.py"
[ -f "test_world_scaffold.py" ] && git mv test_world_scaffold.py tests/e2e/ && echo "    ✓ test_world_scaffold.py"
echo ""

# 第五步：重组web/backend目录
echo -e "${GREEN}步骤5: 重组web/backend目录${NC}"
cd web/backend

# API文件
echo "  移动API文件..."
[ -f "chat_api.py" ] && git mv chat_api.py api/ && echo "    ✓ chat_api.py"
[ -f "generation_api.py" ] && git mv generation_api.py api/ && echo "    ✓ generation_api.py"
[ -f "game_api.py" ] && git mv game_api.py api/ && echo "    ✓ game_api.py"
[ -f "world_api.py" ] && git mv world_api.py api/ && echo "    ✓ world_api.py"

# 服务文件
echo "  移动服务文件..."
[ -f "agent_generation.py" ] && git mv agent_generation.py services/ && echo "    ✓ agent_generation.py"
[ -f "world_generator.py" ] && git mv world_generator.py services/ && echo "    ✓ world_generator.py"
[ -f "scene_refinement.py" ] && git mv scene_refinement.py services/ && echo "    ✓ scene_refinement.py"

# 游戏引擎文件
echo "  移动游戏引擎文件..."
[ -f "game_engine.py" ] && git mv game_engine.py game/ && echo "    ✓ game_engine.py"
[ -f "game_tools.py" ] && git mv game_tools.py game/ && echo "    ✓ game_tools.py"

# 模型文件
echo "  移动模型文件..."
[ -f "world_models.py" ] && git mv world_models.py models/ && echo "    ✓ world_models.py"

# 数据库文件
echo "  移动数据库文件..."
[ -f "world_db.py" ] && git mv world_db.py database/ && echo "    ✓ world_db.py"

cd "$PROJECT_ROOT"
echo ""

# 创建__init__.py文件
echo -e "${GREEN}步骤6: 创建__init__.py文件${NC}"
touch web/backend/api/__init__.py
touch web/backend/services/__init__.py
touch web/backend/models/__init__.py
touch web/backend/database/__init__.py
touch tests/e2e/__init__.py
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
echo "详细步骤请参考: docs/DIRECTORY_REORGANIZATION_PLAN.md"
