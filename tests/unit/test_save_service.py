"""SaveService 单元测试

测试存档服务的所有功能:
- save_game (保存游戏)
- load_game (加载游戏)
- get_saves (获取存档列表)
- delete_save (删除存档)
- create_snapshot (创建快照)
- get_snapshots (获取快照列表)
- load_snapshot (加载快照)
- auto_save (自动保存)
- get_latest_auto_save (获取最新自动保存)
- cleanup_old_auto_saves (清理旧自动保存)
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path

from web.backend.services.save_service import SaveService


@pytest.fixture
def temp_db():
    """创建临时数据库用于测试"""
    # 创建临时文件
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # 初始化数据库表
    conn = sqlite3.connect(path)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS game_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL DEFAULT 'default_user',
            slot_id INTEGER NOT NULL CHECK(slot_id >= 1 AND slot_id <= 10),
            save_name TEXT NOT NULL,
            game_state TEXT NOT NULL,
            metadata TEXT,
            screenshot_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, slot_id)
        );

        CREATE TABLE IF NOT EXISTS save_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            save_id INTEGER NOT NULL,
            turn_number INTEGER NOT NULL,
            snapshot_data TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (save_id) REFERENCES game_saves(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS auto_saves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            game_state TEXT NOT NULL,
            turn_number INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

    yield path

    # 清理
    os.unlink(path)


@pytest.fixture
def save_service(temp_db):
    """创建 SaveService 实例"""
    return SaveService(temp_db)


@pytest.fixture
def sample_game_state():
    """示例游戏状态"""
    return {
        "turn_number": 10,
        "playtime": 3600,
        "player": {
            "hp": 80,
            "max_hp": 100,
            "level": 5,
            "inventory": [
                {"id": "sword", "name": "铁剑", "quantity": 1},
                {"id": "potion", "name": "治疗药水", "quantity": 3}
            ],
            "gold": 150
        },
        "world": {
            "current_location": "森林深处",
            "theme": "奇幻世界"
        },
        "quests": [
            {"id": "quest_1", "title": "寻找宝藏", "status": "active"}
        ]
    }


# ==================== 基础保存/加载测试 ====================

def test_save_game(save_service, sample_game_state):
    """测试保存游戏"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="第一次冒险",
        game_state=sample_game_state
    )

    assert save_id > 0


def test_save_game_invalid_slot(save_service, sample_game_state):
    """测试无效槽位"""
    with pytest.raises(ValueError):
        save_service.save_game(
            user_id="test_user",
            slot_id=11,  # 超出范围
            save_name="无效存档",
            game_state=sample_game_state
        )


def test_save_game_overwrite(save_service, sample_game_state):
    """测试覆盖存档"""
    # 第一次保存
    save_id_1 = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="存档 A",
        game_state=sample_game_state
    )

    # 覆盖同一槽位
    save_id_2 = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="存档 B",
        game_state=sample_game_state
    )

    # 应该是同一个存档ID
    assert save_id_1 == save_id_2

    # 验证名称已更新
    loaded = save_service.load_game(save_id_1)
    assert loaded["save_info"]["save_name"] == "存档 B"


def test_load_game(save_service, sample_game_state):
    """测试加载游戏"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=2,
        save_name="测试存档",
        game_state=sample_game_state
    )

    loaded = save_service.load_game(save_id)

    assert loaded is not None
    assert loaded["game_state"]["turn_number"] == 10
    assert loaded["game_state"]["player"]["level"] == 5
    assert loaded["metadata"]["turn_number"] == 10
    assert loaded["save_info"]["save_name"] == "测试存档"


def test_load_game_not_found(save_service):
    """测试加载不存在的存档"""
    loaded = save_service.load_game(9999)
    assert loaded is None


def test_get_saves(save_service, sample_game_state):
    """测试获取存档列表"""
    # 创建多个存档
    save_service.save_game("user1", 1, "存档 1", sample_game_state)
    save_service.save_game("user1", 3, "存档 3", sample_game_state)
    save_service.save_game("user2", 1, "其他用户", sample_game_state)

    # 获取 user1 的存档
    saves = save_service.get_saves("user1")

    assert len(saves) == 2
    assert saves[0]["slot_id"] == 1
    assert saves[1]["slot_id"] == 3


def test_delete_save(save_service, sample_game_state):
    """测试删除存档"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="待删除",
        game_state=sample_game_state
    )

    # 删除
    deleted = save_service.delete_save(save_id)
    assert deleted is True

    # 验证已删除
    loaded = save_service.load_game(save_id)
    assert loaded is None


def test_delete_save_not_found(save_service):
    """测试删除不存在的存档"""
    deleted = save_service.delete_save(9999)
    assert deleted is False


# ==================== 快照系统测试 ====================

