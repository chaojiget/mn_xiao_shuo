#!/usr/bin/env python3
"""
Import narrative asset blueprints (YAML) and inject them into a WorldPack stored
in the SQLite DB. It updates loot tables, scene encounters and lore entries.

Usage:
  uv run python scripts/import_assets.py \
    --world-id <world_id> \
    --blueprint examples/blueprints/dark_forest_pack.yaml \
    [--override-setting true] [--dry-run]
"""

from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
import sys
from pathlib import Path

# Add project root for imports
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from web.backend.assets.loader import bundle_summary, load_blueprint
from web.backend.assets.injector import inject_bundle
from web.backend.models.world_pack import WorldPack


def get_db_path() -> str:
    try:
        # Try settings used by API code
        from web.backend.config.settings import settings  # type: ignore

        return str(settings.database_path)
    except Exception:
        return str(ROOT / "data" / "sqlite" / "novel.db")


def fetch_world(conn: sqlite3.Connection, world_id: str) -> WorldPack:
    cur = conn.cursor()
    row = cur.execute("SELECT json_gz FROM worlds WHERE id = ?", (world_id,)).fetchone()
    if not row:
        raise SystemExit(f"World not found: {world_id}")
    data = gzip.decompress(row[0]).decode("utf-8")
    return WorldPack.model_validate_json(data)


def save_world(conn: sqlite3.Connection, world_id: str, world: WorldPack) -> None:
    json_str = world.model_dump_json(ensure_ascii=False)
    blob = gzip.compress(json_str.encode("utf-8"))
    cur = conn.cursor()
    cur.execute("UPDATE worlds SET json_gz = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (blob, world_id))
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser(description="Import YAML assets into a WorldPack")
    ap.add_argument("--world-id", required=True)
    ap.add_argument("--blueprint", required=True)
    ap.add_argument("--override-setting", default="true", choices=["true", "false"]) 
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    bp_path = Path(args.blueprint).resolve()
    bundle = load_blueprint(bp_path)
    print("Loaded bundle:", json.dumps(bundle_summary(bundle), ensure_ascii=False))

    db_path = get_db_path()
    print(f"DB: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        world = fetch_world(conn, args.world_id)
        report = inject_bundle(world, bundle, override_setting=(args.override_setting == "true"))

        print("Injection report:")
        print(json.dumps(report.model_dump(), ensure_ascii=False, indent=2))

        if args.dry_run:
            print("Dry-run: not saving changes.")
            return

        save_world(conn, args.world_id, world)
        print("Saved updated world.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

