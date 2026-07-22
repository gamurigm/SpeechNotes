"""
test_documents.py - Tests for /api/documents (documents.py router).

Covers:
    GET /api/documents                 -> list metadata
    GET /api/documents/{id}/content    -> document text content
"""

from __future__ import annotations

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


VALID_CONTENT_TYPES = {"formatted", "raw", "edited", "segments", "empty"}


class TestListDocuments:
    """GET /api/documents?limit=N"""

    def test_list_documents_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/documents", params={"limit": 10})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_list_documents_returns_array(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/documents", params={"limit": 10})
        body = resp.json()
        assert isinstance(body, list), f"Expected list, got {type(body).__name__}: {body}"

    def test_list_documents_item_shape(self, http_client: BackendHttpClient, seed_document: str):
        resp = http_client.get("/api/documents", params={"limit": 50})
        assert resp.status_code == 200
        body = resp.json()
        assert len(body) > 0, "Expected at least the seeded document in the list"
        # Pick the seeded doc
        seeded = next((d for d in body if d.get("id") == seed_document), None)
        assert seeded is not None, f"Seeded document {seed_document} not in list"
        # DocumentMetadata has: id, filename (opt), date (opt), has_content (bool)
        assert "id" in seeded
        assert "has_content" in seeded
        assert isinstance(seeded["has_content"], bool)

    def test_list_documents_empty_when_no_processed(self, http_client: BackendHttpClient):
        """Without processed=True seed, default list may be empty or small.
        Just assert it returns a list and HTTP 200."""
        resp = http_client.get("/api/documents", params={"limit": 1})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestGetDocumentContent:
    """GET /api/documents/{id}/content"""

    def test_get_content_returns_200(self, http_client: BackendHttpClient, seed_document: str):
        resp = http_client.get(f"/api/documents/{seed_document}/content")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_get_content_shape(self, http_client: BackendHttpClient, seed_document: str):
        """DocumentContent has: id, content, content_type, title (opt), filename (opt)"""
        resp = http_client.get(f"/api/documents/{seed_document}/content")
        body = resp.json()
        assert "id" in body, f"Missing id in {body}"
        assert "content" in body, f"Missing content in {body}"
        assert "content_type" in body, f"Missing content_type in {body}"
        assert isinstance(body["content"], str)
        assert body["content_type"] in VALID_CONTENT_TYPES, (
            f"Unexpected content_type '{body['content_type']}', expected one of {VALID_CONTENT_TYPES}"
        )

    def test_get_content_404_when_missing(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/documents/id-que-no-existe-9876/content")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_get_content_includes_seeded_text(self, http_client: BackendHttpClient, seed_document: str):
        """The seed inserts formatted_content starting with '# Documento QA'."""
        resp = http_client.get(f"/api/documents/{seed_document}/content")
        body = resp.json()
        # Content source can be raw/formatted/edited; we set formatted_content
        # and raw_content, so either is fine
        assert "Documento QA" in body["content"] or "Contenido en bruto" in body["content"], (
            f"Seeded marker not found in content: {body['content'][:200]}"
        )


class TestDocumentsEdgeCases:
    """Edge cases and validation for /api/documents"""

    def test_list_with_negative_limit(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/documents", params={"limit": -1})
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}"

    def test_list_with_zero_limit(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/documents", params={"limit": 0})
        assert resp.status_code in (200, 422), f"Expected 200 or 422, got {resp.status_code}"

    def test_get_content_invalid_id_returns_404(self, http_client: BackendHttpClient):
        """Invalid ID format should return 404, not 500."""
        resp = http_client.get("/api/documents/invalid-id-!!! /content")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"

    def test_get_content_empty_id_returns_400(self, http_client: BackendHttpClient):
        """An empty/space ID is treated as a bad request."""
        resp = http_client.get("/api/documents/ /content")
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"

    def test_list_documents_response_is_list(self, http_client: BackendHttpClient):
        """Regardless of data, the endpoint must return a JSON list."""
        resp = http_client.get("/api/documents", params={"limit": 10})
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
