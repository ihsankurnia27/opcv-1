"""Test preset import endpoint."""

import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)

PRESET_CONFIG = json.dumps({
    "point": "G-01",
    "server_api_url": "",
    "api_key": "",
    "presets": [],
})


def test_import_valid():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_imp_valid.json"):
        with open("/tmp/_test_imp_valid.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets/import", json={
            "version": 1,
            "presets": [
                {"name": "P1", "params": {"blur_kernel": 7}},
                {"name": "P2", "params": {"blur_kernel": 11, "threshold_block": 15}},
            ],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    with open("/tmp/_test_imp_valid.json") as f:
        cfg = json.load(f)
    assert len(cfg["presets"]) == 2
    names = [p["name"] for p in cfg["presets"]]
    assert "P1" in names
    assert "P2" in names


def test_import_unknown_version():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_imp_ver.json"):
        with open("/tmp/_test_imp_ver.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets/import", json={
            "version": 999,
            "presets": [{"name": "X", "params": {}}],
        })
    assert resp.status_code == 400
    assert "Unknown version" in resp.json()["detail"]


def test_import_invalid_format():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_imp_fmt.json"):
        with open("/tmp/_test_imp_fmt.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets/import", json={
            "version": 1,
            "presets": [{"name": "X"}],  # missing params
        })
    assert resp.status_code == 400
    assert "name and params" in resp.json()["detail"]


def test_import_duplicate_names():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_imp_dup.json"):
        with open("/tmp/_test_imp_dup.json", "w") as f:
            json.dump({"presets": [
                {"id": "orig1", "name": "P1", "params": {"blur_kernel": 3}, "created": "2024-01-01"},
            ]}, f)
        resp = client.post("/api/presets/import", json={
            "version": 1,
            "presets": [
                {"name": "P1", "params": {"blur_kernel": 11}},
                {"name": "P2", "params": {"blur_kernel": 7}},
            ],
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["imported"] == 2
    assert data["skipped"] == 0
    with open("/tmp/_test_imp_dup.json") as f:
        cfg = json.load(f)
    # P1 was overwritten (still 1 entry), P2 added
    matches_p1 = [p for p in cfg["presets"] if p["name"] == "P1"]
    assert len(matches_p1) == 1
    assert matches_p1[0]["params"]["blur_kernel"] == 11  # overwritten
    assert len(cfg["presets"]) == 2  # P1 (overwritten) + P2


def test_import_empty_presets():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_imp_empty.json"):
        with open("/tmp/_test_imp_empty.json", "w") as f:
            f.write(PRESET_CONFIG)
        resp = client.post("/api/presets/import", json={
            "version": 1,
            "presets": [],
        })
    assert resp.status_code == 400
    assert "non-empty" in resp.json()["detail"]
