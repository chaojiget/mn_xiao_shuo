-- 世界脚手架 Schema 扩展
-- 用于世界雏形管理与逐步细化

-- 1. 世界脚手架元数据
CREATE TABLE IF NOT EXISTS world_scaffolds (
    id TEXT PRIMARY KEY,                   -- 世界ID
    novel_id TEXT NOT NULL,                -- 关联小说ID
    name TEXT NOT NULL,                    -- 世界名称

    -- 主题与基调
    theme TEXT NOT NULL,                   -- 主题 (dark survival, epic cultivation, etc.)
    tone TEXT NOT NULL,                    -- 基调 (冷冽压抑、波澜壮阔、etc.)

    -- 设定
    timeline TEXT,                         -- 时间线设定 (JSON)
    tech_magic_level TEXT,                 -- 科技/魔法水平 (JSON)
    geography_climate TEXT,                -- 地理气候 (JSON)
    core_conflicts TEXT,                   -- 核心冲突 (JSON数组)
    forbidden_rules TEXT,                  -- 禁忌规则 (JSON数组)

    -- 风格圣经
    style_bible TEXT NOT NULL,             -- JSON: {tone, sensory[], syntax{}}

    -- 状态
    status TEXT DEFAULT 'draft',           -- draft/published/locked
    version INTEGER DEFAULT 1,

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (novel_id) REFERENCES novels(id)
);

CREATE INDEX idx_world_scaffolds_novel ON world_scaffolds(novel_id);
CREATE INDEX idx_world_scaffolds_status ON world_scaffolds(status);

