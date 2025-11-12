from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Model(BaseModel):
    model_config = {"extra": "allow"}


class WorldSettingAsset(Model):
    id: str
    title: str
    tone: Literal["dark", "epic", "cozy", "mystery", "whimsical"]
    difficulty: Literal["story", "normal", "hard"] = "normal"
    power_ceiling: int = Field(ge=1, le=5, default=3)
    themes: List[str] = []
    taboos: List[str] = []
    aesthetics: List[str] = []
    cosmology: Dict[str, Any] = {}
    factions: List[Dict[str, Any]] = []
    constraints: List[str] = []
    narrative_guides: Dict[str, Any] = {}
    version: str = "1.0.0"
    changelog: List[str] = []


class ItemDropSources(Model):
    loot_tables: List[str] = []
    quests: List[str] = []
    pois: List[str] = []


class ItemAsset(Model):
    id: str
    name: str
    rarity: Literal["common", "uncommon", "rare", "epic", "legendary", "mythic"]
    type: Literal["weapon", "armor", "trinket", "consumable", "material", "quest", "misc"]
    origin: Optional[str] = None
    affinity_tags: List[str] = []
    mechanical_effects: Dict[str, Any] = {}
    narrative_hooks: List[str] = []
    usage_constraints: Dict[str, Any] = {}
    synergy: Dict[str, Any] = {}
    drop_sources: ItemDropSources = Field(default_factory=ItemDropSources)
    versions: List[Dict[str, Any]] = []


class SkillAsset(Model):
    id: str
    name: str
    school: str
    grade: Literal["E", "D", "C", "B", "A", "S"] = "C"
    type: Literal["active", "passive", "reaction"] = "active"
    cost: Dict[str, Any] = {}
    targeting: Literal["self", "single", "aoe", "zone"] = "single"
    cooldown: int = 0
    scaling: Dict[str, Any] = {}
    checks: Dict[str, Any] | List[Dict[str, Any]] | None = None
    effects: Dict[str, Any] = {}
    unlock_reqs: List[str] = []
    narrative_beats: List[str] = []
    versions: List[Dict[str, Any]] = []


class TalentAsset(Model):
    id: str
    name: str
    branch: str
    prerequisites: List[str] = []
    mutually_exclusive: List[str] = []
    bonuses: Dict[str, Any] = {}
    drawbacks: Dict[str, Any] = {}
    roleplay_prompts: List[str] = []
    quest_hooks: List[str] = []
    versions: List[Dict[str, Any]] = []


class SceneActor(Model):
    id: str
    stance: Literal["hostile", "neutral", "friendly", "cautious"] = "neutral"


class SceneBindings(Model):
    biomes: List[str] = []
    pois: List[str] = []
    time_of_day: List[str] = []
    weather: List[str] = []


class SceneOutcomes(Model):
    rewards: Dict[str, Any] = {}
    world_changes: Dict[str, Any] = {}


class SceneAsset(Model):
    id: str
    kind: Literal["exploration", "combat", "social", "puzzle", "event"]
    location_bindings: SceneBindings = Field(default_factory=SceneBindings)
    triggers: List[str] = []
    actors: List[SceneActor] = []
    beats: List[Dict[str, Any] | str] = []
    checks: List[Dict[str, Any]] = []
    outcomes: SceneOutcomes = Field(default_factory=SceneOutcomes)
    reuse_strategy: Dict[str, Any] = {}
    versions: List[Dict[str, Any]] = []


class AssetBundle(Model):
    world_setting: Optional[WorldSettingAsset] = None
    items: List[ItemAsset] = []
    skills: List[SkillAsset] = []
    talents: List[TalentAsset] = []
    scenes: List[SceneAsset] = []

    def all_ids(self) -> List[str]:
        ids = []
        if self.world_setting:
            ids.append(self.world_setting.id)
        ids.extend([i.id for i in self.items])
        ids.extend([s.id for s in self.skills])
        ids.extend([t.id for t in self.talents])
        ids.extend([c.id for c in self.scenes])
        return ids

