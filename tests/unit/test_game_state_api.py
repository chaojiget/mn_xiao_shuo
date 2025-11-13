"""Game API session state endpoints tests."""

import pytest

pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from web.backend.api import game_api
from web.backend.database.game_state_db import GameStateManager


def create_test_client(tmp_path):
    """Create a FastAPI test client with isolated game state manager."""
    db_path = tmp_path / "game_state.db"
    manager = GameStateManager(str(db_path))

    original_manager = game_api.game_state_manager
    game_api.game_state_manager = manager

    app = FastAPI()
    app.include_router(game_api.router)
    client = TestClient(app)

    return client, original_manager


def test_save_and_retrieve_game_state(tmp_path):
    client, original_manager = create_test_client(tmp_path)

    try:
        game_id = "session-001"
        payload = {
            "player": {"hp": 42, "max_hp": 100},
            "world": {"time": 3, "current_location": "start"},
            "turn_number": 3,
        }

        response = client.post(f"/api/game/state/{game_id}", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["game_id"] == game_id

        fetch = client.get(f"/api/game/state/{game_id}")
        assert fetch.status_code == 200
        fetched_data = fetch.json()
        assert fetched_data["success"] is True
        assert fetched_data["game_id"] == game_id
        assert fetched_data["state"]["player"]["hp"] == 42
    finally:
        client.close()
        game_api.game_state_manager = original_manager


def test_get_game_state_not_found(tmp_path):
    client, original_manager = create_test_client(tmp_path)

    try:
        response = client.get("/api/game/state/missing-session")
        assert response.status_code == 404
    finally:
        client.close()
        game_api.game_state_manager = original_manager
