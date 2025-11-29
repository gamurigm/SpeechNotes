"""
Interactive Agent Demo
Run an interactive demo of the LangGraph agent with NVIDIA NIM.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import create_agent_graph, AgentState
from src.agent.nodes import get_vector_store


def setup_knowledge_base():
    """Setup the knowledge base with sample documents."""
    print("Configurando base de conocimientos...")
    
    vector_store = get_vector_store()
    
    # Check if already populated
    if len(vector_store) > 0:
        print(f"✓ Base de conocimientos ya contiene {len(vector_store)} documentos\n")
        return
    
    documents = [
        "Python es un lenguaje de programación de alto nivel, interpretado y de propósito general. "
        "Fue creado por Guido van Rossum y lanzado por primera vez en 1991. Es conocido por su "
        "sintaxis clara y legible, lo que lo hace ideal para principiantes y expertos.",
        
        "La inteligencia artificial (IA) es la simulación de procesos de inteligencia humana por "
        "parte de máquinas, especialmente sistemas informáticos. Incluye aprendizaje automático, "
        "procesamiento de lenguaje natural, visión por computadora y robótica.",
        
        "LangGraph es un framework desarrollado por LangChain para construir agentes con grafos de estado. "
        "Permite crear flujos de trabajo complejos con múltiples nodos, transiciones condicionales y "
        "gestión de estado, ideal para aplicaciones de IA conversacional.",
        
        "NVIDIA NIM (NVIDIA Inference Microservices) es una plataforma de inferencia que proporciona "
        "acceso a modelos de IA de última generación a través de APIs optimizadas. Incluye modelos de "
        "lenguaje como DeepSeek, embeddings de alta calidad y más.",
        
        "FAISS (Facebook AI Similarity Search) es una biblioteca desarrollada por Meta para búsqueda "
        "eficiente de similitud y agrupación de vectores densos. Es especialmente útil para búsqueda "
        "semántica en grandes conjuntos de datos.",
        
        "El aprendizaje automático (Machine Learning) es una rama de la IA que permite a las máquinas "
        "aprender de datos sin ser programadas explícitamente. Incluye técnicas como redes neuronales, "
        "árboles de decisión, y algoritmos de clustering.",
        
        "Los embeddings son representaciones vectoriales de texto que capturan el significado semántico. "
        "Se utilizan en búsqueda semántica, clasificación de texto y sistemas de recomendación.",
    ]
    
    metadata = [
        {"topic": "Python", "category": "Programming", "difficulty": "Beginner"},
        {"topic": "AI", "category": "Technology", "difficulty": "Intermediate"},
        {"topic": "LangGraph", "category": "Framework", "difficulty": "Advanced"},
        {"topic": "NVIDIA NIM", "category": "AI Platform", "difficulty": "Intermediate"},
        {"topic": "FAISS", "category": "Library", "difficulty": "Advanced"},
        {"topic": "Machine Learning", "category": "AI", "difficulty": "Intermediate"},
        {"topic": "Embeddings", "category": "NLP", "difficulty": "Advanced"},
    ]
    
    vector_store.add_documents(documents, metadata)
    print(f"✓ Agregados {len(documents)} documentos a la base de conocimientos\n")


def print_banner():
    """Print welcome banner."""
    print("\n" + "=" * 70)
    print(" " * 15 + "NVIDIA NIM + LangGraph Agent Demo")
    print("=" * 70)
    print("\nEste agente puede:")
    print("  • Buscar información en la base de conocimientos")
    print("  • Generar texto creativo")
    print("  • Responder preguntas basándose en contexto\n")
    print("Comandos especiales:")
    print("  /help    - Mostrar esta ayuda")
    print("  /docs    - Listar documentos en la base de conocimientos")
    print("  /clear   - Limpiar la base de conocimientos")
    print("  /exit    - Salir del demo")
    print("=" * 70 + "\n")


def list_documents():
    """List all documents in the vector store."""
    vector_store = get_vector_store()
    
    if len(vector_store) == 0:
        print("\n⚠ La base de conocimientos está vacía\n")
        return
    
    print(f"\n📚 Documentos en la base de conocimientos ({len(vector_store)}):")
    print("-" * 70)
    
    for i, (doc, meta) in enumerate(zip(vector_store.documents, vector_store.metadata), 1):
        topic = meta.get("topic", "N/A")
        category = meta.get("category", "N/A")
        print(f"\n[{i}] {topic} ({category})")
        print(f"    {doc[:100]}...")
    
    print("\n" + "-" * 70 + "\n")


def run_query(app, query: str):
    """Run a query through the agent."""
    initial_state: AgentState = {
        "messages": [{"role": "user", "content": query}],
        "query": query,
        "search_results": None,
        "generated_text": None,
        "next_action": "",
        "context": None
    }
    
    try:
        print("\n🤔 Procesando...\n")
        result = app.invoke(initial_state)
        
        # Show search results if any
        if result.get("search_results"):
            print("📊 Resultados de búsqueda:")
            for i, res in enumerate(result["search_results"], 1):
                print(f"  [{i}] {res['metadata'].get('topic', 'N/A')} (Score: {res['score']:.3f})")
            print()
        
        # Show generated response
        response = result.get("generated_text", "No se generó respuesta")
        print("💬 Respuesta:")
        print("-" * 70)
        print(response)
        print("-" * 70 + "\n")
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")


def main():
    """Run the interactive demo."""
    print_banner()
    
    # Setup
    setup_knowledge_base()
    
    # Create agent
    print("Inicializando agente...")
    app = create_agent_graph()
    print("✓ Agente listo\n")
    
    # Interactive loop
    while True:
        try:
            query = input("Tu pregunta: ").strip()
            
            if not query:
                continue
            
            # Handle commands
            if query.lower() == "/exit":
                print("\n👋 ¡Hasta luego!\n")
                break
            
            elif query.lower() == "/help":
                print_banner()
                continue
            
            elif query.lower() == "/docs":
                list_documents()
                continue
            
            elif query.lower() == "/clear":
                vector_store = get_vector_store()
                vector_store.clear()
                print("\n✓ Base de conocimientos limpiada\n")
                continue
            
            # Run query
            run_query(app, query)
        
        except KeyboardInterrupt:
            print("\n\n👋 ¡Hasta luego!\n")
            break
        
        except Exception as e:
            print(f"\n❌ Error inesperado: {str(e)}\n")


if __name__ == "__main__":
    main()
