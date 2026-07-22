"""
test_vad_config.py - Tests for /api/config/vad (VAD voice activity detection).

The VAD router is mounted without auth (main.py:102) and reads/writes a JSON
file at temporal_docs/configuracion/.vad_config.json (vad_config.py:11-12).

The conftest auto-fixture _vad_config_backup ensures any pre-existing config
file is restored after the test run, so these tests are safe to run against
a real local installation.
"""

from __future__ import annotations

import json

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


class TestGetVadConfig:
    """GET /api/config/vad - returns voice/silence thresholds."""

    def test_get_vad_config_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/config/vad")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_get_vad_config_schema(self, http_client: BackendHttpClient):
        """Body must include voice_threshold and silence_threshold as ints."""
        resp = http_client.get("/api/config/vad")
        body = resp.json()
        assert "voice_threshold" in body, f"Missing voice_threshold in {body}"
        assert "silence_threshold" in body, f"Missing silence_threshold in {body}"
        assert isinstance(body["voice_threshold"], int)
        assert isinstance(body["silence_threshold"], int)

    def test_get_vad_config_defaults_are_positive(self, http_client: BackendHttpClient):
        """Defaults from vad_config.py are 500/200; values must be positive ints."""
        resp = http_client.get("/api/config/vad")
        body = resp.json()
        assert body["voice_threshold"] > 0
        assert body["silence_threshold"] > 0


class TestPostVadConfig:
    """POST /api/config/vad - persists new thresholds."""

    def test_save_vad_config_returns_200_and_echo(self, http_client: BackendHttpClient):
        new_values = {"voice_threshold": 800, "silence_threshold": 300}
        resp = http_client.post("/api/config/vad", json_body=new_values)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert body.get("voice_threshold") == 800
        assert body.get("silence_threshold") == 300

    def test_save_vad_config_persists(self, http_client: BackendHttpClient):
        """After POST, a GET must return the new values."""
        new_values = {"voice_threshold": 1234, "silence_threshold": 567}
        post_resp = http_client.post("/api/config/vad", json_body=new_values)
        assert post_resp.status_code == 200

        get_resp = http_client.get("/api/config/vad")
        assert get_resp.status_code == 200
        body = get_resp.json()
        assert body["voice_threshold"] == 1234
        assert body["silence_threshold"] == 567

    def test_save_vad_config_writes_file(self, http_client: BackendHttpClient):
        """POST should create a .vad_config.json file with valid JSON."""
        from backend.tests.conftest import VAD_CONFIG_PATH

        new_values = {"voice_threshold": 999, "silence_threshold": 111}
        http_client.post("/api/config/vad", json_body=new_values)

        assert VAD_CONFIG_PATH.exists(), f"Expected file at {VAD_CONFIG_PATH}"
        with VAD_CONFIG_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["voice_threshold"] == 999
        assert data["silence_threshold"] == 111

    def test_save_vad_config_rejects_invalid_payload(self, http_client: BackendHttpClient):
        """Pydantic should return 422 for non-integer thresholds."""
        bad = {"voice_threshold": "no-es-numero", "silence_threshold": 100}
        resp = http_client.post("/api/config/vad", json_body=bad)
        assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}: {resp.text}"


class TestVadConfigEdgeCases:
    """VAD edge cases: boundary values, negative, missing fields."""

    def test_save_negative_threshold_returns_200_or_422(self, http_client: BackendHttpClient):
        """Negative thresholds may be accepted or rejected depending on validation."""
        resp = http_client.post("/api/config/vad", json_body={
            "voice_threshold": -100,
            "silence_threshold": -50,
        })
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}: {resp.text}"

    def test_save_zero_threshold_returns_200_or_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/config/vad", json_body={
            "voice_threshold": 0,
            "silence_threshold": 0,
        })
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}: {resp.text}"

    def test_save_missing_voice_threshold_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/config/vad", json_body={"silence_threshold": 200})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_save_large_values_returns_200_or_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/config/vad", json_body={
            "voice_threshold": 999999,
            "silence_threshold": 999999,
        })
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}: {resp.text}"

    def test_no_auth_required(self, base_url: str, backend_health):
        """VAD config endpoints are mounted without auth."""
        import requests

        resp = requests.get(f"{base_url.rstrip('/')}/api/config/vad", timeout=10)
        assert resp.status_code == 200

        resp = requests.post(f"{base_url.rstrip('/')}/api/config/vad",
                             json={"voice_threshold": 500, "silence_threshold": 200},
                             timeout=10)
        assert resp.status_code == 200
