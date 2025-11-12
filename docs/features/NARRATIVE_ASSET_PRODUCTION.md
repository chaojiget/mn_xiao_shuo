# 叙事资产生产规范（物品/技能/场景/天赋/世界设定）

> 目标：在不牺牲玩法自由的前提下，确保叙事完整性、一致性与可复用性。

## 核心原则

- 统一语义：所有资产以相同字段语义描述（蓝本 → 实例）。
- 叙事挂钩：每个资产必须可回溯到“世界设定/派系/任务线/地点/POI”。
- 明确约束：在蓝本上声明“使用条件/代价/上限/冲突关系”，避免系统性冲突。
- 可复用：通过标签与参数化模板，实现快速换皮与平衡裁剪。
- 可追溯：每个资产记录“来源/版本/变更原因/适配范围”。

## 与 WorldPack 的映射

- WorldSetting → `WorldPack.meta` + `WorldPack.lore`
- Items → 通过 `LootTable.entries.item_id` 参与掉落；可在 `lore` 存放设定条目
- Skills/Talents → 作为“玩法规则层”由 DM/引擎消费（叙事字段仍入库，便于提示与一致性）
- Scenes → 绑定 `Location`/`POI`/`QuestObjective` 的发生模板与过场文本

## 资产类型与字段约定

统一主键风格：`<domain>.<slug>`（例：`item.frostbite_dagger`）。

### 1) WorldSetting（世界设定）
- id, title, tone, difficulty, power_ceiling（能力上限刻度：1–5）
- themes（主题标签）、taboos（禁忌）、aesthetics（风格要素）
- cosmology（世界观/能量来源）、factions（派系纲要）、constraints（硬性约束）
- narrative_guides（叙事守恒：因果/代价/信息一致性）

### 2) Item（物品）
- id, name, rarity（common→mythic）, type（weapon/consumable/etc）
- origin（来源/故事）、affinity_tags（元素/学派/派系）
- mechanical_effects（数值/状态）、narrative_hooks（可触发剧情/台词）
- usage_constraints（需求/冷却/禁忌）、synergy（与技能/天赋/派系联动）
- drop_sources（对应 LootTable/POI/Quest）、versions（平衡调整记录）

### 3) Skill（技能）
- id, name, school, grade（E→S）、cost（资源/代价）
- targeting（self/single/aoe/zone）、cooldown、scaling（面板/情境加成）
- checks（叙事检定：社交/探索/知识/信念）
- failures（失败代价/反噬）、synergy、unlock_reqs（学习条件）
- narrative_beats（使用时的叙事节拍/镜头）

### 4) Talent（天赋/特质）
- id, name, branch（天赋树分支）、prerequisites（前置）、mutually_exclusive（互斥）
- bonuses（被动效果/阈值/上限）、roleplay_prompts（扮演倾向）
- drawbacks（副作用/代价）、quest_hooks（相关任务线）

### 5) Scene（场景模板）
- id, kind（exploration/combat/social/puzzle/event）
- location_bindings（可触发地点/POI/生态）、triggers（条件/时间/天气）
- actors（参与者与立场）、beats（叙事节拍：目标→冲突→转折→出场）
- checks（可用技能/难度/失败分支）、outcomes（奖励/代价/世界变化）
- reuse_strategy（换皮参数/难度刻度/冲突重抽）

## 生产流程（五步）

1) 设定收敛：读取 WorldSetting，确定 tone/theme/power_ceiling/taboos
2) 蓝本编写：按模板填写最小完备字段（docs/templates/*.yaml）
3) 约束校验：检查引用存在性、互斥/环依赖、强度上限
4) 叙事挂钩：添加 narrative_hooks/quest_hooks/scene.bindings
5) 发布与复用：打标签、版本化，入库并加入 Loot/Encounter/Quest 链路

## 复用策略

- 标签复用：`tags: [school:shadow, faction:order, tone:dark]`
- 参数化换皮：保留机制，替换命名/美术/台词（不越过 power_ceiling）
- 分层复用：设定层（世界观）→ 机制层（数值/规则）→ 呈现层（文案/演出）
- 版本控制：`version.semver` + `changelog` + `balance_note`
- 组合包：按照“主题/派系/剧情章”打包场景+物品+任务一揽子复用

## 叙事完整性检查表（精选）

- 因果：每个奖励/惩罚可回溯到明确行为/抉择
- 一致：tone/禁忌/世界规则不自相矛盾
- 约束：技能/天赋不会突破 world.power_ceiling
- 钩子：资产至少提供1个进入/推进剧情的钩子
- 回收：强力资产具备合理代价或中后期回收机制

## LLM 生成提示框架（可嵌入）

输入：`world_setting + asset_kind + required_fields`

- 系统意图：
  “在不违背 world.constraints 与 power_ceiling 的前提下，生成最小完备资产。”
- 结构约束：
  “仅输出符合 docs/templates/{asset_kind}.yaml 字段的 JSON/YAML。”
- 叙事约束：
  “为每个资产添加 narrative_hooks（将如何推动任务/关系/地点探索）。”

## 与现有系统的对接建议

- Items：将 `id` 注入 `LootTable.entries.item_id`，并在 `lore` 写入百科
- Scenes：把 `scene.id` 绑定到 `POI.encounter_table_id` 或 `QuestObjective` 的触发
- Skills/Talents：前端展示 + DM 提示中使用（数据入库，规则由引擎消费）

## 目录与模板

- `docs/templates/*.yaml` 提供蓝本模板与注释
- `examples/blueprints/` 存放示例（小型可运行组合包）

维护者约定：新增资产类型时，先补模板，再落地对接策略与检查项。

## 导入到世界（CLI）

- 命令：`uv run python scripts/import_assets.py --world-id <world_id> --blueprint examples/blueprints/dark_forest_pack.yaml [--override-setting true] [--dry-run]`
- 功能：
  - 写入 lore：items/skills/talents/scenes/setting 摘要，便于检索/提示
  - 物品→掉落：按稀有度默认权重注入 LootTable（找不到则创建）
  - 场景→遭遇：按 POI 绑定生成 EncounterTable（或向现有表追加）
  - 任务奖励：对接 `item.drop_sources.quests`，为匹配任务追加奖励
- 报告：注入完成后输出 JSON 报告（变更摘要）
