"""
conftest.py - Shared fixtures for the SpeechNotes backend test suite.

All fixtures are designed for *integration* tests against a running backend.
The backend is expected to be reachable at BACKEND_URL (default localhost:9443).

Note: The SpeechNotes backend uses SQLite (via src.database.sqlite_manager)
for its data store, not MongoDB. The fixtures in this file use SQLite
accordingly. SQLite is essentially always available as a local file, so
the `db_client` fixture is rarely skipped.
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Iterator

import pytest

# Make the helpers package importable from test files.
from backend.tests.helpers.http_client import BackendHttpClient
from backend.tests.helpers.seed import (
    connect_db,
    cleanup_test_transcriptions,
    delete_transcription,
    insert_transcription,
    db_available,
    default_db_path,
)


# ──────────────────────────────────────────────────────────────
#  Configuration constants (read once at import time)
# ──────────────────────────────────────────────────────────────

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:9443")
API_KEY = os.environ.get("API_KEY", "dev-secret-api-key")
SQLITE_DB_DIR = os.environ.get("SQLITE_DB_DIR", "data")
RUN_AUTH_TESTS = os.environ.get("TEST_AUTH") == "1"

# Path to the VAD config file (mirrors backend/routers/vad_config.py:11-12)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
VAD_CONFIG_PATH = PROJECT_ROOT / "temporal_docs" / "configuracion" / ".vad_config.json"


# Skip test_auth.py unless TEST_AUTH=1 is exported.
collect_ignore_glob: list[str] = [] if RUN_AUTH_TESTS else ["test_auth.py"]


# ──────────────────────────────────────────────────────────────
#  Session-scoped fixtures
# ──────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def base_url() -> str:
    return BACKEND_URL


@pytest.fixture(scope="session")
def api_key() -> str:
    return API_KEY


@pytest.fixture(scope="session")
def db_path() -> str:
    """Absolute path to the SQLite database the backend is using."""
    p = default_db_path()
    if not os.path.isabs(p):
        p = str(PROJECT_ROOT / p)
    return p


@pytest.fixture(scope="session")
def backend_health(base_url: str) -> dict:
    """Verify the backend is up. Skip the whole module if not.

    Returns the JSON body of /health for use in assertions.
    """
    import requests

    try:
        resp = requests.get(f"{base_url.rstrip('/')}/health", timeout=5)
    except requests.RequestException as exc:
        pytest.skip(
            f"Backend no accesible en {base_url}/health ({exc}). "
            "Levanta el backend (run_all.ps1 o docker compose up backend) y vuelve a correr pytest."
        )

    if resp.status_code != 200:
        pytest.skip(
            f"Backend respondio {resp.status_code} en /health. "
            f"Cuerpo: {resp.text[:200]}"
        )

    try:
        return resp.json()
    except ValueError:
        return {"raw": resp.text}


@pytest.fixture(scope="session")
def http_client(base_url: str, api_key: str, backend_health) -> Iterator[BackendHttpClient]:
    """Shared requests Session configured with base URL and API key."""
    client = BackendHttpClient(base_url=base_url, api_key=api_key)
    yield client
    client.session.close()


@pytest.fixture(scope="session")
def db_client(db_path: str) -> Iterator[sqlite3.Connection]:
    """SQLite connection used by the test fixtures to seed/clean data.

    Skips the test if the database file cannot be opened.
    """
    if not db_available(db_path):
        pytest.skip(
            f"SQLite no accesible en {db_path}. "
            "Asegurate de que la ruta sea escribible."
        )
    conn = connect_db(db_path)
    yield conn
    # Belt-and-braces: cleanup any leftover test rows after the run
    try:
        cleanup_test_transcriptions(conn)
    finally:
        conn.close()


# ──────────────────────────────────────────────────────────────
#  Function-scoped fixtures for per-test isolation
# ──────────────────────────────────────────────────────────────

@pytest.fixture
def seed_transcription(db_client: sqlite3.Connection) -> Iterator[str]:
    """Insert a sample transcription and remove it after the test.

    Returns the inserted id.
    """
    doc_id = insert_transcription(
        db_client,
        raw_content="Esta es una transcripcion de prueba para tests automatizados.",
        formatted_content="# Test\n\nContenido formateado de prueba.",
        edited_content="",
    )
    try:
        yield doc_id
    finally:
        delete_transcription(db_client, doc_id)


@pytest.fixture
def seed_document(db_client: sqlite3.Connection) -> Iterator[str]:
    """Insert a transcription suitable for /api/documents/{id}/content tests.

    Sets processed=1 so the document is listed by GET /api/documents.
    """
    doc_id = insert_transcription(
        db_client,
        filename=f"{uuid.uuid4().hex[:10]}_qa.md",
        raw_content="Contenido en bruto del documento de prueba QA.",
        formatted_content="# Documento QA\n\nEste es un documento de prueba para el endpoint /content.",
        processed=True,
    )
    try:
        yield doc_id
    finally:
        delete_transcription(db_client, doc_id)


@pytest.fixture
def unique_id() -> str:
    """Unique identifier per test (for keys, names, etc.)."""
    return f"qa-{uuid.uuid4().hex[:10]}"


# ──────────────────────────────────────────────────────────────
#  VAD config backup/restore (autouse, only for test_vad_config.py)
# ──────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _vad_config_backup(request) -> Iterator[None]:
    """Back up and restore the real .vad_config.json so the VAD tests
    never leave the user's local config in a dirty state."""
    if request.node.fspath.basename != "test_vad_config.py":
        yield
        return

    had_file = VAD_CONFIG_PATH.exists()
    backup: bytes | None = None
    if had_file:
        backup = VAD_CONFIG_PATH.read_bytes()
    try:
        yield
    finally:
        # Restore original file (or delete if it didn't exist)
        try:
            if had_file and backup is not None:
                VAD_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
                VAD_CONFIG_PATH.write_bytes(backup)
            elif VAD_CONFIG_PATH.exists():
                VAD_CONFIG_PATH.unlink()
        except OSError:
            print(f"\n[WARN] Could not restore {VAD_CONFIG_PATH}")


# ──────────────────────────────────────────────────────────────
#  Test settings cleanup (autouse, only for test_settings.py)
# ──────────────────────────────────────────────────────────────

_TEST_SETTINGS_PREFIX = "qa_test_"


@pytest.fixture(autouse=True)
def _test_settings_cleanup(request, http_client: BackendHttpClient) -> Iterator[None]:
    """Remove any settings that start with the QA test prefix after the run."""
    if request.node.fspath.basename != "test_settings.py":
        yield
        return

    yield

    # Cleanup: list all settings and delete the ones we created
    try:
        resp = http_client.get("/api/settings/")
        if resp.status_code != 200:
            return
        data = resp.json()
        for item in data.get("settings", []):
            key = item.get("key", "")
            if key.startswith(_TEST_SETTINGS_PREFIX):
                http_client.delete(f"/api/settings/{key}")
    except Exception:
        pass
