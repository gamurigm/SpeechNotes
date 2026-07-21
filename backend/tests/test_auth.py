"""
test_auth.py - Opt-in tests for the authentication flow.

These tests are only collected when TEST_AUTH=1 is set in the environment.
This is enforced by `collect_ignore_glob` in conftest.py.

IMPORTANT: The SpeechNotes auth module bypasses authentication when the
configured API_KEY equals the default `dev-secret-api-key` (see
backend/utils/auth.py:118-120). To exercise the real auth path, the
backend must be started with a real API_KEY in the environment before
running these tests, e.g.:

    export API_KEY=my-secret-key
    python backend/main.py

And in the test process:

    export TEST_AUTH=1
    export API_KEY=my-secret-key
    pytest backend/tests/test_auth.py -v
"""

from __future__ import annotations

import os

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.auth]


# The endpoints exercised here are guaranteed not to call external services
# so the assertions are deterministic. /health and /api/config/vad are
# both auth-free at the router level, so we cannot use them; we use
# /api/settings/ which is protected by require_auth (main.py:106).
PROTECTED_PATH = "/api/settings/"


def _expected_key() -> str:
    return os.environ.get("API_KEY", "dev-secret-api-key")


class TestValidCredentials:
    """When the right key is provided, the request is accepted."""

    def test_valid_api_key_accepted(self, http_client: BackendHttpClient):
        if _expected_key() == "dev-secret-api-key":
            pytest.skip(
                "El backend esta en modo dev (API_KEY=dev-secret-api-key); "
                "la auth se bypassa. Configura API_KEY en el entorno del backend "
                "para correr los tests de auth."
            )
        # http_client sends the correct x-api-key by default
        resp = http_client.get(PROTECTED_PATH)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_bearer_token_accepted(self, base_url: str):
        if _expected_key() == "dev-secret-api-key":
            pytest.skip("Backend en modo dev, auth bypassed")

        import requests

        key = _expected_key()
        resp = requests.get(
            f"{base_url.rstrip('/')}{PROTECTED_PATH}",
            headers={"Authorization": f"Bearer {key}"},
            timeout=10,
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"


class TestInvalidCredentials:
    """Bad or missing credentials must be rejected."""

    def test_missing_api_key_returns_401(self, base_url: str):
        if _expected_key() == "dev-secret-api-key":
            pytest.skip("Backend en modo dev, auth bypassed")

        import requests

        # Send no auth headers at all
        resp = requests.get(
            f"{base_url.rstrip('/')}{PROTECTED_PATH}",
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 sin credenciales, got {resp.status_code}: {resp.text}"
        )

    def test_invalid_api_key_returns_403(self, base_url: str):
        if _expected_key() == "dev-secret-api-key":
            pytest.skip("Backend en modo dev, auth bypassed")

        import requests

        resp = requests.get(
            f"{base_url.rstrip('/')}{PROTECTED_PATH}",
            headers={"x-api-key": "clave-claramente-incorrecta-12345"},
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 con clave invalida, got {resp.status_code}: {resp.text}"
        )
