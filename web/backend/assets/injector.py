from __future__ import annotations

import json
from typing import Dict, List, Tuple

from pydantic import BaseModel

from ..models.world_pack import (
    EncounterEntry,
    EncounterTable,
    LootEntry,
    LootTable,
    POI,
    Quest,
    WorldPack,
)
from .models import AssetBundle, ItemAsset, SceneAsset, WorldSettingAsset


RARITY_WEIGHT = {
    "common": 50,
    "uncommon": 30,
    "rare": 10,
    "epic": 5,
    "legendary": 2,
    "mythic": 1,
}


class InjectionReport(BaseModel):
    items_added_to_loot: List[Tuple[str, str]] = []  # (loot_table_id, item_id)
    poi_loot_tables_created: List[str] = []
    scenes_added: List[Tuple[str, str]] = []  # (poi_id, scene_id)
    quests_rewards_updated: List[Tuple[str, str]] = []  # (quest_id, item_id)
    meta_overridden: Dict[str, str] = {}
    lore_added: int = 0


def _ensure_loot_table(world: WorldPack, table_id: str) -> LootTable:
    for t in world.loot_tables:
        if t.id == table_id:
            return t
    lt = LootTable(id=table_id, entries=[])
    world.loot_tables.append(lt)
    return lt


def _ensure_encounter_table(world: WorldPack, table_id: str) -> EncounterTable:
    for t in world.encounter_tables:
        if t.id == table_id:
            return t
    et = EncounterTable(id=table_id, entries=[])
    world.encounter_tables.append(et)
    return et


def apply_world_setting(world: WorldPack, ws: WorldSettingAsset, override: bool = True, report: InjectionReport | None = None) -> None:
    if override:
        changes = {}
        if world.meta.tone != ws.tone:
            changes["tone"] = f"{world.meta.tone} → {ws.tone}"
            world.meta.tone = ws.tone
        if world.meta.difficulty != ws.difficulty:
            changes["difficulty"] = f"{world.meta.difficulty} → {ws.difficulty}"
            world.meta.difficulty = ws.difficulty
        if report is not None and changes:
            report.meta_overridden = changes

    # 写入设定摘要到 lore
    summary = {
        "id": ws.id,
        "title": ws.title,
        "themes": ws.themes,
        "taboos": ws.taboos,
        "aesthetics": ws.aesthetics,
        "constraints": ws.constraints,
        "factions": [f.get("name", f.get("id")) for f in (ws.factions or [])],
    }
    world.lore[f"setting:{ws.id}"] = json.dumps(summary, ensure_ascii=False)


def inject_items(world: WorldPack, items: List[ItemAsset], report: InjectionReport) -> None:
    # 先聚合：poi -> items
    poi_to_items: Dict[str, List[ItemAsset]] = {}
    for it in items:
        # lore
        world.lore[f"asset:item:{it.id}"] = json.dumps(
            {
                "id": it.id,
                "name": it.name,
                "rarity": it.rarity,
                "type": it.type,
                "origin": it.origin,
                "affinity_tags": it.affinity_tags,
                "narrative_hooks": it.narrative_hooks,
            },
            ensure_ascii=False,
        )
        report.lore_added += 1

        # loot_tables injection
        for table_id in it.drop_sources.loot_tables:
            lt = _ensure_loot_table(world, table_id)
            weight = RARITY_WEIGHT.get(it.rarity, 5)
            lt.entries.append(
                LootEntry(item_id=it.id, weight=weight, quantity_min=1, quantity_max=1)
            )
            report.items_added_to_loot.append((table_id, it.id))

        # quest rewards
        for quest_id in it.drop_sources.quests:
            for q in world.quests:
                if q.id == quest_id:
                    # Add or increment
                    rewards = q.rewards or {}
                    rewards[it.id] = rewards.get(it.id, 0) + 1
                    q.rewards = rewards
                    report.quests_rewards_updated.append((quest_id, it.id))
                    break

        # poi specific
        for poi_id in it.drop_sources.pois:
            poi_to_items.setdefault(poi_id, []).append(it)

    # materialize POI loot tables
    if poi_to_items:
        poi_index: Dict[str, POI] = {}
        for loc in world.locations:
            for poi in loc.pois:
                poi_index[poi.id] = poi

        for poi_id, items in poi_to_items.items():
            poi = poi_index.get(poi_id)
            if not poi:
                continue
            table_id = poi.loot_table_id or f"loot.auto.{poi_id}"
            if poi.loot_table_id is None:
                poi.loot_table_id = table_id
                report.poi_loot_tables_created.append(table_id)
            lt = _ensure_loot_table(world, table_id)
            for it in items:
                weight = RARITY_WEIGHT.get(it.rarity, 5)
                lt.entries.append(
                    LootEntry(item_id=it.id, weight=weight, quantity_min=1, quantity_max=1)
                )
                report.items_added_to_loot.append((table_id, it.id))


def inject_scenes(world: WorldPack, scenes: List[SceneAsset], report: InjectionReport) -> None:
    # Build indices
    poi_index: Dict[str, POI] = {}
    biome_to_pois: Dict[str, List[POI]] = {}
    for loc in world.locations:
        for poi in loc.pois:
            poi_index[poi.id] = poi
            biome_to_pois.setdefault(loc.biome, []).append(poi)

    for sc in scenes:
        # choose target POIs
        targets: List[POI] = []
        if sc.location_bindings.pois:
            for pid in sc.location_bindings.pois:
                if pid in poi_index:
                    targets.append(poi_index[pid])
        elif sc.location_bindings.biomes:
            for b in sc.location_bindings.biomes:
                targets.extend(biome_to_pois.get(b, []))

        for poi in targets:
            # add hook
            text = f"scene:{sc.id}"
            if text not in poi.hooks:
                poi.hooks.append(text)

            # add to encounter table
            table_id = poi.encounter_table_id or f"enc.auto.{poi.id}"
            if poi.encounter_table_id is None:
                poi.encounter_table_id = table_id
            et = _ensure_encounter_table(world, table_id)
            # default weight
            et.entries.append(EncounterEntry(encounter_id=sc.id, weight=10))
            report.scenes_added.append((poi.id, sc.id))

        # lore for scene
        world.lore[f"asset:scene:{sc.id}"] = json.dumps(
            {
                "id": sc.id,
                "kind": sc.kind,
                "bindings": sc.location_bindings.model_dump(),
                "triggers": sc.triggers,
                "beats": sc.beats,
            },
            ensure_ascii=False,
        )
        report.lore_added += 1


def inject_bundle(world: WorldPack, bundle: AssetBundle, override_setting: bool = True) -> InjectionReport:
    report = InjectionReport()

    if bundle.world_setting:
        apply_world_setting(world, bundle.world_setting, override=override_setting, report=report)

    if bundle.items:
        inject_items(world, bundle.items, report)

    if bundle.scenes:
        inject_scenes(world, bundle.scenes, report)

    # skills / talents: store in lore for DM use
    for obj, prefix in [
        (bundle.skills, "skill"),
        (bundle.talents, "talent"),
    ]:
        for item in obj:
            world.lore[f"asset:{prefix}:{item.id}"] = json.dumps(
                item.model_dump(), ensure_ascii=False
            )
            report.lore_added += 1

    return report

