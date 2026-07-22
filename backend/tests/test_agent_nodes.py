import sys
from unittest.mock import patch, MagicMock
import pytest

def _ensure_mock(mod_name):
    if mod_name not in sys.modules:
        try:
            __import__(mod_name)
        except ImportError:
            sys.modules[mod_name] = MagicMock()

for mod in ["langgraph", "langgraph.graph", "faiss", "dotenv", "openai", "numpy", "typing_extensions"]:
    _ensure_mock(mod)

if isinstance(sys.modules.get("langgraph"), MagicMock):
    sys.modules["langgraph"].graph.add_messages = lambda x, y: (x or []) + (y or [])
    sys.modules["langgraph.graph"] = sys.modules["langgraph"].graph

from src.agent.nodes import router_node, semantic_search_node, writing_node, get_llm_client, get_vector_store
from src.agent.state import AgentState


def test_router_node_defaults_to_write_when_no_documents():
    state: AgentState = {
        "messages": [],
        "query": "buscar informacion de prueba",
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None,
    }
    
    with patch("src.agent.nodes.vector_store") as mock_vs:
        mock_vs.__len__.return_value = 0
        res = router_node(state)
        assert res["next_action"] == "write"


def test_router_node_selects_search_when_keywords_present():
    state: AgentState = {
        "messages": [],
        "query": "buscar algo importante",
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None,
    }
    
    with patch("src.agent.nodes.vector_store") as mock_vs:
        mock_vs.__len__.return_value = 5
        res = router_node(state)
        assert res["next_action"] == "search"


def test_semantic_search_node_builds_context():
    state: AgentState = {
        "messages": [],
        "query": "test query",
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None,
    }
    
    mock_results = [
        {"document": "Doc 1 content", "score": 0.95},
        {"document": "Doc 2 content", "score": 0.85},
    ]
    
    with patch("src.agent.nodes.vector_store") as mock_vs:
        mock_vs.search.return_value = mock_results
        res = semantic_search_node(state)
        
        assert res["search_results"] == mock_results
        assert "Doc 1 content" in res["context"]
        assert res["next_action"] == "write"


def test_writing_node_invokes_llm_and_appends_message():
    state: AgentState = {
        "messages": [],
        "query": "Hola",
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": "Contexto simulado",
    }
    
    mock_llm = MagicMock()
    mock_llm.generate.return_value = "Respuesta simulada del LLM"
    
    with patch("src.agent.nodes.get_llm_client", return_value=mock_llm):
        res = writing_node(state)
        assert res["generated_text"] == "Respuesta simulada del LLM"
        assert res["next_action"] == "end"
        assert len(res["messages"]) == 1
        assert res["messages"][0]["content"] == "Respuesta simulada del LLM"
