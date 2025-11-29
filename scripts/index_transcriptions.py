"""
Index Transcriptions Script
Manually index transcriptions from notas/ directory.
"""

import sys
import os
import argparse

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent import TranscriptionIndexer
from src.agent.nodes import get_vector_store


def main():
    parser = argparse.ArgumentParser(
        description="Index transcriptions into the vector store"
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Index all transcriptions (default: only new/updated)'
    )
    parser.add_argument(
        '--recent',
        type=int,
        metavar='N',
        help='Index only the N most recent transcriptions'
    )
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild index from scratch (clears existing index)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List indexed transcriptions'
    )
    
    args = parser.parse_args()
    
    # Get vector store
    try:
        vector_store = get_vector_store()
    except Exception as e:
        print(f"[ERROR] Error getting vector store: {e}")
        return
    
    # Create indexer
    indexer = TranscriptionIndexer(vector_store)
    
    # Handle list command
    if args.list:
        print("\n" + "=" * 60)
        print("TRANSCRIPCIONES INDEXADAS")
        print("=" * 60 + "\n")
        
        files = indexer.get_indexed_files()
        
        if not files:
            print("[WARN] No hay transcripciones indexadas")
        else:
            for i, file_info in enumerate(files, 1):
                print(f"{i}. {file_info['filename']}")
                print(f"   Fecha: {file_info['date']}")
                print(f"   Chunks: {file_info['chunks']}")
                print(f"   Indexado: {file_info['indexed_at']}")
                print()
        
        print("=" * 60 + "\n")
        return
    
    # Handle rebuild
    if args.rebuild:
        print("\n[WARN] ADVERTENCIA: Esto eliminara el indice actual")
        response = input("Continuar? (s/N): ")
        if response.lower() != 's':
            print("Operacion cancelada")
            return
        
        print("[INFO] Limpiando vector store...")
        vector_store.clear()
        print("[OK] Vector store limpiado\n")
    
    # Index transcriptions
    if args.all or args.rebuild:
        result = indexer.index_all()
    elif args.recent:
        print(f"\n[INFO] Indexando las {args.recent} transcripciones mas recientes...\n")
        from src.agent import TranscriptionLoader
        loader = TranscriptionLoader()
        recent_files = loader.get_recent(args.recent)
        
        results = []
        total_chunks = 0
        
        for file_path in recent_files:
            try:
                result = indexer.index_transcription(file_path)
                results.append(result)
                total_chunks += result["chunks"]
                print()
            except Exception as e:
                print(f"[ERROR] Error procesando {file_path.name}: {e}\n")
                import traceback
                traceback.print_exc()
        
        print("=" * 60)
        print(f"[OK] Indexacion completa:")
        print(f"   Archivos procesados: {len(results)}")
        print(f"   Total de chunks: {total_chunks}")
        print("=" * 60 + "\n")
    else:
        result = indexer.index_new()


if __name__ == "__main__":
    main()
