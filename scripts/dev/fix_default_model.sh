#!/bin/bash

# 批量替换所有文件中的默认模型为 deepseek/deepseek-v3.1-terminus
# 这个脚本会替换所有 kimi-k2-thinking 为 deepseek-v3.1-terminus

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}修复默认模型配置${NC}"
echo -e "${YELLOW}========================================${NC}"

# 查找所有需要替换的文件
FILES=$(grep -r "kimi-k2-thinking" web/backend --include="*.py" -l || true)

if [ -z "$FILES" ]; then
    echo -e "${GREEN}✅ 没有找到需要替换的文件${NC}"
    exit 0
fi

echo -e "${YELLOW}找到以下文件需要替换:${NC}"
echo "$FILES"
echo ""

# 批量替换
for file in $FILES; do
    echo -e "${YELLOW}处理: $file${NC}"

    # macOS 使用 sed -i ''，Linux 使用 sed -i
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' 's/moonshotai\/kimi-k2-thinking/deepseek\/deepseek-v3.1-terminus/g' "$file"
    else
        sed -i 's/moonshotai\/kimi-k2-thinking/deepseek\/deepseek-v3.1-terminus/g' "$file"
    fi

    echo -e "${GREEN}  ✅ 已替换${NC}"
done

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 所有文件已处理完成${NC}"
echo -e "${GREEN}========================================${NC}"
