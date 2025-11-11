#!/bin/bash
# 快速测试 DM Agent 工具调用可见性
# 测试增强的 Checkpoint 模式是否正确捕获工具调用事件

set -e

echo "========================================="
echo "🧪 DM Agent 工具调用测试"
echo "========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查后端服务
echo -n "检查后端服务..."
if curl -s http://localhost:8000/api/dm/health > /dev/null 2>&1; then
    echo -e " ${GREEN}✅ 运行中${NC}"
else
    echo -e " ${RED}❌ 未运行${NC}"
    echo "请先启动后端: ./scripts/start/start_all_with_agent.sh"
    exit 1
fi

# 测试用例
SESSION_ID="test_$(date +%s)"
API_URL="http://localhost:8000/api/game/turn/stream"

echo ""
echo "会话ID: $SESSION_ID"
echo ""

# 测试用例 1: 获取玩家状态 (应触发 get_player_state 工具)
echo "========================================="
echo "测试用例 1: 获取玩家状态"
echo "========================================="
echo ""

TEST_REQUEST_1='{
  "playerInput": "查看我的状态",
  "currentState": {
    "worldName": "测试世界",
    "playerCharacter": {
      "name": "测试玩家",
      "hp": 100,
      "maxHp": 100,
      "level": 1
    },
    "currentLocation": "新手村",
    "turn_number": 1,
    "log": []
  }
}'

echo "输入: 查看我的状态"
echo "预期工具调用: get_player_state"
echo ""

# 发送请求并捕获响应
RESPONSE_1=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$TEST_REQUEST_1")

# 检查是否包含工具调用事件
if echo "$RESPONSE_1" | grep -q '"type":"tool_call"'; then
    echo -e "${GREEN}✅ 检测到工具调用事件${NC}"
    echo "$RESPONSE_1" | grep '"type":"tool_call"' | head -1 | jq -r '.tool' 2>/dev/null || echo "工具名称解析失败"
else
    echo -e "${RED}❌ 未检测到工具调用事件${NC}"
    echo "响应片段:"
    echo "$RESPONSE_1" | head -20
fi

echo ""

# 测试用例 2: 添加物品 (应触发 add_item 工具)
echo "========================================="
echo "测试用例 2: 添加物品"
echo "========================================="
echo ""

TEST_REQUEST_2='{
  "playerInput": "我找到了一把剑",
  "currentState": {
    "worldName": "测试世界",
    "playerCharacter": {
      "name": "测试玩家",
      "hp": 100,
      "maxHp": 100,
      "level": 1,
      "inventory": []
    },
    "currentLocation": "新手村",
    "turn_number": 2,
    "log": []
  }
}'

echo "输入: 我找到了一把剑"
echo "预期工具调用: add_item"
echo ""

RESPONSE_2=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$TEST_REQUEST_2")

if echo "$RESPONSE_2" | grep -q '"type":"tool_call"'; then
    echo -e "${GREEN}✅ 检测到工具调用事件${NC}"

    # 尝试提取工具名称
    TOOL_NAME=$(echo "$RESPONSE_2" | grep -o '"tool":"[^"]*"' | head -1 | cut -d'"' -f4)
    if [ -n "$TOOL_NAME" ]; then
        echo "工具名称: $TOOL_NAME"
    fi

    # 检查是否有工具返回结果
    if echo "$RESPONSE_2" | grep -q '"type":"tool_result"'; then
        echo -e "${GREEN}✅ 检测到工具返回结果${NC}"
    else
        echo -e "${YELLOW}⚠️  未检测到工具返回结果${NC}"
    fi
else
    echo -e "${RED}❌ 未检测到工具调用事件${NC}"
fi

echo ""

# 测试用例 3: 投掷检定 (应触发 roll_check 工具)
echo "========================================="
echo "测试用例 3: 投掷检定"
echo "========================================="
echo ""

TEST_REQUEST_3='{
  "playerInput": "我尝试破解这个机关(力量检定)",
  "currentState": {
    "worldName": "测试世界",
    "playerCharacter": {
      "name": "测试玩家",
      "hp": 100,
      "maxHp": 100,
      "level": 1,
      "attributes": {
        "strength": 15
      }
    },
    "currentLocation": "地牢入口",
    "turn_number": 3,
    "log": []
  }
}'

echo "输入: 我尝试破解这个机关(力量检定)"
echo "预期工具调用: roll_check"
echo ""

