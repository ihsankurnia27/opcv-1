"""Test the /api/send-to-server endpoint."""

import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.api import app

client = TestClient(app)


def _mock_response(body_dict=None, body_bytes=None):
    """Helper: create a mock that works as context manager for urlopen."""
    raw = body_bytes if body_bytes is not None else json.dumps(body_dict or {}).encode()
    m = MagicMock()
    m.read.return_value = raw
    ctx = MagicMock()
    ctx.__enter__.return_value = m
    return ctx


def test_send_missing_fields_returns_422():
    resp = client.post("/api/send-to-server")
    assert resp.status_code == 422


def test_send_no_url_configured_returns_502():
    with patch("app.api.CONFIG_PATH", "/tmp/_test_send_no_url.json"):
        with open("/tmp/_test_send_no_url.json", "w") as f:
            json.dump({"server_api_url": "", "point": "T", "api_key": ""}, f)
        resp = client.post("/api/send-to-server", data={
            "point": "T", "value": "1", "angle": "90",
        })
    assert resp.status_code == 502
    assert "configured" in resp.text


def test_send_ok_roundtrip():
    """Happy path: server returns 200 with status ok."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_send_ok.json"):
        with open("/tmp/_test_send_ok.json", "w") as f:
            json.dump({"server_api_url": "http://x/api", "point": "T", "api_key": ""}, f)
        with patch.object(urllib.request, "urlopen", return_value=_mock_response({"status": "ok", "shift": 1})):
            resp = client.post("/api/send-to-server", data={
                "point": "TEST-001", "value": "5.2", "angle": "180.0",
            })
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_send_authorization_header():
    """Verify Bearer token sent when api_key configured."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_send_auth.json"):
        with open("/tmp/_test_send_auth.json", "w") as f:
            json.dump({"server_api_url": "http://x/api", "point": "T", "api_key": "secret123"}, f)
        mock_urlopen = MagicMock(return_value=_mock_response({"status": "ok"}))
        with patch.object(urllib.request, "urlopen", mock_urlopen):
            resp = client.post("/api/send-to-server", data={
                "point": "T", "value": "1", "angle": "90",
            })
    assert resp.status_code == 200
    # Verify urlopen was called with a Request that has auth header
    mock_urlopen.assert_called_once()
    req_arg = mock_urlopen.call_args[0][0]
    assert req_arg.get_header("Authorization") == "Bearer secret123"


def test_send_server_returns_non_json():
    """Server returns garbage — JSONDecodeError → 502."""
    with patch("app.api.CONFIG_PATH", "/tmp/_test_send_badjson.json"):
        with open("/tmp/_test_send_badjson.json", "w") as f:
            json.dump({"server_api_url": "http://x/api", "point": "T", "api_key": ""}, f)
        with patch.object(urllib.request, "urlopen", return_value=_mock_response(body_bytes=b"<html>Bad</html>")):
            resp = client.post("/api/send-to-server", data={
                "point": "T", "value": "1", "angle": "90",
            })
    assert resp.status_code == 502
    assert "invalid response" in resp.text


def test_send_http_error_returns_502():
    """Server returns 5xx — proxy returns 502."""
    import urllib.error
    with patch("app.api.CONFIG_PATH", "/tmp/_test_send_httperr.json"):
        with open("/tmp/_test_send_httperr.json", "w") as f:
            json.dump({"server_api_url": "http://x/api", "point": "T", "api_key": ""}, f)
        http_err = urllib.error.HTTPError("http://x", 500, "Err", {}, None)
        http_err.read = MagicMock(return_value=b"")
        with patch.object(urllib.request, "urlopen", side_effect=http_err):
            resp = client.post("/api/send-to-server", data={
                "point": "T", "value": "1", "angle": "90",
            })
    assert resp.status_code == 502
    assert "500" in resp.text
