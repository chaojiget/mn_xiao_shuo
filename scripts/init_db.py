#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.database import Database


def main():
    """初始化数据库"""
    print("=" * 60)
    print("初始化 SQLite 数据库")
    print("=" * 60)

    # 创建数据库实例
    db = Database()

    print(f"\n数据库路径: {db.db_path}")

    # 检查数据库文件是否存在
    db_file = Path(db.db_path)
    if db_file.exists():
        print(f"⚠️  数据库文件已存在")
        response = input("是否覆盖? (y/N): ")
        if response.lower() != 'y':
            print("取消操作")
            return

    # 初始化 schema
    try:
        with db:
            print("\n正在创建数据库表...")
            db.init_schema()
            print("✅ 数据库表创建成功")

            # 验证表
            cursor = db.conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
            )
            tables = [row[0] for row in cursor.fetchall()]

            print(f"\n创建的表 ({len(tables)} 个):")
            for table in tables:
                print(f"  - {table}")

        print("\n" + "=" * 60)
        print("✅ 数据库初始化完成!")
        print("=" * 60)

        print("\n下一步:")
        print("1. 运行测试: python test_database.py")
        print("2. 开始开发: 参考 NEXT_STEPS.md")

    except Exception as e:
        print(f"\n❌ 数据库初始化失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
