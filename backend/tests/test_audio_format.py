"""
test_audio_format.py - Integration tests for /api/audio-format endpoints.

Covers (see backend/routers/audio_format.py):
    GET  /api/audio-format/profiles   ΓÇö list available conversion profiles
    POST /api/audio-format/cleanup    ΓÇö cleanup temp files
    POST /api/audio-format/detect     ΓÇö detect format (validation only)
    POST /api/audio-format/convert    ΓÇö single file convert (validation)

The file-based endpoints (detect, convert, normalize, trim, etc.) require
actual audio files on disk and are tested for validation/error paths only.
"""

from __future__ import annotations

import pytest

from backend.tests.helpers.http_client import BackendHttpClient


pytestmark = [pytest.mark.regression]


class TestListProfiles:
    """GET /api/audio-format/profiles"""

    def test_profiles_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/audio-format/profiles")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_profiles_returns_array(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/audio-format/profiles")
        body = resp.json()
        assert isinstance(body, list), f"Expected list, got {type(body).__name__}"

    def test_profiles_item_shape(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/audio-format/profiles")
        body = resp.json()
        if len(body) > 0:
            item = body[0]
            for field in ("name", "description", "settings"):
                assert field in item, f"Missing '{field}' in profile: {item}"

    def test_profiles_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.get(
            f"{base_url.rstrip('/')}/api/audio-format/profiles",
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestDetectFormat:
    """POST /api/audio-format/detect"""

    def test_detect_missing_file_returns_404(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/audio-format/detect", json_body={
            "file_path": "ruta/inexistente/audio.wav"
        })
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_detect_empty_path_returns_500(self, http_client: BackendHttpClient):
        """Empty path causes a filesystem error before validation, resulting in 500."""
        resp = http_client.post("/api/audio-format/detect", json_body={
            "file_path": ""
        })
        assert resp.status_code == 500, f"Expected 500, got {resp.status_code}: {resp.text}"

    def test_detect_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.post(
            f"{base_url.rstrip('/')}/api/audio-format/detect",
            json={"file_path": "test.wav"},
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestConvertFile:
    """POST /api/audio-format/convert"""

    def test_convert_missing_file_returns_404(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/audio-format/convert", json_body={
            "input_path": "ruta/inexistente/audio.wav",
            "output_format": "wav",
            "profile": "transcription",
        })
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_convert_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.post(
            f"{base_url.rstrip('/')}/api/audio-format/convert",
            json={"input_path": "test.wav"},
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestCleanup:
    """POST /api/audio-format/cleanup"""

    def test_cleanup_returns_200(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/audio-format/cleanup")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_cleanup_response_shape(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/audio-format/cleanup")
        body = resp.json()
        assert "status" in body
        assert body["status"] == "success"

    def test_cleanup_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.post(
            f"{base_url.rstrip('/')}/api/audio-format/cleanup",
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestBatchConvert:
    """POST /api/audio-format/batch"""

    def test_batch_empty_files_returns_400(self, http_client: BackendHttpClient):
        resp = http_client.post("/api/audio-format/batch", json_body={
            "files": [],
            "output_format": "wav",
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"

    def test_batch_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.post(
            f"{base_url.rstrip('/')}/api/audio-format/batch",
            json={"files": ["test.wav"]},
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestGetJob:
    """GET /api/audio-format/job/{job_id}"""

    def test_get_nonexistent_job_returns_404(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/audio-format/job/id-inexistente-job-9999")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_get_job_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.get(
            f"{base_url.rstrip('/')}/api/audio-format/job/nonexistent",
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )


class TestDownload:
    """GET /api/audio-format/download/{path}"""

    def test_download_nonexistent_file_returns_404(self, http_client: BackendHttpClient):
        resp = http_client.get("/api/audio-format/download/ruta/inexistente.wav")
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"

    def test_download_requires_auth(self, base_url: str, backend_health, api_key: str):
        import requests

        if api_key == "dev-secret-api-key":
            pytest.skip("Authentication is intentionally disabled in local development mode")

        resp = requests.get(
            f"{base_url.rstrip('/')}/api/audio-format/download/test.wav",
            timeout=10,
        )
        assert resp.status_code in (401, 403), (
            f"Expected 401/403 without auth, got {resp.status_code}"
        )
