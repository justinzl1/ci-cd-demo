from datetime import datetime

import pytest
from fastapi.testclient import TestClient

from app.main import app, store

client = TestClient(app)

VALID = {"battery": 87.5, "x": 1.25, "y": -3.0, "state": "moving"}


@pytest.fixture(autouse=True)
def clear_store():
    store.clear()
    yield
    store.clear()


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_post_telemetry_returns_201_and_record():
    resp = client.post("/robots/r2d2/telemetry", json=VALID)
    assert resp.status_code == 201
    body = resp.json()
    assert body["robot_id"] == "r2d2"
    assert body["battery"] == 87.5
    assert body["state"] == "moving"
    assert datetime.fromisoformat(body["timestamp"]).tzinfo is not None


def test_get_robot_returns_latest():
    client.post("/robots/r2d2/telemetry", json=VALID)
    client.post("/robots/r2d2/telemetry", json={**VALID, "state": "idle", "x": 9.0})
    resp = client.get("/robots/r2d2")
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "idle"
    assert body["x"] == 9.0


def test_get_unknown_robot_returns_404():
    resp = client.get("/robots/ghost")
    assert resp.status_code == 404


def test_list_robots_empty():
    resp = client.get("/robots")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_robots_returns_latest_state_per_robot():
    client.post("/robots/a/telemetry", json=VALID)
    client.post("/robots/b/telemetry", json={**VALID, "state": "error"})
    client.post("/robots/a/telemetry", json={**VALID, "state": "idle"})
    resp = client.get("/robots")
    assert resp.status_code == 200
    states = {r["robot_id"]: r["state"] for r in resp.json()}
    assert states == {"a": "idle", "b": "error"}


@pytest.mark.parametrize("battery", [-0.1, 100.1])
def test_battery_out_of_range_rejected(battery):
    resp = client.post("/robots/r2d2/telemetry", json={**VALID, "battery": battery})
    assert resp.status_code == 422


@pytest.mark.parametrize("battery", [0, 100])
def test_battery_bounds_accepted(battery):
    resp = client.post("/robots/r2d2/telemetry", json={**VALID, "battery": battery})
    assert resp.status_code == 201


def test_invalid_state_rejected():
    resp = client.post("/robots/r2d2/telemetry", json={**VALID, "state": "flying"})
    assert resp.status_code == 422


def test_missing_field_rejected():
    payload = {k: v for k, v in VALID.items() if k != "y"}
    resp = client.post("/robots/r2d2/telemetry", json=payload)
    assert resp.status_code == 422


def test_non_numeric_coordinate_rejected():
    resp = client.post("/robots/r2d2/telemetry", json={**VALID, "x": "left"})
    assert resp.status_code == 422


def test_rejected_post_does_not_store():
    client.post("/robots/r2d2/telemetry", json={**VALID, "battery": 500})
    assert client.get("/robots/r2d2").status_code == 404