-- 2. 区域 (Regions)
CREATE TABLE IF NOT EXISTS regions (
    id TEXT PRIMARY KEY,                   -- 区域ID
    world_id TEXT NOT NULL,                -- 所属世界
    name TEXT NOT NULL,                    -- 区域名称

    -- 地理
    biome TEXT NOT NULL,                   -- 生态群落 (冻海海岸、炎漠、迷雾沼泽)
    climate TEXT,                          -- 气候描述
    geography TEXT,                        -- 地形描述

    -- 资源与派系
    resources TEXT,                        -- JSON数组: 主要资源
    factions TEXT,                         -- JSON数组: 派系IDs

    -- 危险与可达性
    danger_level INTEGER DEFAULT 1,        -- 1-10
    travel_difficulty TEXT,                -- 旅行难度描述
    travel_hints TEXT,                     -- JSON数组: 旅行提示

    -- 区域特性
    special_rules TEXT,                    -- JSON数组: 特殊规则
    atmosphere TEXT,                       -- 氛围描述

    -- 状态
    status TEXT DEFAULT 'draft',           -- draft/published/locked
    canon_locked INTEGER DEFAULT 0,        -- 0=可修改, 1=已锁定

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_regions_world ON regions(world_id);
CREATE INDEX idx_regions_danger ON regions(danger_level);
CREATE INDEX idx_regions_status ON regions(status);

-- 3. 地点 (Locations)
CREATE TABLE IF NOT EXISTS locations (
    id TEXT PRIMARY KEY,                   -- 地点ID
    region_id TEXT NOT NULL,               -- 所属区域
    name TEXT NOT NULL,                    -- 地点名称
    type TEXT NOT NULL,                    -- landmark/settlement/dungeon/wilderness

    -- 快照描述 (粗粒度)
    macro_description TEXT,                -- 宏观描述

    -- 几何与交互
    geometry TEXT,                         -- JSON数组: 几何特征
    interactables TEXT,                    -- JSON数组: 可交互物

    -- 感官
    sensory TEXT,                          -- JSON数组: 感官节点

    -- 可供性
    affordances TEXT,                      -- JSON数组: 可做之事

    -- 派系与NPC
    controlling_faction TEXT,              -- 控制派系ID
    key_npcs TEXT,                         -- JSON数组: 关键NPC IDs

    -- 状态
    status TEXT DEFAULT 'draft',           -- draft/published/locked
    canon_locked INTEGER DEFAULT 0,        -- 0=可修改, 1=已锁定
    detail_level INTEGER DEFAULT 0,        -- 0=轮廓, 1=基础, 2=详细, 3=完全细化

    -- 访问记录
    visit_count INTEGER DEFAULT 0,
    first_visited_turn INTEGER,
    last_visited_turn INTEGER,

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (region_id) REFERENCES regions(id)
);

CREATE INDEX idx_locations_region ON locations(region_id);
CREATE INDEX idx_locations_type ON locations(type);
CREATE INDEX idx_locations_status ON locations(status);
CREATE INDEX idx_locations_detail ON locations(detail_level);

-- 4. 兴趣点 (POIs - Points of Interest)
CREATE TABLE IF NOT EXISTS pois (
    id TEXT PRIMARY KEY,                   -- POI ID
    location_id TEXT NOT NULL,             -- 所属地点
    name TEXT NOT NULL,                    -- POI名称
    type TEXT NOT NULL,                    -- object/npc/event/hazard/secret

    -- 描述
    description TEXT,                      -- 基础描述

    -- 详细信息
    details TEXT,                          -- JSON: 细化信息

    -- 交互
    interaction_type TEXT,                 -- examine/talk/use/combat/solve
    requirements TEXT,                     -- JSON: 交互前置条件
    risks TEXT,                            -- JSON数组: 风险提示
    expected_outcomes TEXT,                -- JSON数组: 可能结果

    -- 状态
    state TEXT DEFAULT 'active',           -- active/depleted/destroyed/hidden
    interacted INTEGER DEFAULT 0,          -- 0=未互动, 1=已互动

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE INDEX idx_pois_location ON pois(location_id);
CREATE INDEX idx_pois_type ON pois(type);
CREATE INDEX idx_pois_state ON pois(state);

-- 5. 派系 (Factions)
CREATE TABLE IF NOT EXISTS factions (
    id TEXT PRIMARY KEY,                   -- 派系ID
    world_id TEXT NOT NULL,                -- 所属世界
    name TEXT NOT NULL,                    -- 派系名称

    -- 定义
    purpose TEXT NOT NULL,                 -- 目的
    ideology TEXT,                         -- 意识形态

    -- 资源与势力
    resources TEXT,                        -- JSON对象: 资源清单
    territory TEXT,                        -- JSON数组: 控制区域IDs
    power_level INTEGER DEFAULT 5,         -- 1-10

    -- 关系
    relationships TEXT,                    -- JSON对象: {factionId: attitude(-10~10)}

    -- 组织结构
    structure TEXT,                        -- 权力结构描述
    key_members TEXT,                      -- JSON数组: 关键成员NPC IDs

    -- 声望与行为
    voice_style TEXT,                      -- 口吻/性格模板
    behavior_patterns TEXT,                -- JSON数组: 行为模式

    -- 状态
    status TEXT DEFAULT 'active',          -- active/weakened/destroyed

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_factions_world ON factions(world_id);
CREATE INDEX idx_factions_status ON factions(status);
CREATE INDEX idx_factions_power ON factions(power_level);

-- 6. 物品与资源库 (Items & Resources)
CREATE TABLE IF NOT EXISTS world_items (
    id TEXT PRIMARY KEY,                   -- 物品ID
    world_id TEXT NOT NULL,                -- 所属世界
    name TEXT NOT NULL,                    -- 物品名称
    type TEXT NOT NULL,                    -- weapon/armor/consumable/material/key_item

    -- 描述
    description TEXT,                      -- 描述
    sensory_details TEXT,                  -- JSON数组: 感官细节

    -- 属性
    rarity TEXT DEFAULT 'common',          -- common/uncommon/rare/legendary
    properties TEXT,                       -- JSON对象: 属性

    -- 制作与获取
    crafting_recipe TEXT,                  -- JSON: 配方
    sources TEXT,                          -- JSON数组: 获取来源

    -- 状态
    status TEXT DEFAULT 'active',          -- active/deprecated

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_world_items_world ON world_items(world_id);
CREATE INDEX idx_world_items_type ON world_items(type);
CREATE INDEX idx_world_items_rarity ON world_items(rarity);

-- 7. 生态与怪物 (Creatures)
CREATE TABLE IF NOT EXISTS creatures (
    id TEXT PRIMARY KEY,                   -- 生物ID
    world_id TEXT NOT NULL,                -- 所属世界
    name TEXT NOT NULL,                    -- 生物名称
    type TEXT NOT NULL,                    -- beast/humanoid/undead/construct/spirit

    -- 描述
    description TEXT,                      -- 描述
    sensory_details TEXT,                  -- JSON数组: 感官细节

    -- 生态位
    habitat TEXT,                          -- JSON数组: 栖息地region/location IDs
    behavior TEXT,                         -- 行为模式描述

    -- 战斗属性
    danger_rating INTEGER DEFAULT 1,       -- 1-10
    abilities TEXT,                        -- JSON数组: 能力列表
    weaknesses TEXT,                       -- JSON数组: 弱点

    -- 掉落
    loot_table TEXT,                       -- JSON数组: 掉落物品IDs与概率

    -- 状态
    status TEXT DEFAULT 'active',          -- active/extinct

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_creatures_world ON creatures(world_id);
CREATE INDEX idx_creatures_type ON creatures(type);
CREATE INDEX idx_creatures_danger ON creatures(danger_rating);

-- 8. 任务钩子表 (Encounter/Quest Hooks)
CREATE TABLE IF NOT EXISTS quest_hooks (
    id TEXT PRIMARY KEY,                   -- 钩子ID
    world_id TEXT NOT NULL,                -- 所属世界

    -- 分类
    category TEXT NOT NULL,                -- encounter/quest/secret/danger
    context TEXT,                          -- 适用场景 (location_type/region_id)

    -- 内容
    title TEXT NOT NULL,                   -- 标题
    description TEXT NOT NULL,             -- 描述
    trigger_conditions TEXT,               -- JSON: 触发条件

    -- 结果
    possible_outcomes TEXT,                -- JSON数组: 可能结果

    -- 权重
    weight REAL DEFAULT 1.0,               -- 选择权重
    used_count INTEGER DEFAULT 0,          -- 已使用次数

    -- 状态
    status TEXT DEFAULT 'active',          -- active/exhausted

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_quest_hooks_world ON quest_hooks(world_id);
CREATE INDEX idx_quest_hooks_category ON quest_hooks(category);
CREATE INDEX idx_quest_hooks_status ON quest_hooks(status);

-- 9. 细化层 (Detail Layers) - 用于存储逐步细化的内容
CREATE TABLE IF NOT EXISTS detail_layers (
    id TEXT PRIMARY KEY,                   -- 层ID
    target_type TEXT NOT NULL,             -- location/poi/region/creature
    target_id TEXT NOT NULL,               -- 目标ID

    -- 细化类型
    layer_type TEXT NOT NULL,              -- sensory/geometry/affordance/cinematic/narrative

    -- 内容
    content TEXT NOT NULL,                 -- JSON: 细化内容

    -- 来源
    source TEXT DEFAULT 'generated',       -- generated/manual/player_action
    generated_by_turn INTEGER,             -- 生成时的回合数
    player_id TEXT,                        -- 触发细化的玩家ID (多人模式)

    -- 状态
    status TEXT DEFAULT 'draft',           -- draft/approved/canon

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(target_type, target_id, layer_type)
);

CREATE INDEX idx_detail_layers_target ON detail_layers(target_type, target_id);
CREATE INDEX idx_detail_layers_status ON detail_layers(status);

-- 10. 世界事件历史 (World Events Log)
CREATE TABLE IF NOT EXISTS world_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,                -- 所属世界
    novel_id TEXT NOT NULL,                -- 所属小说
    turn INTEGER NOT NULL,                 -- 发生回合

    -- 事件内容
    event_type TEXT NOT NULL,              -- faction_change/location_destroyed/npc_death/resource_depleted
    description TEXT NOT NULL,             -- 事件描述

    -- 影响范围
    affected_entities TEXT,                -- JSON对象: {type: id[]}

    -- 状态变化
    state_changes TEXT,                    -- JSON对象: 前后状态差异

    -- 可逆性
    reversible INTEGER DEFAULT 0,          -- 0=不可逆, 1=可逆

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id),
    FOREIGN KEY (novel_id) REFERENCES novels(id)
);

CREATE INDEX idx_world_events_world ON world_events(world_id);
CREATE INDEX idx_world_events_novel ON world_events(novel_id);
CREATE INDEX idx_world_events_turn ON world_events(novel_id, turn);
CREATE INDEX idx_world_events_type ON world_events(event_type);

-- 11. 叙事风格词库 (Narrative Style Vocabulary)
CREATE TABLE IF NOT EXISTS style_vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,                -- 所属世界

    -- 分类
    category TEXT NOT NULL,                -- imagery/metaphor/sensory/syntax_pattern
    subcategory TEXT,                      -- 子分类

    -- 内容
    content TEXT NOT NULL,                 -- 词汇/模式内容
    examples TEXT,                         -- JSON数组: 使用示例

    -- 使用频率
    usage_weight REAL DEFAULT 1.0,         -- 使用权重
    used_count INTEGER DEFAULT 0,          -- 已使用次数

    -- 状态
    status TEXT DEFAULT 'active',          -- active/deprecated

    -- 元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_style_vocabulary_world ON style_vocabulary(world_id);
CREATE INDEX idx_style_vocabulary_category ON style_vocabulary(category);

-- 12. 世界版本控制 (World Versions)
CREATE TABLE IF NOT EXISTS world_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,                -- 世界ID
    version INTEGER NOT NULL,              -- 版本号

    -- 变更
    changes_summary TEXT NOT NULL,         -- 变更摘要
    diff_data TEXT,                        -- JSON: 差异数据

    -- 快照
    snapshot_data TEXT,                    -- JSON: 完整快照 (可选)

    -- 元数据
    created_by TEXT DEFAULT 'system',      -- 创建者
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id),
    UNIQUE(world_id, version)
);

CREATE INDEX idx_world_versions_world ON world_versions(world_id);

-- 13. Canon 冲突检测日志
CREATE TABLE IF NOT EXISTS canon_conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    world_id TEXT NOT NULL,                -- 所属世界

    -- 冲突类型
    conflict_type TEXT NOT NULL,           -- duplicate_name/relationship_conflict/resource_conflict/geography_conflict

    -- 冲突实体
    entity_a TEXT NOT NULL,                -- 实体A: {type}:{id}
    entity_b TEXT NOT NULL,                -- 实体B: {type}:{id}

    -- 详情
    description TEXT NOT NULL,             -- 冲突描述
    severity TEXT DEFAULT 'warning',       -- warning/error/critical

    -- 状态
    status TEXT DEFAULT 'unresolved',      -- unresolved/resolved/ignored
    resolution TEXT,                       -- 解决方案描述

    -- 元数据
    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,

    FOREIGN KEY (world_id) REFERENCES world_scaffolds(id)
);

CREATE INDEX idx_canon_conflicts_world ON canon_conflicts(world_id);
CREATE INDEX idx_canon_conflicts_status ON canon_conflicts(status);
CREATE INDEX idx_canon_conflicts_severity ON canon_conflicts(severity);