RESPONSE_3=$(curl -s -X POST "$API_URL" \
  -H "Content-Type: application/json" \
  -d "$TEST_REQUEST_3")

if echo "$RESPONSE_3" | grep -q '"type":"tool_call"'; then
    echo -e "${GREEN}✅ 检测到工具调用事件${NC}"

    # 检查是否是 roll_check
    if echo "$RESPONSE_3" | grep -q '"tool":"roll_check"'; then
        echo -e "${GREEN}✅ 正确的工具: roll_check${NC}"
    else
        echo -e "${YELLOW}⚠️  工具名称不匹配${NC}"
    fi
else
    echo -e "${RED}❌ 未检测到工具调用事件${NC}"
fi

echo ""

# 测试用例 4: 思考过程检测 (仅限 Kimi K2)
echo "========================================="
echo "测试用例 4: 思考过程检测"
echo "========================================="
echo ""

# 读取当前模型
CURRENT_MODEL=$(grep "DEFAULT_MODEL=" .env 2>/dev/null | cut -d'=' -f2 | tr -d ' "' || echo "未设置")

echo "当前模型: $CURRENT_MODEL"

if echo "$CURRENT_MODEL" | grep -q "kimi-k2"; then
    echo -e "${GREEN}✅ 使用 Kimi K2 模型，支持思考过程${NC}"

    TEST_REQUEST_4='{
      "playerInput": "这个房间有什么可疑之处？",
      "currentState": {
        "worldName": "测试世界",
        "playerCharacter": {
          "name": "测试玩家",
          "hp": 100,
          "maxHp": 100,
          "level": 1
        },
        "currentLocation": "神秘房间",
        "turn_number": 4,
        "log": []
      }
    }'

    echo ""
    echo "输入: 这个房间有什么可疑之处？"
    echo "预期: thinking_start, thinking_step, thinking_end 事件"
    echo ""

    RESPONSE_4=$(curl -s -X POST "$API_URL" \
      -H "Content-Type: application/json" \
      -d "$TEST_REQUEST_4")

    # 检查思考过程标记
    THINKING_START=$(echo "$RESPONSE_4" | grep -c '"type":"thinking_start"' || echo "0")
    THINKING_STEP=$(echo "$RESPONSE_4" | grep -c '"type":"thinking_step"' || echo "0")
    THINKING_END=$(echo "$RESPONSE_4" | grep -c '"type":"thinking_end"' || echo "0")

    echo "thinking_start: $THINKING_START"
    echo "thinking_step: $THINKING_STEP"
    echo "thinking_end: $THINKING_END"

    if [ "$THINKING_START" -gt 0 ] || [ "$THINKING_STEP" -gt 0 ]; then
        echo -e "${GREEN}✅ 检测到思考过程事件${NC}"
    else
        echo -e "${YELLOW}⚠️  未检测到思考过程事件（模型可能未输出思考标记）${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  当前模型不支持思考过程，跳过测试${NC}"
    echo "提示: 切换到 Kimi K2 模型以测试思考过程"
    echo "修改 .env: DEFAULT_MODEL=moonshotai/kimi-k2-thinking"
fi

echo ""

# 总结
echo "========================================="
echo "📊 测试总结"
echo "========================================="
echo ""

# 简单统计
TOTAL_TESTS=3
PASSED=0

if echo "$RESPONSE_1" | grep -q '"type":"tool_call"'; then
    PASSED=$((PASSED + 1))
fi

if echo "$RESPONSE_2" | grep -q '"type":"tool_call"'; then
    PASSED=$((PASSED + 1))
fi

if echo "$RESPONSE_3" | grep -q '"type":"tool_call"'; then
    PASSED=$((PASSED + 1))
fi

echo "工具调用测试: $PASSED / $TOTAL_TESTS 通过"

if [ $PASSED -eq $TOTAL_TESTS ]; then
    echo -e "${GREEN}✅ 所有测试通过！增强 Checkpoint 模式工作正常${NC}"
    exit 0
else
    echo -e "${RED}❌ 部分测试失败，请检查实现${NC}"
    echo ""
    echo "调试建议:"
    echo "1. 查看后端日志: tail -f logs/app.log | grep '检测到工具'"
    echo "2. 检查 dm_agent_langchain.py:340-386 实现"
    echo "3. 验证 WebSocket 连接是否正常"
    exit 1
fi
