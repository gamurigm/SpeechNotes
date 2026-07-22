import sys
import os
from unittest.mock import patch, MagicMock
import pytest

# Ensure mocks for optional imports
for mod in ["smolagents", "langchain_chroma", "opentelemetry", "opentelemetry.trace", "dotenv", "openai"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

if isinstance(sys.modules.get("smolagents"), MagicMock):
    sys.modules["smolagents"].tool = lambda f: f

from src.agent.rag_agent import search_knowledge_base, search_knowledge_base_by_file, RagAgent


def test_search_knowledge_base_handles_none_vectordb():
    with patch("src.agent.rag_agent.vectordb", None):
        result = search_knowledge_base("test query")
        assert "Contexto no disponible" in result


def test_search_knowledge_base_returns_documents():
    mock_doc = MagicMock()
    mock_doc.metadata = {"source": "nota1.md"}
    mock_doc.page_content = "Contenido de la nota 1"

    mock_db = MagicMock()
    mock_db.similarity_search.return_value = [mock_doc]

    with patch("src.agent.rag_agent.vectordb", mock_db):
        res = search_knowledge_base("pregunta sobre nota")
        assert "nota1.md" in res
        assert "Contenido de la nota 1" in res


def test_search_knowledge_base_by_file_filters_correctly():
    doc1 = MagicMock()
    doc1.metadata = {"source": "nota1.md", "filename": "clase1.md"}
    doc1.page_content = "Texto clase 1"

    doc2 = MagicMock()
    doc2.metadata = {"source": "nota2.md", "filename": "clase2.md"}
    doc2.page_content = "Texto clase 2"

    mock_db = MagicMock()
    mock_db.similarity_search.return_value = [doc1, doc2]

    with patch("src.agent.rag_agent.vectordb", mock_db):
        res = search_knowledge_base_by_file("test", "clase1.md")
        assert "Texto clase 1" in res
        assert "Texto clase 2" not in res


def test_rag_agent_get_context_text_reads_notes(tmp_path):
    notes_dir = tmp_path / "notas"
    notes_dir.mkdir()
    (notes_dir / "transcription_clase1.md").write_text("Contenido transcripcion clase 1", encoding="utf-8")

    with patch("src.agent.rag_agent.LLM_API_KEY", "test-key"):
        with patch("src.agent.rag_agent.OpenAI"):
            agent = RagAgent()
            agent.notes_dir = str(notes_dir)

            context = agent._get_context_text(active_file="clase1.md")
            assert "Contenido transcripcion clase 1" in context
