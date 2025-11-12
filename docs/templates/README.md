# 模板使用说明（docs/templates）

## 命名与主键

- 主键格式：`<domain>.<slug>`，示例：`item.frostbite_dagger`
- 统一使用小写、下划线或连字符，避免空格与中文主键。

## 基本流程

1) 先确定/引用 `world_setting.yaml`（tone/themes/power_ceiling/taboos）
2) 在对应模板中填充最小完备字段（先小后全，留注释）
3) 运行校验（引用存在性、互斥、强度上限）
4) 将 `id` 纳入现有链路（Loot/Encounter/Quest/Lore）
5) 标注 `version` 与 `changelog`，提交审阅

## 字段约定摘录

- `affinity_tags`：用于复用/筛选（例：`school:shadow`, `faction:order`）
- `power_ceiling`：1–5，对齐世界强度上限；超上限需明确代价/稀有度
- `narrative_hooks`：必须至少提供1条推进剧情的挂钩

## 校验建议（人工/脚本）

- 引用存在性：items↔loot，scenes↔poi/quest，skills/talents↔unlock_reqs
- 冲突检测：talent.mutually_exclusive，quest 依赖是否环
- 强度守恒：不越过 world.power_ceiling；强力资产需代价/冷却/失败分支

