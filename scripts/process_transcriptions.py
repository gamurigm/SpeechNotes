"""
Transcription Processing Pipeline
Orchestrates the ingestion, analysis, and generation of transcriptions using MongoDB.
"""

import sys
import os
import argparse
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agent.transcription_ingestor import TranscriptionIngestor
from src.agent.transcription_analyzer import TranscriptionAnalyzer
from src.agent.document_generator import DocumentGenerator
from src.agent.transcription_embedder import TranscriptionEmbedder


def main():
    parser = argparse.ArgumentParser(description="Transcription Processing Pipeline (MongoDB)")
    
    parser.add_argument('--ingest', action='store_true', help='Ingest new files to MongoDB')
    parser.add_argument('--analyze', action='store_true', help='Analyze pending transcriptions with LLM')
    parser.add_argument('--generate', action='store_true', help='Generate markdown documents from MongoDB')
    parser.add_argument('--embed', action='store_true', help='Generate embeddings and store in ChromaDB')
    parser.add_argument('--pipeline', action='store_true', help='Run full pipeline (Ingest -> Analyze -> Generate -> Embed)')
    
    args = parser.parse_args()
    
    if not (args.ingest or args.analyze or args.generate or args.embed or args.pipeline):
        parser.print_help()
        return

    # 1. Ingestion
    if args.ingest or args.pipeline:
        print("\n" + "="*50)
        print("STAGE 1: INGESTION")
        print("="*50)
        ingestor = TranscriptionIngestor()
        stats = ingestor.ingest_all()
        print(f"[RESULT] Added: {stats['added']}, Skipped: {stats['skipped']}, Errors: {stats['errors']}")
        
    # 2. Analysis
    if args.analyze or args.pipeline:
        print("\n" + "="*50)
        print("STAGE 2: ANALYSIS (LLM)")
        print("="*50)
        analyzer = TranscriptionAnalyzer()
        count = analyzer.analyze_pending()
        print(f"[RESULT] Analyzed {count} transcriptions")
        
    # 3. Generation
    if args.generate or args.pipeline:
        print("\n" + "="*50)
        print("STAGE 3: GENERATION")
        print("="*50)
        generator = DocumentGenerator()
        count = generator.generate_all()
        print(f"[RESULT] Generated {count} documents")

    # 4. Embedding
    if args.embed or args.pipeline:
        print("\n" + "="*50)
        print("STAGE 4: EMBEDDING")
        print("="*50)
        embedder = TranscriptionEmbedder()
        count = embedder.embed_pending()
        print(f"[RESULT] Embedded {count} segments")
        
    print("\n[DONE] Pipeline execution finished.")

if __name__ == "__main__":
    main()
