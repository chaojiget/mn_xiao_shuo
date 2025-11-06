-- ============================================================
-- 世界生成系统数据库 Schema
-- 用于世界预生成、管理、快照与 Fog of War
-- ============================================================

-- ============ 世界表 ============

CREATE TABLE IF NOT EXISTS worlds (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    seed INTEGER NOT NULL,
    json_gz BLOB NOT NULL,               -- gzip 压缩的 WorldPack JSON
    index_version INTEGER DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'draft', -- draft/published/locked
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_worlds_status ON worlds(status);
CREATE INDEX IF NOT EXISTS idx_worlds_updated ON worlds(updated_at DESC);


-- ============ 世界快照 ============

CREATE TABLE IF NOT EXISTS world_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,
    tag TEXT NOT NULL,                   -- 用户自定义标签
    json_gz BLOB NOT NULL,               -- 快照的 WorldPack JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_snapshots_world ON world_snapshots(world_id);
CREATE INDEX IF NOT EXISTS idx_snapshots_created ON world_snapshots(created_at DESC);


-- ============ 生成任务 ============

CREATE TABLE IF NOT EXISTS world_generation_jobs (
    id TEXT PRIMARY KEY,
    world_id TEXT NOT NULL,
    phase TEXT NOT NULL DEFAULT 'QUEUED', -- QUEUED/OUTLINE/LOCATIONS/.../READY/FAILED
    progress REAL DEFAULT 0.0,            -- 0.0-1.0
    error TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_world ON world_generation_jobs(world_id);
CREATE INDEX IF NOT EXISTS idx_jobs_phase ON world_generation_jobs(phase);


-- ============ 向量知识库 ============

CREATE TABLE IF NOT EXISTS world_kb (
    id TEXT PRIMARY KEY,
    world_id TEXT NOT NULL,
    kind TEXT NOT NULL,                   -- npc/lore
    ref_id TEXT NOT NULL,                 -- npc.id 或 lore key
    content TEXT NOT NULL,
    embedding BLOB NOT NULL,              -- 向量嵌入（序列化）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (world_id) REFERENCES worlds(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_kb_world_kind ON world_kb(world_id, kind);
CREATE INDEX IF NOT EXISTS idx_kb_ref ON world_kb(ref_id);


-- ============ 世界发现（Fog of War）============

CREATE TABLE IF NOT EXISTS world_discovery (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    world_id TEXT NOT NULL,
    chunk_x INTEGER NOT NULL,             -- 地图格子坐标
    chunk_y INTEGER NOT NULL,
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(session_id, world_id, chunk_x, chunk_y)
);

CREATE INDEX IF NOT EXISTS idx_discovery_session ON world_discovery(session_id, world_id);
CREATE INDEX IF NOT EXISTS idx_discovery_chunk ON world_discovery(world_id, chunk_x, chunk_y);


-- ============ 游戏事件溯源 ============

CREATE TABLE IF NOT EXISTS game_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    turn INTEGER NOT NULL,
    action TEXT NOT NULL,                 -- 工具名称
    payload TEXT NOT NULL,                -- JSON 参数
    result TEXT NOT NULL,                 -- JSON 结果
    latency_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_events_session ON game_events(session_id, turn);
CREATE INDEX IF NOT EXISTS idx_events_action ON game_events(action);
CREATE INDEX IF NOT EXISTS idx_events_created ON game_events(created_at DESC);


-- ============ 默认世界配置 ============

CREATE TABLE IF NOT EXISTS system_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 插入默认配置
INSERT OR IGNORE INTO system_config (key, value) VALUES ('default_world_id', '');
