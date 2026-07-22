"""
test_translation_integration.py - Integration tests for /api/translate endpoints.

Covers (see backend/routers/translation.py):
    POST /api/translate/           ΓÇö translate text
    POST /api/translate/detect     ΓÇö detect language
    POST /api/translate/batch      ΓÇö batch translate

All endpoints call external NVIDIA NIM services (Mistral Large, Gemma),
so these tests validate request schemas and error paths only.
"""

from __future__ import annotations

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


class TestTranslateText:
    """POST /api/translate/"""

    def test_translate_empty_text_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/", json_body={
            "text": "",
            "target_language": "es",
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_translate_missing_text_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/", json_body={
            "target_language": "es",
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_translate_valid_request_shape(self, http_client: BackendHttpClient):
        """May succeed if NVIDIA NIM is available, otherwise may 500."""
        resp = http_client.post("/api/translate/", json_body={
            "text": "Hello world",
            "target_language": "es",
            "source_language": "en",
            "preserve_formatting": True,
            "domain": "general",
        })
        assert resp.status_code in (200, 500), (
            f"Expected 200 or 500, got {resp.status_code}: {resp.text[:200]}"
        )


class TestDetectLanguage:
    """POST /api/translate/detect"""

    def test_detect_empty_text_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/detect", json_body={
            "text": "",
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_detect_missing_text_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/detect", json_body={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_detect_valid_request_shape(self, http_client: BackendHttpClient):
        """Valid request. If NIM is available, returns language info."""
        resp = http_client.post("/api/translate/detect", json_body={
            "text": "This is a sample text in English for language detection.",
        })
        assert resp.status_code in (200, 500), (
            f"Expected 200 or 500, got {resp.status_code}: {resp.text[:200]}"
        )
        if resp.status_code == 200:
            body = resp.json()
            for field in ("language_code", "language_name", "confidence"):
                assert field in body, f"Missing '{field}' in {body}"


class TestBatchTranslate:
    """POST /api/translate/batch"""

    def test_batch_empty_items_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/batch", json_body={
            "items": [],
            "target_language": "es",
        })
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_batch_missing_items_returns_422(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/translate/batch", json_body={})
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    def test_batch_valid_request_shape(self, http_client: BackendHttpClient):
        """Valid batch request. If NIM is available, returns translations."""
        resp = http_client.post("/api/translate/batch", json_body={
            "items": [
                {"id": "1", "text": "Hello world"},
                {"id": "2", "text": "Good morning"},
            ],
            "target_language": "es",
        })
        assert resp.status_code in (200, 500), (
            f"Expected 200 or 500, got {resp.status_code}: {resp.text[:200]}"
        )
        if resp.status_code == 200:
            body = resp.json()
            assert "results" in body
            assert isinstance(body["results"], list)
            assert len(body["results"]) == 2