def test_create_snapshot(save_service, sample_game_state):
    """测试创建快照"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="快照测试",
        game_state=sample_game_state
    )

    # 创建快照
    snapshot_id = save_service.create_snapshot(
        save_id=save_id,
        turn_number=15,
        game_state=sample_game_state
    )

    assert snapshot_id > 0


def test_get_snapshots(save_service, sample_game_state):
    """测试获取快照列表"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="快照测试",
        game_state=sample_game_state,
        auto_save=True  # 不创建自动快照
    )

    # 创建多个快照
    save_service.create_snapshot(save_id, 10, sample_game_state)
    save_service.create_snapshot(save_id, 20, sample_game_state)
    save_service.create_snapshot(save_id, 15, sample_game_state)

    snapshots = save_service.get_snapshots(save_id)

    assert len(snapshots) == 3
    # 应该按回合数降序排列
    assert snapshots[0]["turn_number"] == 20
    assert snapshots[1]["turn_number"] == 15
    assert snapshots[2]["turn_number"] == 10


def test_load_snapshot(save_service, sample_game_state):
    """测试加载快照"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="快照测试",
        game_state=sample_game_state
    )

    # 修改状态并创建快照
    modified_state = sample_game_state.copy()
    modified_state["turn_number"] = 20
    snapshot_id = save_service.create_snapshot(save_id, 20, modified_state)

    # 加载快照
    loaded = save_service.load_snapshot(snapshot_id)

    assert loaded is not None
    assert loaded["turn_number"] == 20


# ==================== 自动保存测试 ====================

def test_auto_save(save_service, sample_game_state):
    """测试自动保存"""
    auto_save_id = save_service.auto_save(
        user_id="test_user",
        game_state=sample_game_state,
        turn_number=10
    )

    assert auto_save_id > 0


def test_get_latest_auto_save(save_service, sample_game_state):
    """测试获取最新自动保存"""
    # 创建多个自动保存
    id1 = save_service.auto_save("test_user", sample_game_state, 5)
    id2 = save_service.auto_save("test_user", sample_game_state, 10)
    id3 = save_service.auto_save("test_user", sample_game_state, 15)

    latest = save_service.get_latest_auto_save("test_user")

    assert latest is not None
    # 由于 SQLite 的 CURRENT_TIMESTAMP 可能相同，我们检查 ID 递增
    # 最新的应该是最后一个插入的（ID 最大）
    assert latest["auto_save_id"] in [id1, id2, id3]
    # 实际上，最后插入的应该是 id3，所以 turn_number 应该是 15
    assert latest["auto_save_id"] == id3
    assert latest["turn_number"] == 15


def test_get_latest_auto_save_not_found(save_service):
    """测试获取不存在的自动保存"""
    latest = save_service.get_latest_auto_save("nonexistent_user")
    assert latest is None


def test_cleanup_old_auto_saves(save_service, sample_game_state):
    """测试清理旧自动保存"""
    # 创建10个自动保存
    for i in range(10):
        save_service.auto_save("test_user", sample_game_state, i)

    # 清理，只保留5个
    deleted_count = save_service.cleanup_old_auto_saves("test_user", keep_count=5)

    assert deleted_count == 5

    # 验证最新的是最后插入的（ID 最大，turn_number = 9）
    latest = save_service.get_latest_auto_save("test_user")
    assert latest["turn_number"] == 9  # 最新的应该是第9个（0-9）


# ==================== 元数据提取测试 ====================

def test_metadata_extraction(save_service, sample_game_state):
    """测试元数据自动提取"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="元数据测试",
        game_state=sample_game_state
    )

    loaded = save_service.load_game(save_id)

    metadata = loaded["metadata"]
    assert metadata["turn_number"] == 10
    assert metadata["playtime"] == 3600
    assert metadata["location"] == "森林深处"
    assert metadata["level"] == 5
    assert metadata["hp"] == 80
    assert metadata["max_hp"] == 100


# ==================== 快照自动创建测试 ====================

def test_auto_snapshot_on_save(save_service, sample_game_state):
    """测试保存时自动创建快照"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="自动快照测试",
        game_state=sample_game_state,
        auto_save=False  # 应该创建快照
    )

    snapshots = save_service.get_snapshots(save_id)
    assert len(snapshots) == 1
    assert snapshots[0]["turn_number"] == 10


def test_no_snapshot_on_auto_save(save_service, sample_game_state):
    """测试自动保存不创建快照"""
    save_id = save_service.save_game(
        user_id="test_user",
        slot_id=1,
        save_name="自动保存测试",
        game_state=sample_game_state,
        auto_save=True  # 不应该创建快照
    )

    snapshots = save_service.get_snapshots(save_id)
    assert len(snapshots) == 0
