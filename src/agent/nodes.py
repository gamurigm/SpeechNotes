"""
Agent Nodes
Defines the nodes for the LangGraph agent workflow.
"""

from typing import Dict, Any
from .state import AgentState
from .vector_store import VectorStore
from src.llm.nvidia_client import NvidiaInferenceClient


# Global instances (initialized once)
vector_store = VectorStore()
_llm_client = None  # Lazy-loaded


def get_llm_client():
    """Lazy load LLM client only when needed"""
    global _llm_client
    if _llm_client is None:
        _llm_client = NvidiaInferenceClient()
    return _llm_client


def router_node(state: AgentState) -> AgentState:
    """
    Router node - decides what action to take based on the query.
    
    Analyzes the user query to determine if it requires:
    - Semantic search (finding relevant information)
    - Direct writing/generation
    """
    query = state["query"]
    
    # Simple heuristic: if query contains search keywords, do search
    search_keywords = [
        "buscar", "search", "encontrar", "find", "qué es", "what is",
        "información sobre", "information about", "dime sobre", "tell me about",
        "explica", "explain", "describe", "cuál", "which"
    ]
    
    query_lower = query.lower()
    needs_search = any(keyword in query_lower for keyword in search_keywords)
    
    # Check if vector store has documents
    has_documents = len(vector_store) > 0
    
    if needs_search and has_documents:
        state["next_action"] = "search"
    else:
        state["next_action"] = "write"
    
    return state


def semantic_search_node(state: AgentState) -> AgentState:
    """
    Semantic search node - performs vector search on indexed documents.
    """
    query = state["query"]
    
    # Perform search
    results = vector_store.search(query, k=3)
    
    state["search_results"] = results
    
    # Build context from search results
    if results:
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Resultado {i}] (Score: {result['score']:.3f})\n{result['document']}"
            )
        state["context"] = "\n\n".join(context_parts)
    else:
        state["context"] = "No se encontraron resultados relevantes."
    
    state["next_action"] = "write"
    
    return state


def writing_node(state: AgentState) -> AgentState:
    """
    Writing node - generates text using NVIDIA NIM API.
    """
    query = state["query"]
    context = state.get("context", "")
    
    # Build prompt
    if context:
        prompt = f"""Basándote en la siguiente información de contexto, responde a la pregunta del usuario.

Contexto:
{context}

Pregunta: {query}

Respuesta:"""
    else:
        prompt = query
    
    # Generate response
    try:
        llm = get_llm_client()  # Lazy load
        response = llm.generate(prompt)
        state["generated_text"] = response
        
        # Add to messages
        state["messages"].append({
            "role": "assistant",
            "content": response
        })
    
    except Exception as e:
        error_msg = f"Error generando respuesta: {str(e)}"
        state["generated_text"] = error_msg
        state["messages"].append({
            "role": "assistant",
            "content": error_msg
        })
    
    state["next_action"] = "end"
    
    return state


def get_vector_store() -> VectorStore:
    """Get the global vector store instance."""
    return vector_store
