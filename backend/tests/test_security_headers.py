"""Security regression tests for HTTP hardening controls."""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Python 3.13+ removed audioop; these tests do not exercise audio processing.
sys.modules.setdefault("audioop", types.ModuleType("audioop"))
BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from backend.main import ALLOWED_ORIGINS, app


pytestmark = [pytest.mark.security]
client = TestClient(app)


SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
}


def test_health_sets_baseline_security_headers() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    for header, expected_value in SECURITY_HEADERS.items():
        assert response.headers.get(header) == expected_value

    permissions_policy = response.headers.get("permissions-policy", "")
    assert "geolocation=()" in permissions_policy
    assert "camera=()" in permissions_policy
    assert "microphone=(self)" in permissions_policy


def test_cors_preflight_allows_known_frontend_origin() -> None:
    origin = ALLOWED_ORIGINS[0]

    response = client.options(
        "/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type,x-api-key",
        },
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    for header in ("authorization", "content-type", "x-api-key"):
        assert header in allowed_headers


def test_cors_preflight_rejects_untrusted_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code in {400, 403}
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_never_uses_wildcard_with_credentials() -> None:
    response = client.get(
        "/health",
        headers={"Origin": "https://attacker.example"},
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "*"