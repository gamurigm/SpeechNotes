"""
test_transcriptions.py - CRUD tests for /api/transcriptions.

Covers (see backend/routers/transcriptions.py):
    GET  /api/transcriptions/latest
    GET  /api/transcriptions?limit=N
    GET  /api/transcriptions/search?q=...
    GET  /api/transcriptions/{id}
    PUT  /api/transcriptions/{id}
    DELETE /api/transcriptions/{id}

Test data is seeded into MongoDB via the `seed_transcription` fixture
(autocleanup at the end of each test).
"""

from __future__ import annotations

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


class TestListTranscriptions:
    """GET /api/transcriptions?limit=N"""

    def test_list_transcriptions_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions", params={"limit": 10})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_list_transcriptions_returns_items_array(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions", params={"limit": 10})
        body = resp.json()
        assert "items" in body, f"Missing 'items' key in {body}"
        assert isinstance(body["items"], list)

    def test_list_transcriptions_includes_seeded(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.get("/api/transcriptions", params={"limit": 50})
        body = resp.json()
        ids = [item.get("id") or item.get("_id") for item in body["items"]]
        assert seed_transcription in ids, (
            f"Seeded transcription {seed_transcription} not found in list: {ids}"
        )

    def test_list_transcriptions_limit_honored(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions", params={"limit": 1})
        body = resp.json()
        assert len(body["items"]) <= 1


class TestLatestTranscription:
    """GET /api/transcriptions/latest"""

    def test_latest_returns_200_or_404(self, http_client: BackendHttpClient):
        """If no transcriptions exist, the endpoint may 404. Otherwise 200."""
        resp = http_client.get("/api/transcriptions/latest")
        assert resp.status_code in (200, 404), f"Expected 200/404, got {resp.status_code}"

    def test_latest_returns_object_when_present(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.get("/api/transcriptions/latest")
        if resp.status_code == 200:
            body = resp.json()
            # If body is not None, must contain some identifier
            if body is not None:
                assert isinstance(body, dict)
                assert ("id" in body) or ("_id" in body) or ("filename" in body)


class TestGetTranscriptionById:
    """GET /api/transcriptions/{id}"""

    def test_get_by_id_returns_200(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.get(f"/api/transcriptions/{seed_transcription}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_get_by_id_includes_filename(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.get(f"/api/transcriptions/{seed_transcription}")
        body = resp.json()
        # transcriptions_service.get_by_id returns the full document
        assert "filename" in body or "_id" in body, f"Unexpected shape: {body}"

    def test_get_by_id_404_when_missing(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions/id-que-no-existe-12345")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


class TestUpdateTranscription:
    """PUT /api/transcriptions/{id}"""

    def test_update_returns_200(self, http_client: BackendHttpClient, seed_transcription: str):
        payload = {"content": "Contenido actualizado por test QA"}
        resp = http_client.put(f"/api/transcriptions/{seed_transcription}", json_body=payload)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_update_response_shape(self, http_client: BackendHttpClient, seed_transcription: str):
        payload = {"content": "Otro contenido"}
        resp = http_client.put(f"/api/transcriptions/{seed_transcription}", json_body=payload)
        body = resp.json()
        assert body.get("status") == "updated", f"Expected status=updated, got {body}"

    def test_update_persists_content(self, http_client: BackendHttpClient, seed_transcription: str):
        new_content = "Contenido persistente del test de update"
        http_client.put(f"/api/transcriptions/{seed_transcription}", json_body={"content": new_content})

        # Re-fetch and confirm the change is visible
        resp = http_client.get(f"/api/transcriptions/{seed_transcription}")
        assert resp.status_code == 200
        body = resp.json()
        # The router stores via service.update_content which writes to edited_content
        # The exact key can vary (content/edited_content), so check any matches
        body_str = str(body)
        assert new_content in body_str, f"New content not found in response: {body}"

    def test_update_404_when_missing(self, http_client: BackendHttpClient):
        payload = {"content": "x"}
        resp = http_client.put("/api/transcriptions/id-inexistente-update-9999", json_body=payload)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


class TestDeleteTranscription:
    """DELETE /api/transcriptions/{id}"""

    def test_delete_returns_200(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.delete(f"/api/transcriptions/{seed_transcription}")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_delete_response_shape(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.delete(f"/api/transcriptions/{seed_transcription}")
        body = resp.json()
        assert body.get("status") == "deleted", f"Expected status=deleted, got {body}"

    def test_delete_404_when_missing(self, http_client: BackendHttpClient):
        resp = http_client.delete("/api/transcriptions/id-inexistente-delete-9999")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


class TestSearchTranscriptions:
    """GET /api/transcriptions/search?q=..."""

    def test_search_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions/search", params={"q": "test"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_search_returns_items_array(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions/search", params={"q": "qa"})
        body = resp.json()
        assert "items" in body, f"Missing 'items' in {body}"
        assert isinstance(body["items"], list)

    def test_search_finds_seeded_content(self, http_client: BackendHttpClient, seed_transcription: str):
        # The seed inserts raw_content with a known phrase
        unique_word = "QA-SEARCH-MARKER"
        # Inject a marker via update
        http_client.put(
            f"/api/transcriptions/{seed_transcription}",
            json_body={"content": f"# Test {unique_word}\n\nContenido unico"},
        )
        resp = http_client.get("/api/transcriptions/search", params={"q": unique_word})
        assert resp.status_code == 200
        body = resp.json()
        ids = [item.get("id") or item.get("_id") for item in body["items"]]
        assert seed_transcription in ids, f"Seeded doc not found in search: {ids}"


class TestTranscriptionsEdgeCases:
    """Edge cases and validation for /api/transcriptions"""

    def test_list_with_zero_limit(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions", params={"limit": 0})
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}"

    def test_search_empty_query(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions/search", params={"q": ""})
        assert resp.status_code in (200, 400, 422), f"Expected 200/400/422, got {resp.status_code}"

    def test_search_special_chars(self, http_client: BackendHttpClient):
        """Search with special regex characters should not crash."""
        resp = http_client.get("/api/transcriptions/search", params={"q": "test[.*?"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        body = resp.json()
        assert "items" in body

    def test_update_empty_content(self, http_client: BackendHttpClient, seed_transcription: str):
        resp = http_client.put(
            f"/api/transcriptions/{seed_transcription}",
            json_body={"content": ""},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_update_with_extra_fields(self, http_client: BackendHttpClient, seed_transcription: str):
        """Extra fields in the payload should be ignored, not rejected."""
        resp = http_client.put(
            f"/api/transcriptions/{seed_transcription}",
            json_body={"content": "nuevo", "extra_field": "should_be_ignored"},
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_list_with_large_limit(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/transcriptions", params={"limit": 10000})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_get_by_invalid_id_format(self, http_client: BackendHttpClient):
        """Invalid ID format should return 404, not 500."""
        resp = http_client.get("/api/transcriptions/invalid-id-format-!!!")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
