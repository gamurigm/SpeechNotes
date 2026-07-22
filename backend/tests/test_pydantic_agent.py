import sys
from unittest.mock import patch, MagicMock, AsyncMock
from types import SimpleNamespace
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
def test_chat_stream_direct_missing_key_returns_error():
    import asyncio

    async def _run():
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

    asyncio.run(_run())


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_with_document_success_and_failure():
    import asyncio
    from backend.services.agents import pydantic_agent as module

    doc = DocumentContext(doc_id="doc", content="contenido", content_type="raw")

    async def _run():
        agent = MagicMock()
        agent.run = AsyncMock(return_value=SimpleNamespace(output="respuesta"))
        with patch.object(module, "get_agent", return_value=agent):
            assert await module.chat_with_document("hola", doc) == "respuesta"
        agent.run.side_effect = RuntimeError("provider")
        with patch.object(module, "get_agent", return_value=agent):
            with pytest.raises(RuntimeError, match="provider"):
                await module.chat_with_document("hola", doc)

    asyncio.run(_run())


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_stream_with_document_success_and_failure():
    import asyncio
    from backend.services.agents import pydantic_agent as module

    doc = DocumentContext(doc_id="doc", content="contenido", content_type="raw")

    class StreamContext:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return None

        async def stream_text(self):
            for chunk in ("uno", "dos"):
                yield chunk

    async def _run():
        agent = MagicMock()
        agent.run_stream.return_value = StreamContext()
        with patch.object(module, "get_agent", return_value=agent):
            chunks = [chunk async for chunk in module.chat_stream_with_document("hola", doc)]
        assert chunks == ["uno", "dos"]

        class BrokenAgent:
            def run_stream(self, *args, **kwargs):
                raise RuntimeError("stream failed")

        with patch.object(module, "get_agent", return_value=BrokenAgent()):
            chunks = [chunk async for chunk in module.chat_stream_with_document("hola", doc)]
        assert "stream failed" in chunks[0]

    asyncio.run(_run())


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_stream_direct_yields_content_and_reasoning_heartbeat():
    import asyncio
    from backend.services.agents import pydantic_agent as module

    doc = DocumentContext(doc_id="doc", filename="clase.md", content="contenido", content_type="raw")

    async def response_stream():
        yield SimpleNamespace(choices=[])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(reasoning_content="pensando", content=None))])
        yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(reasoning_content=None, content="respuesta"))])

    async def _run():
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=response_stream())
        with patch.object(module, "NVIDIA_API_KEY_THINKING", "key"), \
             patch.object(module, "AsyncOpenAI", return_value=client):
            chunks = [chunk async for chunk in module.chat_stream_direct("hola", doc, thinking=True)]
        assert " " in chunks and "respuesta" in chunks
        client.chat.completions.create.assert_awaited_once()

    asyncio.run(_run())


@pytest.mark.skipif(not HAS_PYDANTIC, reason="pydantic missing in test environment")
def test_chat_stream_direct_propagates_provider_error_as_chunk():
    import asyncio
    from backend.services.agents import pydantic_agent as module

    doc = DocumentContext(doc_id="doc", content="contenido", content_type="raw")

    async def _run():
        client = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=RuntimeError("NIM down"))
        with patch.object(module, "NVIDIA_API_KEY_FAST", "fast-key"), \
             patch.object(module, "NVIDIA_API_KEY_THINKING", None), \
             patch.object(module, "AsyncOpenAI", return_value=client):
            chunks = [chunk async for chunk in module.chat_stream_direct("hola", doc, thinking=False)]
        assert any("NIM down" in chunk for chunk in chunks)

    asyncio.run(_run())
