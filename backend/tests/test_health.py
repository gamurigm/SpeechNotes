"""
test_health.py - Smoke tests for the root and health endpoints.

These are the fastest tests in the suite and confirm that the backend
process is up, responding, and returning the expected JSON shape.
"""

from __future__ import annotations

import time

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.smoke]


class TestRoot:
    """GET / - root endpoint defined in main.py:125-131"""

    def test_root_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_root_returns_ok_status(self, http_client: BackendHttpClient):
        resp = http_client.get("/")
        body = resp.json()
        assert body.get("status") == "ok", f"Expected status=ok, got {body}"

    def test_root_includes_message(self, http_client: BackendHttpClient):
        resp = http_client.get("/")
        body = resp.json()
        assert "message" in body, f"Missing 'message' in {body}"
        assert isinstance(body["message"], str)
        assert len(body["message"]) > 0

    def test_root_includes_version_string(self, http_client: BackendHttpClient):
        resp = http_client.get("/")
        body = resp.json()
        assert "version" in body, f"Missing 'version' in {body}"
        assert isinstance(body["version"], str)
        assert len(body["version"]) > 0


class TestHealth:
    """GET /health - health check defined in main.py:133-135"""

    def test_health_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/health")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    def test_health_reports_healthy(self, http_client: BackendHttpClient):
        resp = http_client.get("/health")
        body = resp.json()
        assert body.get("status") == "healthy", f"Expected status=healthy, got {body}"

    def test_health_responds_quickly(self, http_client: BackendHttpClient):
        start = time.perf_counter()
        resp = http_client.get("/health")
        elapsed = time.perf_counter() - start
        assert resp.status_code == 200
        # 3s is generous: /health should respond in < 50ms on a healthy
        # backend, but cold CI runners and shared hosts can add latency.
        assert elapsed < 3.0, f"/health tardo {elapsed:.2f}s, esperado < 3s"

    def test_health_response_keys(self, http_client: BackendHttpClient):
        resp = http_client.get("/health")
        body = resp.json()
        # At minimum, must contain status
        assert "status" in body, f"Missing 'status' in {body}"

    def test_root_no_auth_required(self, base_url: str, backend_health):
        """Root and health endpoints must be accessible without API key."""
        import requests

        resp = requests.get(f"{base_url.rstrip('/')}/", timeout=10)
        assert resp.status_code == 200

        resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=10)
        assert resp.status_code == 200
