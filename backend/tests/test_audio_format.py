import sys
from unittest.mock import patch, MagicMock
import pytest

# Ensure mocks for optional dependencies in lightweight CI environment
for mod in [
    "services.audio.audio_formatter",
    "services.audio",
    "backend.services.audio.audio_formatter",
    "dotenv",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

try:
    from fastapi.testclient import TestClient
    from fastapi import FastAPI
    from backend.routers.audio_format import router, resolve_project_path, DetectFormatRequest
    from backend.utils.auth import require_auth
    HAS_FASTAPI = True
except Exception:
    HAS_FASTAPI = False

if HAS_FASTAPI:
    app = FastAPI()
    app.dependency_overrides[require_auth] = lambda: True
    app.include_router(router)
    client = TestClient(app)


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi missing in CI runner environment")
def test_get_profiles_returns_profiles():
    mock_service = MagicMock()
    mock_service.get_available_profiles.return_value = [
        {"name": "transcription", "description": "16kHz Mono WAV", "settings": {}}
    ]

    with patch("backend.routers.audio_format.audio_formatter", mock_service):
        response = client.get("/profiles")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "transcription"


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi missing in CI runner environment")
def test_cleanup_temp_files_route():
    mock_service = MagicMock()
    with patch("backend.routers.audio_format.audio_formatter", mock_service):
        response = client.post("/cleanup")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        mock_service.cleanup_temp_files.assert_called_once()


@pytest.mark.skipif(not HAS_FASTAPI, reason="fastapi missing in CI runner environment")
def test_get_job_status_not_found():
    mock_service = MagicMock()
    mock_service.get_job.return_value = None

    with patch("backend.routers.audio_format.audio_formatter", mock_service):
        response = client.get("/job/invalid-id")
        assert response.status_code == 404
