#!/usr/bin/env python3
"""
Index MongoDB Transcriptions into ChromaDB Vector Store

This script indexes all processed transcriptions from MongoDB into the ChromaDB vector store
for semantic search capabilities in the chat interface.

Usage:
    python scripts/index_documents.py
    
Environment Variables:
    - NVIDIA_EMBEDDING_API_KEY: Required for generating embeddings
    - MONGO_URI: MongoDB connection string (default: mongodb://localhost:27017/)
    - MONGO_DB_NAME: Database name (default: agent_knowledge_base)
"""

from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

from dotenv import load_dotenv
load_dotenv()

from services.rag_service import RagService


def main():
    print("=" * 60)
    print("Indexando documentos de MongoDB a ChromaDB")
    print("=" * 60)
    
    # Check environment
    if not os.getenv("NVIDIA_EMBEDDING_API_KEY"):
        print("❌ ERROR: NVIDIA_EMBEDDING_API_KEY no está configurada")
        print("Exporta la variable de entorno:")
        print("  export NVIDIA_EMBEDDING_API_KEY='tu_clave_aqui'  # Linux/Mac")
        print("  $env:NVIDIA_EMBEDDING_API_KEY='tu_clave_aqui'   # PowerShell")
        return 1
    
    # Initialize service
    try:
        print("\n🔧 Inicializando RAG Service...")
        service = RagService()
    except Exception as e:
        print(f"❌ Error inicializando servicio: {e}")
        return 1
    
    # Index documents
    try:
        print("\n📚 Indexando documentos de MongoDB...")
        count = service.index_documents_from_mongo()
        
        if count > 0:
            print(f"\n✅ ¡Éxito! Se indexaron {count} documentos nuevos")
            print("\nAhora puedes usar el chat en: http://localhost:3006/dashboard/chat")
        else:
            print("\n✓ No hay documentos nuevos para indexar")
            print("Todos los documentos ya están en el vector store")
        
        # Show stats
        total_docs = len(service.vector_store.collection.get()['ids'])
        print(f"\n📊 Total de documentos en vector store: {total_docs}")
        
    except Exception as e:
        print(f"\n❌ Error durante la indexación: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\n" + "=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
