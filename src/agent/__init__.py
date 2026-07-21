"""Agent package with optional components loaded only when requested."""

from importlib import import_module
from typing import Any

__all__ = [
    "AgentState",
    "create_agent_graph",
    "VectorStore",
    "TranscriptionLoader",
    "TranscriptionIndexer"
]

_LAZY_IMPORTS = {
    "AgentState": (".state", "AgentState"),
    "create_agent_graph": (".graph", "create_agent_graph"),
    "VectorStore": (".vector_store", "VectorStore"),
    "TranscriptionLoader": (".transcription_loader", "TranscriptionLoader"),
    "TranscriptionIndexer": (".transcription_indexer", "TranscriptionIndexer"),
}


def __getattr__(name: str) -> Any:
    """Load legacy LangGraph/FAISS exports only when explicitly accessed."""
    if name not in _LAZY_IMPORTS:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    module_name, attribute_name = _LAZY_IMPORTS[name]
    value = getattr(import_module(module_name, __name__), attribute_name)
    globals()[name] = value
    return value
