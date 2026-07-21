"""
Minimal FastAPI backend for the Pytest suite.

Only registers the 6 routers that the test suite exercises (health, VAD config,
transcriptions, documents, settings, admin, debug). This avoids pulling in the
heavy routers (chat, formatter, transcribe, audio_*, translation) which depend
on NVIDIA NIM, LangChain, Riva, and other services that aren't installed in
the test environment.

Run with:  python backend/main_test.py

IMPORTANT - Limitations of this test backend vs. the real one (main.py):
  - main_test.py is a STRICT SUBSET. The real main.py registers 12 routers;
    this one only registers the 6 above.
  - Storage split: the 4 routers tested here (transcriptions, documents,
    settings, vad_config) use the MongoManager alias which resolves to
    SQLiteManager. The fixtures therefore seed SQLite (data/speechnotes.db).
  - The real backend also has admin.py and formatter_agent.py which import
    `from src.database.mongo_manager import MongoManager` — that is the REAL
    MongoManager, not the alias. They are NOT covered by this test backend.
  - If you change admin.py or formatter_agent.py, the suite will not detect
    regressions. Test them manually against main.py with Mongo running.

See docs/QA/BACKEND_TESTS.md (section "Limitacion importante") for details.
"""

from __future__ import annotations

import os
import sys
import types

# Mirror the sys.path setup from the real main.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


# ── Pre-import stubs ────────────────────────────────────────────────────────
# src/__init__.py auto-imports src.core.* which drags in riva.client,
# nvidia-riva-client, smolagents, langchain, etc. We work around this by:
# 1. Stubbing the heavy third-party modules
# 2. Pre-loading 'src' as a stub with __path__ pointing to the real src dir,
#    so Python skips src/__init__.py but still finds subpackages
#    (src.database, src.database.config_service) normally.

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC_DIR = os.path.join(ROOT, "src")


def _stub_module(name: str) -> types.ModuleType:
    mod = types.ModuleType(name)
    mod.__path__ = []
    sys.modules[name] = mod
    return mod


# 1. Stub heavy third-party modules
for _mod in [
    "riva",
    "smolagents",
    "langchain",
    "langchain_community",
    "langchain_huggingface",
    "langchain_chroma",
    "chromadb",
    "sentence_transformers",
    "tf_keras",
    "nvidia_riva_client",
    "pydantic_ai",
    "faiss",
    "imageio_ffmpeg",
    "logfire",
    "openai",
    "pydub",
    "PyPDF2",
    "docx",
    "pptx",
    "PIL",
]:
    if _mod not in sys.modules:
        _stub_module(_mod)

# 2. Stub submodules so 'from riva.client import X' resolves
for _parent, _child in [
    ("riva", "client"),
    ("riva", "proto"),
    ("riva.client", "proto"),
    ("src.core", "environment_factory"),
    ("src.core", "riva_client"),
    ("src.core", "config"),
    ("src", "agent"),
    ("src", "agent.transcription_loader"),
    ("src", "agent.transcription_embedder"),
    ("src", "agent.transcription_indexer"),
    ("src", "agent.transcription_ingestor"),
    ("src", "agent.transcription_analyzer"),
    ("src", "agent.document_generator"),
    ("src", "agent.vector_store"),
    ("src", "agent.rag_agent"),
    ("src", "agent.state"),
    ("src", "agent.graph"),
    ("src", "agent.nodes"),
    ("src", "audio"),
    ("src", "audio.factory"),
    ("src", "transcription"),
    ("src", "transcription.service"),
    ("src", "transcription.formatters"),
    ("src", "llm"),
    ("src", "llm.nvidia_client"),
    ("src", "llm.embedding_client"),
]:
    _full = f"{_parent}.{_child}"
    if _full not in sys.modules:
        _stub_module(_full)

# 3. Provide dummy attributes commonly looked up
sys.modules["riva.client"].Auth = type("Auth", (), {})
sys.modules["riva.client"].ASRService = type("ASRService", (), {})
sys.modules["riva.client"].AudioEncoding = type("AudioEncoding", (), {})
sys.modules["riva.client"].StreamingRecognitionConfig = type("StreamingRecognitionConfig", (), {})
sys.modules["riva.client"].RecognitionConfig = type("RecognitionConfig", (), {})

# 4. Pre-stub 'src' itself with a real __path__ so it acts as a package
#    without running src/__init__.py
if "src" not in sys.modules:
    _src_stub = types.ModuleType("src")
    _src_stub.__path__ = [SRC_DIR]
    sys.modules["src"] = _src_stub

# Make sure the submodules of src/ that don't have heavy chains are loaded
# normally when accessed. We pre-load src.database explicitly so its
# __init__.py runs (which is lightweight).
import importlib
if "src.database" not in sys.modules:
    importlib.import_module("src.database")


from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

load_dotenv()

from backend.utils.auth import require_auth
from backend.routers import transcriptions, debug, admin, vad_config, documents, settings

app = FastAPI(
    title="SpeechNotes Test API",
    description="Minimal backend for Pytest integration tests",
    version="test-1.0.0",
)

# CORS middleware (same as main.py)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register only the routers exercised by the Pytest suite
app.include_router(transcriptions.router, prefix="/api/transcriptions", tags=["transcriptions"], dependencies=[Depends(require_auth)])
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])
app.include_router(vad_config.router, prefix="/api/config/vad", tags=["vad-config"])
app.include_router(documents.router, prefix="/api/documents", tags=["documents"], dependencies=[Depends(require_auth)])
app.include_router(settings.router, prefix="/api/settings", tags=["settings"])


@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "SpeechNotes Test API (minimal mode)",
        "version": "test-1.0.0",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 9443))
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)
