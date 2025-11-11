#!/bin/bash
# 测试节奏调控 API

echo "=========================================="
echo "测试节奏调控系统 API"
echo "=========================================="
echo ""

BASE_URL="http://localhost:8000"

# 1. 测试获取所有预设
echo "📋 1. 获取所有节奏预设..."
echo ""
curl -s "$BASE_URL/api/worlds/pacing/presets" | python3 -m json.tool | head -50
echo ""
echo ""

# 2. 测试获取特定预设
echo "⚡ 2. 获取动作快节奏预设..."
echo ""
curl -s "$BASE_URL/api/worlds/pacing/presets/action" | python3 -m json.tool
echo ""
echo ""

echo "📚 3. 获取文学慢节奏预设..."
echo ""
curl -s "$BASE_URL/api/worlds/pacing/presets/literary" | python3 -m json.tool
echo ""
echo ""

echo "🏔️ 4. 获取史诗节奏预设..."
echo ""
curl -s "$BASE_URL/api/worlds/pacing/presets/epic" | python3 -m json.tool
echo ""
echo ""

echo "=========================================="
echo "✅ 测试完成！"
echo "=========================================="
