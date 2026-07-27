"""Security regression tests for HTTP hardening controls.

These tests intentionally call the running backend instead of importing
``backend.main``. The CI job already starts uvicorn before pytest, and avoiding
application imports keeps collection independent from optional AI/audio routers.
"""

from __future__ import annotations

import os

import pytest
import requests


pytestmark = [pytest.mark.security]

DEFAULT_ALLOWED_ORIGINS = [
    "http://localhost:3006",
    "http://127.0.0.1:3006",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

SECURITY_HEADERS = {
    "x-content-type-options": "nosniff",
    "x-frame-options": "DENY",
    "referrer-policy": "no-referrer",
}


def allowed_origin() -> str:
    configured = os.environ.get("BACKEND_CORS_ORIGINS", "")
    origins = [origin.strip() for origin in configured.split(",") if origin.strip()]
    return origins[0] if origins else DEFAULT_ALLOWED_ORIGINS[0]


def test_health_sets_baseline_security_headers(base_url: str, backend_health) -> None:
    response = requests.get(f"{base_url.rstrip('/')}/health", timeout=10)

    assert response.status_code == 200
    for header, expected_value in SECURITY_HEADERS.items():
        assert response.headers.get(header) == expected_value

    permissions_policy = response.headers.get("permissions-policy", "")
    assert "geolocation=()" in permissions_policy
    assert "camera=()" in permissions_policy
    assert "microphone=(self)" in permissions_policy


def test_cors_preflight_allows_known_frontend_origin(base_url: str, backend_health) -> None:
    origin = allowed_origin()

    response = requests.options(
        f"{base_url.rstrip('/')}/health",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization,content-type,x-api-key",
        },
        timeout=10,
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == origin
    assert response.headers.get("access-control-allow-credentials") == "true"
    allowed_headers = response.headers.get("access-control-allow-headers", "").lower()
    for header in ("authorization", "content-type", "x-api-key"):
        assert header in allowed_headers


def test_cors_preflight_rejects_untrusted_origin(base_url: str, backend_health) -> None:
    response = requests.options(
        f"{base_url.rstrip('/')}/health",
        headers={
            "Origin": "https://attacker.example",
            "Access-Control-Request-Method": "GET",
        },
        timeout=10,
    )

    assert response.status_code in {400, 403}
    assert response.headers.get("access-control-allow-origin") is None


def test_cors_never_uses_wildcard_with_credentials(base_url: str, backend_health) -> None:
    response = requests.get(
        f"{base_url.rstrip('/')}/health",
        headers={"Origin": "https://attacker.example"},
        timeout=10,
    )

    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != "*"