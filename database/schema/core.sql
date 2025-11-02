-- SQLite 数据库 Schema
-- 长篇小说生成系统

-- 1. 世界状态表
CREATE TABLE IF NOT EXISTS world_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id TEXT NOT NULL,                -- 小说ID
    turn INTEGER NOT NULL,                 -- 回合数
    timestamp INTEGER NOT NULL,            -- 游戏内时间戳
    state_json TEXT NOT NULL,              -- 完整状态JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(novel_id, turn)
);

CREATE INDEX idx_world_states_novel ON world_states(novel_id);
CREATE INDEX idx_world_states_turn ON world_states(novel_id, turn);

-- 2. 事件节点表
CREATE TABLE IF NOT EXISTS event_nodes (
    id TEXT PRIMARY KEY,                   -- 事件ID (如 ARC-1:E001)
    novel_id TEXT NOT NULL,                -- 所属小说
    arc_id TEXT NOT NULL,                  -- 所属事件线
    title TEXT NOT NULL,                   -- 标题
    goal TEXT NOT NULL,                    -- 目标

    -- 前置条件
    prerequisites TEXT,                    -- JSON数组: 前置事件IDs
    required_flags TEXT,                   -- JSON对象: 需要的标志位
    required_resources TEXT,               -- JSON对象: 需要的资源

    -- 效果
    effects TEXT,                          -- JSON对象: 状态变化
    rewards TEXT,                          -- JSON对象: 奖励

    -- 评分指标
    tension_delta REAL DEFAULT 0.0,

    -- 可玩性指标
    puzzle_density REAL DEFAULT 0.0,
    skill_checks_variety REAL DEFAULT 0.0,
    failure_grace REAL DEFAULT 0.0,
    hint_latency REAL DEFAULT 0.0,
    exploit_resistance REAL DEFAULT 0.0,
    reward_loop REAL DEFAULT 0.0,

    -- 叙事指标
    arc_progress REAL DEFAULT 0.0,
    theme_echo REAL DEFAULT 0.0,
    conflict_gradient REAL DEFAULT 0.0,
    payoff_debt REAL DEFAULT 0.0,
    scene_specificity REAL DEFAULT 0.0,
    pacing_smoothness REAL DEFAULT 0.0,

    -- 玄幻专用指标
    upgrade_frequency REAL DEFAULT 0.0,
    resource_gain REAL DEFAULT 0.0,
    combat_variety REAL DEFAULT 0.0,
    reversal_satisfaction REAL DEFAULT 0.0,
    faction_expansion REAL DEFAULT 0.0,

    -- 线索经济
    setups TEXT,                           -- JSON数组: 埋下的伏笔IDs
    clues TEXT,                            -- JSON数组: 提供的线索IDs
    payoffs TEXT,                          -- JSON数组: 偿还的伏笔IDs

    -- 状态
    status TEXT DEFAULT 'pending',         -- pending/in_progress/completed/failed/skipped
    attempts INTEGER DEFAULT 0,

    -- 元数据
    description TEXT,
    tags TEXT,                             -- JSON数组

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_nodes_novel ON event_nodes(novel_id);
CREATE INDEX idx_event_nodes_arc ON event_nodes(arc_id);
CREATE INDEX idx_event_nodes_status ON event_nodes(status);

-- 3. 事件线表
CREATE TABLE IF NOT EXISTS event_arcs (
    id TEXT PRIMARY KEY,                   -- 事件线ID (如 ARC-1)
    novel_id TEXT NOT NULL,                -- 所属小说
    title TEXT NOT NULL,                   -- 标题
    description TEXT,                      -- 描述
    type TEXT DEFAULT 'main',              -- main/side/hidden

    -- 进度
    current_event_idx INTEGER DEFAULT 0,
    completed INTEGER DEFAULT 0,           -- 0=false, 1=true

    -- 主题
    themes TEXT,                           -- JSON数组

    -- 元数据
    estimated_chapters TEXT,               -- 预计章节数

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_event_arcs_novel ON event_arcs(novel_id);
CREATE INDEX idx_event_arcs_type ON event_arcs(type);

-- 4. 线索注册表
CREATE TABLE IF NOT EXISTS clues (
    id TEXT PRIMARY KEY,                   -- 线索ID
    novel_id TEXT NOT NULL,                -- 所属小说
    content TEXT NOT NULL,                 -- 线索内容
    type TEXT NOT NULL,                    -- 类型 (data_anomaly/witness/item等)

    -- 证据链
    evidence_ids TEXT,                     -- JSON数组: 证据IDs
    verification_method TEXT,              -- 验证方法

    -- 状态
    status TEXT DEFAULT 'hidden',          -- hidden/discovered/verified/misleading

    -- 关联
    related_event TEXT,                    -- 关联的事件ID
    leads_to TEXT,                         -- JSON数组: 指向的其他线索IDs

    -- 发现条件
    discovery_requirements TEXT,           -- JSON对象

    -- 时间
    discovered_at TIMESTAMP,
    verified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_clues_novel ON clues(novel_id);
CREATE INDEX idx_clues_status ON clues(status);

-- 5. 证据表
CREATE TABLE IF NOT EXISTS evidence (
    id TEXT PRIMARY KEY,                   -- 证据ID
    novel_id TEXT NOT NULL,                -- 所属小说
    content TEXT NOT NULL,                 -- 证据内容
    type TEXT NOT NULL,                    -- data/testimony/physical/document
    source TEXT,                           -- 来源

    -- 可信度
    credibility REAL DEFAULT 1.0,          -- 0.0-1.0

    -- 关联
    related_clues TEXT,                    -- JSON数组: 相关线索IDs
    related_events TEXT,                   -- JSON数组: 相关事件IDs

    -- 元数据
    location TEXT,                         -- 发现地点
    discovered_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_evidence_novel ON evidence(novel_id);

-- 6. 伏笔债务表
CREATE TABLE IF NOT EXISTS setup_debts (
    id TEXT PRIMARY KEY,                   -- 伏笔ID
    novel_id TEXT NOT NULL,                -- 所属小说
    description TEXT NOT NULL,             -- 伏笔描述
    setup_event_id TEXT NOT NULL,          -- 埋伏笔的事件ID

    -- SLA
    sla_deadline INTEGER NOT NULL,         -- 必须在多少回合内偿还
    setup_turn INTEGER NOT NULL,           -- 埋下伏笔的回合

    -- 偿还
    payoff_event_id TEXT,                  -- 偿还伏笔的事件ID
    payoff_turn INTEGER,                   -- 偿还回合

    -- 状态
    status TEXT DEFAULT 'pending',         -- pending/hinted/paid_off/overdue

    -- 优先级
    priority REAL DEFAULT 1.0,

    -- 类型
    type TEXT DEFAULT 'plot',              -- plot/character/world

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_setup_debts_novel ON setup_debts(novel_id);
CREATE INDEX idx_setup_debts_status ON setup_debts(status, sla_deadline);

-- 7. 执行日志表
CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id TEXT NOT NULL,                -- 所属小说
    event_id TEXT,                         -- 执行的事件ID
    turn INTEGER NOT NULL,                 -- 回合数

    -- 执行内容
    action_queue TEXT,                     -- JSON: 动作队列
    result TEXT,                           -- JSON: 执行结果

    -- 状态
    success INTEGER DEFAULT 0,             -- 0=失败, 1=成功
    stall_rounds INTEGER DEFAULT 0,        -- 停滞回合数

    -- 元数据
    duration_ms INTEGER,                   -- 执行耗时(毫秒)
    model_used TEXT,                       -- 使用的模型
    tokens_used INTEGER,                   -- 消耗的tokens

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_execution_logs_novel ON execution_logs(novel_id);
CREATE INDEX idx_execution_logs_event ON execution_logs(event_id);
CREATE INDEX idx_execution_logs_turn ON execution_logs(novel_id, turn);

-- 8. 小说元数据表
CREATE TABLE IF NOT EXISTS novels (
    id TEXT PRIMARY KEY,                   -- 小说ID
    title TEXT NOT NULL,                   -- 标题
    novel_type TEXT NOT NULL,              -- scifi/xianxia
    preference TEXT DEFAULT 'hybrid',      -- playability/narrative/hybrid

    -- 设定
    setting_json TEXT NOT NULL,            -- 完整设定JSON

    -- 进度
    current_turn INTEGER DEFAULT 0,
    total_chapters INTEGER DEFAULT 0,

    -- 状态
    status TEXT DEFAULT 'active',          -- active/paused/completed

    -- 统计
    total_tokens INTEGER DEFAULT 0,
    total_cost REAL DEFAULT 0.0,

    -- 时间
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_novels_status ON novels(status);
CREATE INDEX idx_novels_type ON novels(novel_type);

-- 9. 章节内容表
CREATE TABLE IF NOT EXISTS chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id TEXT NOT NULL,                -- 所属小说
    chapter_num INTEGER NOT NULL,          -- 章节号
    title TEXT,                            -- 章节标题

    -- 内容
    content TEXT NOT NULL,                 -- 章节内容
    word_count INTEGER,                    -- 字数

    -- 关联
    event_ids TEXT,                        -- JSON数组: 相关事件IDs

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(novel_id, chapter_num)
);

CREATE INDEX idx_chapters_novel ON chapters(novel_id);

-- 10. 角色表 (可选,用于快速查询)
CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY,                   -- 角色ID
    novel_id TEXT NOT NULL,                -- 所属小说
    name TEXT NOT NULL,                    -- 名字
    role TEXT,                             -- protagonist/ally/enemy/neutral

    -- 属性(快照)
    attributes TEXT,                       -- JSON对象
    resources TEXT,                        -- JSON对象

    -- 当前状态
    location TEXT,
    status TEXT DEFAULT 'normal',

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_characters_novel ON characters(novel_id);
CREATE INDEX idx_characters_role ON characters(role);
