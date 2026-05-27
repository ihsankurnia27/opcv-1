"""Test preset CRUD endpoints."""

import json
import os
import sys
import threading

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import app, _detect_config, _detect_config_lock

client = TestClient(app)

PRESET_CONFIG = json.dumps({
    "point": "G-01",
    "server_api_url": "",
    "api_key": "",
    "presets": [],
})


def _with_config(data):
    """Decorator/helper: patch CONFIG_PATH with a temp file."""
    return patch("app.api.CONFIG_PATH", data)


# --- CRUD ---

def test_create_preset():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_create.json"):
        with open("/tmp/_test_p_create.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets", json={"name": "my preset", "params": {"blur_kernel": 7}})
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "my preset"
    assert data["params"] == {"blur_kernel": 7}
    assert "id" in data and len(data["id"]) == 12
    assert "created" in data


def test_create_preset_no_name():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_noname.json"):
        with open("/tmp/_test_p_noname.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets", json={"params": {}})
    assert resp.status_code == 400


def test_list_presets():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_list.json"):
        with open("/tmp/_test_p_list.json", "w") as f:
            json.dump({"presets": [
                {"id": "aaa", "name": "P1", "params": {}, "created": "2024-01-01"},
                {"id": "bbb", "name": "P2", "params": {"blur_kernel": 5}, "created": "2024-01-02"},
            ]}, f)
        resp = client.get("/api/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert data[0]["name"] == "P1"
    assert data[1]["name"] == "P2"


def test_get_presets_empty_list():
    """GET /api/presets returns [] when presets key is an empty array."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_empty_list2.json"):
        with open("/tmp/_test_p_empty_list2.json", "w") as f:
            json.dump({"presets": []}, f)
        resp = client.get("/api/presets")
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_preset():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_get.json"):
        with open("/tmp/_test_p_get.json", "w") as f:
            json.dump({"presets": [
                {"id": "abc123", "name": "X", "params": {"blur_kernel": 9}, "created": "2024-01-01"},
            ]}, f)
        resp = client.get("/api/presets/abc123")
    assert resp.status_code == 200
    assert resp.json()["name"] == "X"
    assert resp.json()["params"]["blur_kernel"] == 9


def test_get_preset_not_found():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_get404.json"):
        with open("/tmp/_test_p_get404.json", "w") as f:
            json.dump({"presets": []}, f)
        resp = client.get("/api/presets/nonexistent")
    assert resp.status_code == 404


def test_update_preset():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_update.json"):
        with open("/tmp/_test_p_update.json", "w") as f:
            json.dump({"presets": [
                {"id": "xyz", "name": "Old", "params": {"blur_kernel": 3}, "created": "2024-01-01"},
            ]}, f)
        resp = client.put("/api/presets/xyz", json={"name": "New", "params": {"blur_kernel": 11}})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New"
    assert data["params"]["blur_kernel"] == 11


def test_update_preset_not_found():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_up404.json"):
        with open("/tmp/_test_p_up404.json", "w") as f:
            json.dump({"presets": []}, f)
        resp = client.put("/api/presets/nope", json={"name": "Nope"})
    assert resp.status_code == 404


def test_update_preset_partial():
    """Only update name if that's all that's provided."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_partial.json"):
        with open("/tmp/_test_p_partial.json", "w") as f:
            json.dump({"presets": [
                {"id": "p1", "name": "OG", "params": {"blur_kernel": 5}, "created": "2024-01-01"},
            ]}, f)
        resp = client.put("/api/presets/p1", json={"name": "Renamed"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Renamed"
    assert data["params"]["blur_kernel"] == 5


def test_delete_preset():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_del.json"):
        with open("/tmp/_test_p_del.json", "w") as f:
            json.dump({"presets": [
                {"id": "del1", "name": "Del", "params": {}, "created": "2024-01-01"},
            ]}, f)
        resp = client.delete("/api/presets/del1")
        assert resp.status_code == 204
        with open("/tmp/_test_p_del.json") as f:
            cfg = json.load(f)
        assert len(cfg["presets"]) == 0


def test_delete_preset_not_found():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_del404.json"):
        with open("/tmp/_test_p_del404.json", "w") as f:
            json.dump({"presets": []}, f)
        resp = client.delete("/api/presets/nonexistent")
    assert resp.status_code == 404


# --- Duplicate name overwrites ---

def test_create_duplicate_name_overwrites():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_dup.json"):
        with open("/tmp/_test_p_dup.json", "w") as f:
            json.dump({"presets": [
                {"id": "orig", "name": "SameName", "params": {"blur_kernel": 3}, "created": "2024-01-01"},
            ]}, f)
        resp = client.post("/api/presets", json={"name": "SameName", "params": {"blur_kernel": 11}})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "SameName"
        assert data["params"]["blur_kernel"] == 11
        assert data["id"] != "orig"  # new id generated
        with open("/tmp/_test_p_dup.json") as f:
            cfg = json.load(f)
        matches = [p for p in cfg["presets"] if p["name"] == "SameName"]
        assert len(matches) == 1


# --- Apply ---

def test_apply_preset():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_apply.json"):
        cfg = {"presets": [
            {"id": "ap1", "name": "App", "params": {"blur_kernel": 11, "threshold_block": 15},
             "created": "2024-01-01"},
        ]}
        with open("/tmp/_test_p_apply.json", "w") as f:
            json.dump(cfg, f)
        with _detect_config_lock:
            _detect_config.clear()
        resp = client.post("/api/presets/ap1/apply")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    with _detect_config_lock:
        assert _detect_config.get("blur_kernel") == 11
        assert _detect_config.get("threshold_block") == 15


def test_apply_preset_not_found():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_ap404.json"):
        with open("/tmp/_test_p_ap404.json", "w") as f:
            json.dump({"presets": []}, f)
        resp = client.post("/api/presets/nope/apply")
    assert resp.status_code == 404


def test_apply_preset_unknown_keys_ignored():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_ap_unk.json"):
        cfg = {"presets": [
            {"id": "uk1", "name": "Unk", "params": {"blur_kernel": 9, "nonexistent_opt": 999,
                                                       "another_bad": "x"},
             "created": "2024-01-01"},
        ]}
        with open("/tmp/_test_p_ap_unk.json", "w") as f:
            json.dump(cfg, f)
        with _detect_config_lock:
            _detect_config.clear()
        resp = client.post("/api/presets/uk1/apply")
    assert resp.status_code == 200
    assert resp.json()["ok"] is True
    with _detect_config_lock:
        assert _detect_config.get("blur_kernel") == 9
        # Unknown keys do NOT appear in _detect_config
        assert "nonexistent_opt" not in _detect_config
        assert "another_bad" not in _detect_config


def test_apply_preset_missing_keys_use_defaults():
    """Keys not in preset params keep their current values in _detect_config."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_ap_missing.json"):
        cfg = {"presets": [
            {"id": "m1", "name": "Miss", "params": {"blur_kernel": 7},
             "created": "2024-01-01"},
        ]}
        with open("/tmp/_test_p_ap_missing.json", "w") as f:
            json.dump(cfg, f)
        with _detect_config_lock:
            _detect_config.clear()
            _detect_config["threshold_block"] = 99  # existing value
        resp = client.post("/api/presets/m1/apply")
    assert resp.status_code == 200
    with _detect_config_lock:
        assert _detect_config.get("blur_kernel") == 7   # set from preset
        assert _detect_config.get("threshold_block") == 99  # kept its value


# --- Full CRUD cycle ---

def test_full_crud_cycle():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_p_full.json"):
        with open("/tmp/_test_p_full.json", "w") as f:
            json.dump({"presets": []}, f)

        # Create
        resp = client.post("/api/presets", json={"name": "Cycle", "params": {"blur_kernel": 7}})
        assert resp.status_code == 201
        pid = resp.json()["id"]

        # Read
        resp = client.get(f"/api/presets/{pid}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Cycle"

        # Update
        resp = client.put(f"/api/presets/{pid}", json={"name": "Updated", "params": {"blur_kernel": 11}})
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated"
        assert resp.json()["params"]["blur_kernel"] == 11

        # Delete
        resp = client.delete(f"/api/presets/{pid}")
        assert resp.status_code == 204

        # Verify gone
        resp = client.get(f"/api/presets/{pid}")
        assert resp.status_code == 404
