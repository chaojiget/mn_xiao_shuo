"""测试存档元数据提取"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "web" / "backend"))

from services.save_service import SaveService
import json

def test_save_metadata_extraction():
    """测试元数据提取是否正确"""

    # 模拟游戏状态（实际格式）
    game_state = {
        "version": "1.0.0",
        "turn_number": 0,  # 这个字段可能不准确
        "player": {
            "hp": 85,
            "maxHp": 100,
            "stamina": 90,
            "maxStamina": 100,
            "location": "起点",
            "inventory": [
                {"id": "gold_coin", "name": "金币", "quantity": 50}
            ],
            "money": 0
        },
        "world": {
            "time": 15,  # 实际回合数
            "flags": {},
            "discoveredLocations": ["起点", "森林"],
            "variables": {}
        },
        "map": {
            "currentNodeId": "start",
            "nodes": [
                {
                    "id": "start",
                    "name": "起始广场",
                    "shortDesc": "一片空旷的广场",
                    "discovered": True
                },
                {
                    "id": "forest",
                    "name": "迷雾森林",
                    "shortDesc": "神秘的森林",
                    "discovered": True
                }
            ],
            "edges": []
        },
        "quests": [],
        "log": []
    }

    # 创建临时数据库（使用内存数据库）
    import sqlite3
    import tempfile

    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name

    # 初始化数据库schema
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS game_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            slot_id INTEGER NOT NULL CHECK(slot_id >= 0 AND slot_id <= 10),
            save_name TEXT NOT NULL,
            game_state TEXT NOT NULL,
            metadata TEXT,
            screenshot_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, slot_id)
        );
    """)
    conn.commit()
    conn.close()

    # 测试保存
    save_service = SaveService(db_path)
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="测试存档",
        game_state=game_state
    )

    print("=" * 60)
    print("存档元数据提取测试")
    print("=" * 60)

    # 获取存档
    saves = save_service.get_saves("test_user")
    assert len(saves) == 1, "应该有1个存档"

    save = saves[0]
    metadata = save['metadata']

    print(f"\n✅ 保存成功，存档ID: {save_id}")
    print(f"\n提取的元数据:")
    print(f"  回合数: {metadata['turn_number']} (期望: 15)")
    print(f"  位置: {metadata['location']} (期望: '起始广场')")
    print(f"  HP: {metadata['hp']}/{metadata['max_hp']} (期望: 85/100)")
    print(f"  等级: {metadata['level']}")

    # 验证
    errors = []
    if metadata['turn_number'] != 15:
        errors.append(f"❌ 回合数错误: {metadata['turn_number']} != 15")
    else:
        print(f"\n✅ 回合数正确: {metadata['turn_number']}")

    if metadata['location'] != "起始广场":
        errors.append(f"❌ 位置错误: {metadata['location']} != '起始广场'")
    else:
        print(f"✅ 位置正确: {metadata['location']}")

    if metadata['hp'] != 85 or metadata['max_hp'] != 100:
        errors.append(f"❌ HP错误: {metadata['hp']}/{metadata['max_hp']} != 85/100")
    else:
        print(f"✅ HP正确: {metadata['hp']}/{metadata['max_hp']}")

    # 清理
    import os
    os.unlink(db_path)

    if errors:
        print(f"\n❌ 测试失败:")
        for error in errors:
            print(f"  {error}")
        return False
    else:
        print(f"\n✅ 所有测试通过！")
        return True

if __name__ == "__main__":
    success = test_save_metadata_extraction()
    sys.exit(0 if success else 1)
