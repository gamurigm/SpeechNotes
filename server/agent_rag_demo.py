"""Agent RAG demo

Indexa transcripciones usando `TranscriptionIndexer` y realiza una consulta RAG
usando el `VectorStore` y `NvidiaInferenceClient` (NIM). Este script es un pequeño
runner para validar que el pipeline RAG del agente funciona.

Uso:
    python server/agent_rag_demo.py --query "¿Cómo exporto una transcripción?"

Requisitos de entorno:
  - NVIDIA_EMBEDDING_API_KEY (para embeddings en `VectorStore`)
  - NVIDIA_API_KEY (para generación con `NvidiaInferenceClient`)
  - Opcional: tener archivos `notas/transcripcion_*.md` o `data/...` para indexar
"""
import argparse
import os
from pathlib import Path

from src.agent.vector_store import VectorStore
from src.agent.transcription_indexer import TranscriptionIndexer
from src.llm.nvidia_client import NvidiaInferenceClient


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", "-q", required=False, help="Consulta para RAG")
    parser.add_argument("--topk", type=int, default=3)
    parser.add_argument("--index-new-only", action="store_true", help="Indexar sólo nuevos archivos")
    args = parser.parse_args()

    # Check env vars
    emb_key = os.getenv("NVIDIA_EMBEDDING_API_KEY")
    gen_key = os.getenv("NVIDIA_API_KEY")

    if not emb_key:
        print("ERROR: NVIDIA_EMBEDDING_API_KEY no definido. Exporta la variable y vuelve a intentar.")
        print("Ejemplo (PowerShell): $env:NVIDIA_EMBEDDING_API_KEY = 'tu_key'")
        return

    if not gen_key:
        print("AVISO: NVIDIA_API_KEY no definido. La generación con NIM fallará si intentas generar texto.")

    # Initialize vector store and indexer
    try:
        vs = VectorStore()
    except Exception as e:
        print(f"ERROR al inicializar VectorStore: {e}")
        return

    indexer = TranscriptionIndexer(vs, source_dir="notas")

    # Index files
    try:
        if args.index_new_only:
            summary = indexer.index_new()
        else:
            summary = indexer.index_all()
        print(f"Indexado: {summary}")
    except Exception as e:
        print(f"ERROR durante la indexación: {e}")
        return

    # Get query
    if args.query:
        query = args.query
    else:
        query = input("Consulta RAG: ")

    # Perform search
    print(f"Buscando top {args.topk} para: {query}")
    results = vs.search(query, k=args.topk)

    if not results:
        print("No se encontraron resultados en el vector store.")
    else:
        print("Resultados recuperados:")
        for r in results:
            meta = r.get("metadata", {})
            print(f"- score={r['score']:.3f} file={meta.get('filename') or meta.get('source') or meta.get('file')}\n  {r['document'][:300].replace('\n',' ')}...\n")

    # Build context
    context = "\n\n".join([f"Fuente: {r.get('metadata',{}).get('filename', r.get('metadata',{}).get('file', 'unknown'))}\n{r['document']}" for r in results])

    # Generate with NVIDIA NIM if possible
    try:
        nim = NvidiaInferenceClient()
    except Exception as e:
        print(f"No se pudo inicializar NvidiaInferenceClient: {e}")
        nim = None

    if nim:
        prompt = f"Basándote en la siguiente información, responde brevemente:\n\nContexto:\n{context}\n\nPregunta: {query}\n\nRespuesta:"
        try:
            print("Generando respuesta con NVIDIA NIM...")
            resp = nim.generate(prompt)
            print("\n=== RESPUESTA ===\n")
            print(resp)
        except Exception as e:
            print(f"Error generando con NIM: {e}")
            print("Puedes revisar las variables de entorno o probar con otro LLM.")
    else:
        print("NIM no disponible — no se generó respuesta.")


if __name__ == '__main__':
    main()
