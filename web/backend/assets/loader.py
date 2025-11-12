from __future__ import annotations

import json
from pathlib import Path
from typing import List, Tuple

import yaml

from .models import (
    AssetBundle,
    ItemAsset,
    SceneAsset,
    SkillAsset,
    TalentAsset,
    WorldSettingAsset,
)


def _read_yaml(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_world_setting(path: Path) -> WorldSettingAsset:
    data = _read_yaml(path)
    return WorldSettingAsset.model_validate(data)


def load_item(path: Path) -> ItemAsset:
    data = _read_yaml(path)
    return ItemAsset.model_validate(data)


def load_skill(path: Path) -> SkillAsset:
    data = _read_yaml(path)
    return SkillAsset.model_validate(data)


def load_talent(path: Path) -> TalentAsset:
    data = _read_yaml(path)
    return TalentAsset.model_validate(data)


def load_scene(path: Path) -> SceneAsset:
    data = _read_yaml(path)
    return SceneAsset.model_validate(data)


def load_blueprint(bp_path: Path) -> AssetBundle:
    """Load a blueprint YAML that lists asset file paths.

    Example shape:
      world_setting: ./../docs/templates/world_setting.yaml
      items: [path1.yaml, path2.yaml]
      skills: [...]
      talents: [...]
      scenes: [...]
    """
    bp = _read_yaml(bp_path)

    bundle = AssetBundle()

    def _resolve_list(paths: List[str]) -> List[Path]:
        out = []
        for p in paths:
            out.append((bp_path.parent / p).resolve())
        return out

    if ws := bp.get("world_setting"):
        bundle.world_setting = load_world_setting((bp_path.parent / ws).resolve())

    for key, loader in [
        ("items", load_item),
        ("skills", load_skill),
        ("talents", load_talent),
        ("scenes", load_scene),
    ]:
        paths = bp.get(key, []) or []
        for p in _resolve_list(paths):
            bundle.__dict__[key].append(loader(p))

    return bundle


def bundle_summary(bundle: AssetBundle) -> dict:
    return {
        "world_setting": bundle.world_setting.id if bundle.world_setting else None,
        "counts": {
            "items": len(bundle.items),
            "skills": len(bundle.skills),
            "talents": len(bundle.talents),
            "scenes": len(bundle.scenes),
        },
        "ids": bundle.all_ids(),
    }

