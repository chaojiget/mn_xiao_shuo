#!/bin/bash

# 日志查看脚本
# 用于实时查看后端和前端的日志输出

echo "🔍 实时日志监控"
echo "============================================"
echo ""
echo "选择要查看的日志:"
echo "  1) 后端日志 (logs/backend.log)"
echo "  2) 前端日志 (logs/frontend.log)"
echo "  3) 同时查看两个日志"
echo "  4) 显示最近50行后端日志"
echo "  5) 显示最近50行前端日志"
echo ""
read -p "请输入选项 (1-5): " choice

case $choice in
    1)
        echo "📊 实时监控后端日志 (Ctrl+C 退出)..."
        tail -f logs/backend.log
        ;;
    2)
        echo "🎨 实时监控前端日志 (Ctrl+C 退出)..."
        tail -f logs/frontend.log
        ;;
    3)
        echo "📊🎨 实时监控所有日志 (Ctrl+C 退出)..."
        tail -f logs/backend.log logs/frontend.log
        ;;
    4)
        echo "📊 最近50行后端日志:"
        echo "============================================"
        tail -50 logs/backend.log
        ;;
    5)
        echo "🎨 最近50行前端日志:"
        echo "============================================"
        tail -50 logs/frontend.log
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
