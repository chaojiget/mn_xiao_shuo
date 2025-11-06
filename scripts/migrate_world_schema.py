#!/usr/bin/env python3
"""
世界生成系统数据库迁移脚本
应用 world_generation.sql schema 到数据库
"""

import sqlite3
import sys
from pathlib import Path


def main():
    # 项目根目录
    project_root = Path(__file__).parent.parent
    db_path = project_root / "data" / "sqlite" / "novel.db"
    schema_path = project_root / "database" / "schema" / "world_generation.sql"

    # 确保数据库目录存在
    db_path.parent.mkdir(parents=True, exist_ok=True)

    # 检查 schema 文件
    if not schema_path.exists():
        print(f"❌ Schema 文件不存在: {schema_path}")
        sys.exit(1)

    # 读取 schema
    print(f"📖 读取 schema: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # 连接数据库
    print(f"🔗 连接数据库: {db_path}")
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    try:
        # 执行 schema
        print("⚙️  应用 schema...")
        cursor.executescript(schema_sql)

        # 验证表创建
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN (
                'worlds',
                'world_snapshots',
                'world_generation_jobs',
                'world_kb',
                'world_discovery',
                'game_events',
                'system_config'
            )
        """)
        tables = [row[0] for row in cursor.fetchall()]

        print("\n✅ 成功创建的表:")
        for table in tables:
            print(f"   - {table}")

        # 提交
        conn.commit()
        print("\n🎉 数据库迁移成功！")

    except Exception as e:
        print(f"\n❌ 迁移失败: {e}")
        conn.rollback()
        sys.exit(1)

    finally:
        conn.close()


if __name__ == "__main__":
    main()
