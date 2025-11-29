"""
Test LangGraph Agent
Tests the complete agent workflow with semantic search and writing.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import create_agent_graph, AgentState
from src.agent.nodes import get_vector_store


def setup_sample_documents():
    """Add sample documents to the vector store."""
    print("Setting up sample documents...")
    
    vector_store = get_vector_store()
    
    documents = [
        "Python es un lenguaje de programación de alto nivel, interpretado y de propósito general. "
        "Fue creado por Guido van Rossum y lanzado por primera vez en 1991.",
        
        "La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana por "
        "parte de máquinas, especialmente sistemas informáticos. Incluye aprendizaje automático, "
        "procesamiento de lenguaje natural y visión por computadora.",
        
        "LangGraph es un framework para construir agentes con grafos de estado. Permite crear "
        "flujos de trabajo complejos con múltiples nodos y transiciones condicionales.",
        
        "NVIDIA NIM es una plataforma de inferencia que proporciona acceso a modelos de IA "
        "de última generación a través de APIs. Incluye modelos de lenguaje, embeddings y más.",
        
        "FAISS (Facebook AI Similarity Search) es una biblioteca para búsqueda eficiente de "
        "similitud y agrupación de vectores densos. Es especialmente útil para búsqueda semántica.",
    ]
    
    metadata = [
        {"topic": "Python", "category": "Programming"},
        {"topic": "AI", "category": "Technology"},
        {"topic": "LangGraph", "category": "Framework"},
        {"topic": "NVIDIA NIM", "category": "AI Platform"},
        {"topic": "FAISS", "category": "Library"},
    ]
    
    vector_store.add_documents(documents, metadata)
    print(f"✓ Added {len(documents)} documents to vector store\n")


def test_search_query():
    """Test agent with a search query."""
    print("=" * 60)
    print("Test 1: Search Query")
    print("=" * 60)
    
    app = create_agent_graph()
    
    query = "¿Qué es FAISS?"
    print(f"\nQuery: {query}\n")
    
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": query}],
        "query": query,
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None
    }
    
    try:
        result = app.invoke(initial_state)
        
        print("Search Results:")
        if result.get("search_results"):
            for i, res in enumerate(result["search_results"], 1):
                print(f"\n  [{i}] Score: {res['score']:.3f}")
                print(f"      {res['document'][:100]}...")
        
        print(f"\nGenerated Response:\n{result.get('generated_text', 'No response')}\n")
        print("✓ Test passed!")
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_direct_writing():
    """Test agent with a direct writing query."""
    print("\n" + "=" * 60)
    print("Test 2: Direct Writing Query")
    print("=" * 60)
    
    app = create_agent_graph()
    
    query = "Escribe un haiku sobre la programación."
    print(f"\nQuery: {query}\n")
    
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": query}],
        "query": query,
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None
    }
    
    try:
        result = app.invoke(initial_state)
        
        print(f"Generated Response:\n{result.get('generated_text', 'No response')}\n")
        print("✓ Test passed!")
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def test_search_with_context():
    """Test agent with search that provides context for writing."""
    print("\n" + "=" * 60)
    print("Test 3: Search with Context")
    print("=" * 60)
    
    app = create_agent_graph()
    
    query = "Explica qué es Python y para qué se usa"
    print(f"\nQuery: {query}\n")
    
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": query}],
        "query": query,
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None
    }
    
    try:
        result = app.invoke(initial_state)
        
        print("Search Results:")
        if result.get("search_results"):
            for i, res in enumerate(result["search_results"], 1):
                print(f"\n  [{i}] Score: {res['score']:.3f}")
                print(f"      Topic: {res['metadata'].get('topic', 'N/A')}")
        
        print(f"\nGenerated Response:\n{result.get('generated_text', 'No response')}\n")
        print("✓ Test passed!")
        return True
    
    except Exception as e:
        print(f"✗ Test failed: {str(e)}")
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("LANGGRAPH AGENT TESTS")
    print("=" * 60 + "\n")
    
    # Setup
    setup_sample_documents()
    
    # Run tests
    tests = [
        test_search_query,
        test_direct_writing,
        test_search_with_context
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"\n✗ Unexpected error: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {total - passed} test(s) failed")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
