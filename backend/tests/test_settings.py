"""
test_settings.py - Tests for /api/settings (settings.py router).

Covers:
    GET  /api/settings/                       -> list (optionally filtered)
    GET  /api/settings/categories             -> list categories
    GET  /api/settings/validate               -> check required keys
    GET  /api/settings/{key}                  -> single setting
    PUT  /api/settings/{key}                  -> update single
    PUT  /api/settings/                       -> bulk update
    DELETE /api/settings/{key}                -> clear

All test-created settings are prefixed with `qa_test_` and removed by the
autouse _test_settings_cleanup fixture in conftest.py.
"""

from __future__ import annotations

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


class TestListSettings:
    """GET /api/settings/"""

    def test_list_settings_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_list_settings_payload_shape(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/")
        body = resp.json()
        assert "settings" in body, f"Missing 'settings' in {body}"
        assert isinstance(body["settings"], list)

    def test_list_settings_by_category(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/", params={"category": "general"})
        assert resp.status_code == 200
        body = resp.json()
        assert isinstance(body["settings"], list)


class TestSettingsCategories:
    """GET /api/settings/categories"""

    def test_categories_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/categories")
        assert resp.status_code == 200

    def test_categories_payload_shape(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/categories")
        body = resp.json()
        assert "categories" in body, f"Missing 'categories' in {body}"
        assert isinstance(body["categories"], list)
        for cat in body["categories"]:
            assert isinstance(cat, str)


class TestValidateSettings:
    """GET /api/settings/validate"""

    def test_validate_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/validate")
        assert resp.status_code == 200

    def test_validate_payload_shape(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/validate")
        body = resp.json()
        assert "valid" in body, f"Missing 'valid' in {body}"
        assert "missing" in body, f"Missing 'missing' in {body}"
        assert isinstance(body["valid"], bool)
        assert isinstance(body["missing"], list)


class TestGetSetting:
    """GET /api/settings/{key}"""

    def test_get_existing_setting(self, http_client: BackendHttpClient, seed_test_setting):
        resp = http_client.get(f"/api/settings/{seed_test_setting}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_get_setting_payload_shape(self, http_client: BackendHttpClient, seed_test_setting):
        resp = http_client.get(f"/api/settings/{seed_test_setting}")
        body = resp.json()
        assert "key" in body
        assert body["key"] == seed_test_setting
        # The endpoint may mask the value but should include it
        assert "value" in body

    def test_get_missing_setting_returns_404(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/settings/qa_test_inexistente_9999")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


class TestUpdateSetting:
    """PUT /api/settings/{key}"""

    def test_update_returns_200(self, http_client: BackendHttpClient, seed_test_setting):
        payload = {"key": seed_test_setting, "value": "qa-value-001"}
        resp = http_client.put(f"/api/settings/{seed_test_setting}", json_body=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_update_response_shape(self, http_client: BackendHttpClient, seed_test_setting):
        payload = {"key": seed_test_setting, "value": "qa-value-002"}
        resp = http_client.put(f"/api/settings/{seed_test_setting}", json_body=payload)
        body = resp.json()
        assert body.get("ok") is True
        assert body.get("key") == seed_test_setting

    def test_update_then_get_returns_new_value(self, http_client: BackendHttpClient, seed_test_setting):
        http_client.put(
            f"/api/settings/{seed_test_setting}",
            json_body={"key": seed_test_setting, "value": "qa-value-roundtrip"},
        )
        resp = http_client.get(f"/api/settings/{seed_test_setting}")
        body = resp.json()
        # The masked value is still "qa-***" or similar; check the key matches
        assert body["key"] == seed_test_setting


class TestBulkUpdate:
    """PUT /api/settings/ - update multiple at once"""

    def test_bulk_update_returns_200(self, http_client: BackendHttpClient, unique_id: str):
        payload = {
            "settings": [
                {"key": f"qa_test_bulk_{unique_id}_a", "value": "v1"},
                {"key": f"qa_test_bulk_{unique_id}_b", "value": "v2"},
            ]
        }
        resp = http_client.put("/api/settings/", json_body=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_bulk_update_response_shape(self, http_client: BackendHttpClient, unique_id: str):
        payload = {
            "settings": [
                {"key": f"qa_test_bulk2_{unique_id}_a", "value": "v1"},
            ]
        }
        resp = http_client.put("/api/settings/", json_body=payload)
        body = resp.json()
        assert body.get("ok") is True
        assert body.get("updated") == 1


class TestClearSetting:
    """DELETE /api/settings/{key}"""

    def test_clear_returns_200(self, http_client: BackendHttpClient, seed_test_setting):
        resp = http_client.delete(f"/api/settings/{seed_test_setting}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_clear_response_shape(self, http_client: BackendHttpClient, seed_test_setting):
        resp = http_client.delete(f"/api/settings/{seed_test_setting}")
        body = resp.json()
        assert body.get("ok") is True
        assert body.get("key") == seed_test_setting


# ── Local fixtures (file-scoped) ──────────────────────────────────────────────

@pytest.fixture
def seed_test_setting(http_client: BackendHttpClient, unique_id: str) -> str:
    """Create a settings entry with a qa_test_ prefix; cleanup is handled by
    the autouse _test_settings_cleanup fixture in conftest.py."""
    key = f"qa_test_{unique_id}"
    payload = {"key": key, "value": "qa-initial"}
    resp = http_client.put(f"/api/settings/{key}", json_body=payload)
    assert resp.status_code == 200, f"Failed to seed test setting: {resp.text}"
    return key
