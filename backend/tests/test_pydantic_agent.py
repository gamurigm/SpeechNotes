import sys
from unittest.mock import patch, MagicMock
import pytest

# Ensure mocks for optional dependencies in lightweight CI environment
for mod in [
    "dotenv",
    "pydantic_ai",
    "logfire",
    "openai",
    "src.database.config_service",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

try:
    from backend.services.agents.pydantic_agent import (
        DocumentContext,
        ChatDependencies,
        ChatResponse,
        create_agent,
        chat_stream_direct,
    )
    HAS_PYDANTIC = True
except Exception:
    HAS_PYDANTIC = False


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_document_context_model():
    doc = DocumentContext(
        doc_id="doc-1",
        filename="clase1.md",
        title="Clase 1",
        content="Contenido de la transcripcion",
        content_type="formatted"
    )
    assert doc.doc_id == "doc-1"
    assert doc.content_type == "formatted"
    assert doc.content == "Contenido de la transcripcion"


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_dependencies():
    doc = DocumentContext(
        doc_id="doc-1",
        content="test",
        content_type="raw"
    )
    deps = ChatDependencies(active_document=doc)
    assert deps.active_document.doc_id == "doc-1"


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_response_model():
    resp = ChatResponse(answer="Respuesta", confidence=0.9, referenced_doc="clase1.md")
    assert resp.answer == "Respuesta"
    assert resp.confidence == 0.9
    assert resp.referenced_doc == "clase1.md"


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
@pytest.mark.asyncio
async def test_chat_stream_direct_missing_key_returns_error():
    doc = DocumentContext(
        doc_id="doc-1",
        content="test",
        content_type="raw"
    )

    with patch("backend.services.agents.pydantic_agent.NVIDIA_API_KEY_THINKING", None):
        with patch("backend.services.agents.pydantic_agent.NVIDIA_API_KEY_FAST", None):
            chunks = []
            async for chunk in chat_stream_direct("query", doc, thinking=True):
                chunks.append(chunk)

            assert len(chunks) > 0
            assert "Error" in chunks[0]
