"""
Vector Store Module
Manages vector embeddings using ChromaDB.
"""

import os
import chromadb
from typing import List, Dict, Any, Optional
from pathlib import Path

class VectorStore:
    """
    Manages ChromaDB for storing and querying embeddings.
    """
    
    def __init__(self, persist_directory: str = "knowledge_base/chroma_db"):
        self.persist_directory = persist_directory
        
        # Ensure directory exists
        Path(persist_directory).mkdir(parents=True, exist_ok=True)
        
        # Initialize Client
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name="transcriptions",
            metadata={"hnsw:space": "cosine"} # Cosine similarity
        )
        
    def add_documents(
        self,
        ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Add documents and their embeddings to the store.
        """
        if not ids:
            return
            
        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )
        print(f"[INFO] Added {len(ids)} documents to Vector Store.")
        
    def query_similar(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Query for similar documents using an embedding.
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where
        )
        return results

    def count(self) -> int:
        """Return total number of documents."""
        return self.collection.count()
