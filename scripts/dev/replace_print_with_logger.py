#!/usr/bin/env python3
"""
批量替换 print() 为 logger 的脚本

使用方式:
    uv run python scripts/dev/replace_print_with_logger.py [--dry-run]

功能:
    1. 查找所有包含 print() 的 Python 文件
    2. 为每个文件添加 logger 导入（如果没有）
    3. 替换 print() 为 logger.info/debug/error
    4. 保留原始备份到 .bak 文件
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple


# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
BACKEND_DIR = PROJECT_ROOT / "web" / "backend"

# 要排除的目录和文件
EXCLUDE_DIRS = {
    ".venv", "venv", "__pycache__", ".git", "node_modules",
    "_deprecated", ".mypy_cache", "build", "dist"
}

EXCLUDE_FILES = {
    "__init__.py",
}


def should_skip(file_path: Path) -> bool:
    """判断是否应该跳过该文件"""
    # 检查路径中是否包含排除的目录
    for part in file_path.parts:
        if part in EXCLUDE_DIRS:
            return True

    # 检查文件名
    if file_path.name in EXCLUDE_FILES:
        return True

    return False


def find_print_files() -> List[Path]:
    """查找所有包含 print() 的 Python 文件"""
    files = []

    if not BACKEND_DIR.exists():
        print(f"❌ 后端目录不存在: {BACKEND_DIR}")
        return files

    for py_file in BACKEND_DIR.rglob("*.py"):
        if should_skip(py_file):
            continue

        try:
            content = py_file.read_text(encoding="utf-8")
            if "print(" in content:
                files.append(py_file)
        except Exception as e:
            print(f"⚠️  无法读取文件 {py_file}: {e}")

    return files


def count_prints(content: str) -> int:
    """统计 print 语句数量"""
    # 匹配 print(...) 但不匹配注释中的
    pattern = r'^\s*print\('
    count = 0
    for line in content.split('\n'):
        # 跳过注释行
        if line.strip().startswith('#'):
            continue
        if re.search(pattern, line):
            count += 1
    return count


def has_logger_import(content: str) -> bool:
    """检查是否已经导入 logger"""
    patterns = [
        r'from utils\.logger import get_logger',
        r'import logging',
        r'logger = get_logger',
        r'logger = logging\.getLogger'
    ]
    return any(re.search(pattern, content) for pattern in patterns)


def add_logger_import(content: str) -> str:
    """添加 logger 导入"""
    if has_logger_import(content):
        return content

    # 查找最后一个导入语句的位置
    lines = content.split('\n')
    import_end = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        # 跳过文档字符串
        if i < 3 and (stripped.startswith('"""') or stripped.startswith("'''")):
            continue
        # 找到最后一个 import
        if stripped.startswith('import ') or stripped.startswith('from '):
            import_end = i

    # 在最后一个 import 后面插入
    insert_pos = import_end + 1

    # 如果有 import，在后面加空行
    if import_end > 0:
        logger_import = "\nfrom utils.logger import get_logger\n"
    else:
        # 如果没有 import，在文件开头（文档字符串后）加
        logger_import = "from utils.logger import get_logger\n\n"
        insert_pos = 0
        # 跳过文档字符串
        for i, line in enumerate(lines):
            if i > 0 and not line.strip().startswith('"""') and not line.strip().startswith("'''"):
                insert_pos = i
                break

    lines.insert(insert_pos, logger_import)

    # 添加 logger 创建语句（在导入后）
    logger_create = "logger = get_logger(__name__)\n"
    lines.insert(insert_pos + 1, logger_create)

    return '\n'.join(lines)


def classify_print(line: str) -> str:
    """根据内容判断应该使用哪个日志级别"""
    lower = line.lower()

    # 错误
    if any(keyword in lower for keyword in ['error', '❌', 'failed', '失败', 'exception']):
        return 'error'

    # 警告
    if any(keyword in lower for keyword in ['warning', '⚠️', 'warn', '警告']):
        return 'warning'

    # 调试
    if any(keyword in lower for keyword in ['debug', '[debug]', '调试']):
        return 'debug'

    # 默认 info
    return 'info'


def replace_print_statements(content: str) -> Tuple[str, int]:
    """替换 print() 为 logger.xxx()"""
    lines = content.split('\n')
    replaced_count = 0

    for i, line in enumerate(lines):
        # 跳过注释
        if line.strip().startswith('#'):
            continue

        # 查找 print(...)
        if 'print(' in line:
            # 提取缩进
            indent = len(line) - len(line.lstrip())
            indent_str = line[:indent]

            # 判断日志级别
            log_level = classify_print(line)

            # 替换 print( 为 logger.xxx(
            new_line = re.sub(
                r'\bprint\(',
                f'logger.{log_level}(',
                line
            )

            lines[i] = new_line
            replaced_count += 1

    return '\n'.join(lines), replaced_count


def process_file(file_path: Path, dry_run: bool = False) -> Tuple[int, int]:
    """
    处理单个文件

    Returns:
        (print_count, replaced_count)
    """
    try:
        content = file_path.read_text(encoding='utf-8')
    except Exception as e:
        print(f"❌ 读取失败 {file_path}: {e}")
        return 0, 0

    print_count = count_prints(content)
    if print_count == 0:
        return 0, 0

    # 添加 logger 导入
    content = add_logger_import(content)

    # 替换 print
    new_content, replaced_count = replace_print_statements(content)

    if dry_run:
        print(f"  [DRY RUN] 会替换 {replaced_count} 个 print")
    else:
        # 备份原文件
        backup_path = file_path.with_suffix('.py.bak')
        file_path.rename(backup_path)

        # 写入新内容
        file_path.write_text(new_content, encoding='utf-8')
        print(f"  ✅ 替换了 {replaced_count} 个 print (备份: {backup_path.name})")

    return print_count, replaced_count


def main():
    """主函数"""
    dry_run = '--dry-run' in sys.argv

    print("=" * 60)
    print("批量替换 print 为 logger")
    print("=" * 60)

    if dry_run:
        print("🔍 DRY RUN 模式（不会实际修改文件）\n")
    else:
        print("⚠️  将修改文件（原文件备份为 .bak）\n")

    # 查找文件
    files = find_print_files()

    if not files:
        print("✅ 没有找到包含 print 的文件")
        return

    print(f"找到 {len(files)} 个包含 print 的文件:\n")

    total_prints = 0
    total_replaced = 0

    for file_path in files:
        rel_path = file_path.relative_to(PROJECT_ROOT)
        print(f"📄 {rel_path}")

        print_count, replaced_count = process_file(file_path, dry_run)
        total_prints += print_count
        total_replaced += replaced_count

    print("\n" + "=" * 60)
    print(f"总计: {len(files)} 个文件, {total_replaced}/{total_prints} 个 print 已替换")
    print("=" * 60)

    if not dry_run:
        print("\n💡 提示:")
        print("  - 原文件已备份为 .bak")
        print("  - 请检查修改后的代码是否正确")
        print("  - 如需恢复: mv file.py.bak file.py")
        print("  - 确认无误后: find . -name '*.py.bak' -delete")


if __name__ == "__main__":
    main()
