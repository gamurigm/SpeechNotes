"""
Transcription Indexer Module
Automatically indexes transcriptions into the vector store.
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from .transcription_loader import TranscriptionLoader
from .vector_store import VectorStore


class TranscriptionIndexer:
    """
    Indexes transcriptions into the vector store for semantic search.
    """
    
    def __init__(
        self,
        vector_store: VectorStore,
        source_dir: str = "notas",
        processed_dir: str = "knowledge_base/transcriptions"
    ):
        """
        Initialize the transcription indexer.
        
        Args:
            vector_store: VectorStore instance to index into
            source_dir: Directory containing original transcriptions
            processed_dir: Directory for processed transcriptions
        """
        self.vector_store = vector_store
        self.loader = TranscriptionLoader(source_dir, processed_dir)
        self.metadata_file = Path(processed_dir) / "index_metadata.json"
        
        # Load existing metadata
        self.index_metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict[str, Any]:
        """Load index metadata from file."""
        if self.metadata_file.exists():
            try:
                return json.loads(self.metadata_file.read_text())
            except Exception:
                return {"indexed_files": {}, "last_update": None}
        return {"indexed_files": {}, "last_update": None}
    
    def _save_metadata(self):
        """Save index metadata to file."""
        self.metadata_file.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_file.write_text(
            json.dumps(self.index_metadata, indent=2),
            encoding='utf-8'
        )
    
    def check_updates(self) -> List[Path]:
        """
        Check for new or updated transcriptions.
        
        Returns:
            List of files that need to be indexed
        """
        all_files = self.loader.load_from_directory()
        files_to_index = []
        
        for file_path in all_files:
            file_key = file_path.name
            file_mtime = file_path.stat().st_mtime
            
            # Check if file is new or modified
            if file_key not in self.index_metadata["indexed_files"]:
                files_to_index.append(file_path)
            elif self.index_metadata["indexed_files"][file_key]["mtime"] < file_mtime:
                files_to_index.append(file_path)
        
        return files_to_index
    
    def index_transcription(self, file_path: Path) -> Dict[str, Any]:
        """
        Index a single transcription file.
        
        Args:
            file_path: Path to transcription file
            
        Returns:
            Indexing result with statistics
        """
        # Process transcription
        processed_path, metadata = self.loader.process_transcription(file_path)
        
        # Read processed content
        content = processed_path.read_text(encoding='utf-8')
        
        # Split into chunks for indexing
        chunks = self._create_chunks(content, metadata)
        
        # Prepare documents and metadata for vector store
        documents = [chunk["content"] for chunk in chunks]
        chunk_metadata = [chunk["metadata"] for chunk in chunks]
        
        # Add to vector store
        print(f"   [INFO] Indexando {len(chunks)} chunks...")
        self.vector_store.add_documents(documents, chunk_metadata)
        
        # Update index metadata
        self.index_metadata["indexed_files"][file_path.name] = {
            "processed_file": str(processed_path),
            "mtime": file_path.stat().st_mtime,
            "indexed_at": datetime.now().isoformat(),
            "chunks": len(chunks),
            "metadata": metadata
        }
        self.index_metadata["last_update"] = datetime.now().isoformat()
        self._save_metadata()
        
        return {
            "file": file_path.name,
            "chunks": len(chunks),
            "processed_file": processed_path
        }
    
    def _create_chunks(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Create chunks from processed markdown content.
        
        Args:
            content: Processed markdown content
            metadata: File metadata
            chunk_size: Target words per chunk
            
        Returns:
            List of chunks with content and metadata
        """
        chunks = []
        
        # Split by topic sections (## Tema X:)
        import re
        sections = re.split(r'(## Tema \d+:.*?)(?=## Tema \d+:|## 🏷️ Metadata|$)', content, flags=re.DOTALL)
        
        for i, section in enumerate(sections):
            if not section.strip() or section.startswith('---') or section.startswith('# Transcripción'):
                continue
            
            # Extract topic title if present
            title_match = re.search(r'## Tema \d+: (.+)', section)
            topic_title = title_match.group(1) if title_match else f"Sección {i}"
            
            # Extract timestamp if present
            timestamp_match = re.search(r'\*\*⏱️ Timestamp\*\*: (\d{2}:\d{2}:\d{2})', section)
            timestamp = timestamp_match.group(1) if timestamp_match else metadata.get("time", "00:00:00")
            
            # Clean content (remove markdown headers for cleaner indexing)
            clean_content = re.sub(r'##+ ', '', section)
            clean_content = re.sub(r'\*\*⏱️ Timestamp\*\*:.*?\n', '', clean_content)
            clean_content = clean_content.strip()
            
            if not clean_content:
                continue
            
            # Split long sections into smaller chunks
            words = clean_content.split()
            if len(words) > chunk_size:
                # Split into multiple chunks
                for j in range(0, len(words), chunk_size):
                    chunk_words = words[j:j + chunk_size]
                    chunk_content = ' '.join(chunk_words)
                    
                    chunks.append({
                        "content": chunk_content,
                        "metadata": {
                            "source": "transcription",
                            "filename": metadata["filename"],
                            "date": metadata["date"],
                            "topic": topic_title,
                            "timestamp": timestamp,
                            "chunk_id": len(chunks) + 1,
                            "word_count": len(chunk_words)
                        }
                    })
            else:
                # Single chunk for this section
                chunks.append({
                    "content": clean_content,
                    "metadata": {
                        "source": "transcription",
                        "filename": metadata["filename"],
                        "date": metadata["date"],
                        "topic": topic_title,
                        "timestamp": timestamp,
                        "chunk_id": len(chunks) + 1,
                        "word_count": len(words)
                    }
                })
        
        return chunks
    
    def index_all(self) -> Dict[str, Any]:
        """
        Index all transcriptions from source directory.
        
        Returns:
            Summary of indexing operation
        """
        print("\n" + "=" * 60)
        print("INDEXANDO TODAS LAS TRANSCRIPCIONES")
        print("=" * 60 + "\n")
        
        files = self.loader.load_from_directory()
        
        if not files:
            print("[WARN] No se encontraron archivos de transcripcion")
            return {"indexed": 0, "chunks": 0, "files": []}
        
        print(f"[INFO] Encontrados {len(files)} archivos de transcripcion\n")
        
        results = []
        total_chunks = 0
        
        for file_path in files:
            try:
                result = self.index_transcription(file_path)
                results.append(result)
                total_chunks += result["chunks"]
                print()
            except Exception as e:
                print(f"[ERROR] Error procesando {file_path.name}: {e}\n")
        
        print("=" * 60)
        print(f"[OK] Indexacion completa:")
        print(f"   Archivos procesados: {len(results)}")
        print(f"   Total de chunks: {total_chunks}")
        print(f"   Documentos en vector store: {len(self.vector_store)}")
        print("=" * 60 + "\n")
        
        return {
            "indexed": len(results),
            "chunks": total_chunks,
            "files": results
        }
    
    def index_new(self) -> Dict[str, Any]:
        """
        Index only new or updated transcriptions.
        
        Returns:
            Summary of indexing operation
        """
        print("\n" + "=" * 60)
        print("INDEXANDO TRANSCRIPCIONES NUEVAS/ACTUALIZADAS")
        print("=" * 60 + "\n")
        
        files_to_index = self.check_updates()
        
        if not files_to_index:
            print("[INFO] No hay archivos nuevos para indexar")
            print("=" * 60 + "\n")
            return {"indexed": 0, "chunks": 0, "files": []}
        
        print(f"[INFO] Encontrados {len(files_to_index)} archivos para indexar\n")
        
        results = []
        total_chunks = 0
        
        for file_path in files_to_index:
            try:
                result = self.index_transcription(file_path)
                results.append(result)
                total_chunks += result["chunks"]
                print()
            except Exception as e:
                print(f"[ERROR] Error procesando {file_path.name}: {e}\n")
        
        print("=" * 60)
        print(f"[OK] Indexacion completa:")
        print(f"   Archivos procesados: {len(results)}")
        print(f"   Total de chunks: {total_chunks}")
        print(f"   Documentos en vector store: {len(self.vector_store)}")
        print("=" * 60 + "\n")
        
        return {
            "indexed": len(results),
            "chunks": total_chunks,
            "files": results
        }
    
    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        Get list of indexed files with metadata.
        
        Returns:
            List of indexed file information
        """
        files = []
        for filename, info in self.index_metadata["indexed_files"].items():
            files.append({
                "filename": filename,
                "date": info["metadata"]["date"],
                "chunks": info["chunks"],
                "indexed_at": info["indexed_at"],
                "processed_file": info["processed_file"]
            })
        
        # Sort by date (most recent first)
        files.sort(key=lambda x: x["date"], reverse=True)
        
        return files
