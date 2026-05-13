"""Test the /api/send-to-server endpoint."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def test_send_missing_fields_returns_422():
    resp = client.post("/api/send-to-server")
    assert resp.status_code in (400, 422)


def test_send_with_fields_returns_502():
    """server_api_url defaults to http://uvls-app/... which won't resolve in test."""
    resp = client.post("/api/send-to-server", data={
        "point": "TEST-001",
        "value": "5.2",
        "angle": "180.0",
        "annotated_image": "",
    })
    assert resp.status_code == 502
    assert any(w in resp.text for w in ["unreachable", "configured", "not known", "Errno"])
