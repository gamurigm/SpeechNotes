"""
Visualizar el flujo de LangGraph
Genera un diagrama del workflow del agente.
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import create_agent_graph


def visualize_graph():
    """Visualiza el grafo del agente."""
    print("=" * 60)
    print("VISUALIZACIÓN DEL GRAFO LANGGRAPH")
    print("=" * 60)
    
    # Crear el grafo
    print("\nCreando grafo del agente...")
    app = create_agent_graph()
    
    # Método 1: Representación ASCII
    print("\n" + "=" * 60)
    print("REPRESENTACIÓN ASCII DEL GRAFO")
    print("=" * 60)
    print("""
    ┌─────────────┐
    │   START     │
    └──────┬──────┘
           │
           ▼
    ┌─────────────┐
    │   ROUTER    │  ← Analiza la consulta
    └──────┬──────┘
           │
      ┌────┴────┐
      │         │
      ▼         ▼
┌──────────┐  ┌──────────┐
│  SEARCH  │  │  WRITE   │
│  (Query) │  │ (Direct) │
└────┬─────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            ▼
     ┌──────────┐
     │  WRITE   │  ← Genera respuesta
     │(w/Context)│
     └────┬─────┘
          │
          ▼
     ┌──────────┐
     │   END    │
     └──────────┘
    """)
    
    # Método 2: Información del grafo
    print("\n" + "=" * 60)
    print("INFORMACIÓN DEL GRAFO")
    print("=" * 60)
    
    print("\n📊 Nodos del grafo:")
    print("  1. router  - Decide si buscar o escribir directamente")
    print("  2. search  - Realiza búsqueda semántica en documentos")
    print("  3. write   - Genera texto con NVIDIA NIM")
    
    print("\n🔀 Transiciones condicionales:")
    print("  router → search  (si necesita búsqueda)")
    print("  router → write   (si es escritura directa)")
    print("  search → write   (siempre)")
    print("  write  → END     (siempre)")
    
    print("\n🎯 Lógica de routing:")
    print("  • Palabras clave de búsqueda:")
    print("    - buscar, search, encontrar, find")
    print("    - qué es, what is, información sobre")
    print("    - explica, explain, describe")
    print("  • Si NO contiene keywords → escritura directa")
    
    # Método 3: Generar diagrama Mermaid
    print("\n" + "=" * 60)
    print("DIAGRAMA MERMAID (para documentación)")
    print("=" * 60)
    print("""
```mermaid
graph TD
    START([Inicio]) --> ROUTER[Router Node]
    ROUTER -->|Necesita búsqueda| SEARCH[Search Node]
    ROUTER -->|Escritura directa| WRITE[Write Node]
    SEARCH --> WRITE
    WRITE --> END([Fin])
    
    style START fill:#90EE90
    style END fill:#FFB6C1
    style ROUTER fill:#87CEEB
    style SEARCH fill:#DDA0DD
    style WRITE fill:#F0E68C
```
    """)
    
    # Método 4: Intentar generar imagen (si tiene graphviz)
    print("\n" + "=" * 60)
    print("GENERACIÓN DE IMAGEN")
    print("=" * 60)
    
    try:
        # Intentar obtener la representación del grafo
        graph_repr = app.get_graph()
        
        print("\n✓ Grafo creado exitosamente")
        print(f"  Nodos: {len(graph_repr.nodes)}")
        print(f"  Aristas: {len(graph_repr.edges)}")
        
        # Intentar generar imagen PNG
        try:
            from IPython.display import Image, display
            
            # Generar imagen
            png_data = graph_repr.draw_mermaid_png()
            
            # Guardar imagen
            output_file = "langgraph_workflow.png"
            with open(output_file, "wb") as f:
                f.write(png_data)
            
            print(f"\n✓ Imagen guardada en: {output_file}")
            print("  Abre el archivo para ver el diagrama visual")
        
        except ImportError:
            print("\n⚠ Para generar imágenes PNG, instala:")
            print("  pip install pygraphviz")
            print("  (Requiere Graphviz instalado en el sistema)")
        
        except Exception as e:
            print(f"\n⚠ No se pudo generar imagen PNG: {str(e)}")
            print("  Usa el diagrama Mermaid o ASCII arriba")
    
    except Exception as e:
        print(f"\n⚠ Error obteniendo representación del grafo: {str(e)}")
    
    # Método 5: Mostrar código del grafo
    print("\n" + "=" * 60)
    print("CÓDIGO DEL GRAFO (src/agent/graph.py)")
    print("=" * 60)
    print("""
def create_agent_graph():
    workflow = StateGraph(AgentState)
    
    # Agregar nodos
    workflow.add_node("router", router_node)
    workflow.add_node("search", semantic_search_node)
    workflow.add_node("write", writing_node)
    
    # Punto de entrada
    workflow.set_entry_point("router")
    
    # Transiciones condicionales
    workflow.add_conditional_edges(
        "router",
        route_after_router,
        {"search": "search", "write": "write"}
    )
    
    workflow.add_conditional_edges(
        "search",
        route_after_search,
        {"write": "write"}
    )
    
    workflow.add_conditional_edges(
        "write",
        route_after_write,
        {END: END}
    )
    
    return workflow.compile()
    """)
    
    print("\n" + "=" * 60)
    print("EJEMPLOS DE FLUJO")
    print("=" * 60)
    
    print("\n📝 Ejemplo 1: Consulta de búsqueda")
    print("  Query: '¿Qué es FAISS?'")
    print("  Flujo: START → ROUTER → SEARCH → WRITE → END")
    print("  Razón: Contiene '¿Qué es' (keyword de búsqueda)")
    
    print("\n✍️ Ejemplo 2: Escritura directa")
    print("  Query: 'Escribe un haiku sobre programación'")
    print("  Flujo: START → ROUTER → WRITE → END")
    print("  Razón: No contiene keywords de búsqueda")
    
    print("\n🔍 Ejemplo 3: Búsqueda con contexto")
    print("  Query: 'Explica Python'")
    print("  Flujo: START → ROUTER → SEARCH → WRITE → END")
    print("  Razón: Contiene 'Explica' (keyword de búsqueda)")
    
    print("\n" + "=" * 60)
    print("✓ Visualización completa")
    print("=" * 60)


if __name__ == "__main__":
    visualize_graph()
