"""
Vector Store for Semantic Search
Uses FAISS and NVIDIA Embedding API for high-quality embeddings.
"""

import os
import numpy as np
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

try:
    import faiss
except ImportError:
    raise ImportError("faiss-cpu is required. Install with: pip install faiss-cpu")

# Load environment variables
load_dotenv()


class VectorStore:
    """
    Vector store for semantic search using FAISS and NVIDIA embeddings.
    """
    
    def __init__(self, embedding_model: str = "nvidia/nv-embedqa-e5-v5"):
        """
        Initialize the vector store.
        
        Args:
            embedding_model: NVIDIA embedding model to use
        """
        self.embedding_model = embedding_model
        self.api_key = os.getenv("NVIDIA_EMBEDDING_API_KEY")
        self.base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        
        if not self.api_key:
            print("WARNING: NVIDIA_EMBEDDING_API_KEY not found. Vector store will be inactive.")
            self.client = None
        else:
            # Initialize OpenAI client for embeddings
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
        
        # Storage
        self.documents: List[str] = []
        self.metadata: List[Dict[str, Any]] = []
        self.index: Optional[faiss.Index] = None
        self.dimension: Optional[int] = None
    
    def _get_embedding(self, text: str, input_type: str = "query") -> np.ndarray:
        """
        Get embedding for a text using NVIDIA API.
        
        Args:
            text: Text to embed
            input_type: Type of input - "query" for search queries, "passage" for documents
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float",
                extra_body={"input_type": input_type, "truncate": "END"}
            )
            
            embedding = np.array(response.data[0].embedding, dtype=np.float32)
            return embedding
        
        except Exception as e:
            raise RuntimeError(f"Error getting embedding from NVIDIA API: {str(e)}")
    
    def add_documents(
        self,
        documents: List[str],
        metadata: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            documents: List of document texts
            metadata: Optional metadata for each document
        """
        if not documents:
            return
        
        # Prepare metadata
        if metadata is None:
            metadata = [{"index": i} for i in range(len(documents))]
        elif len(metadata) != len(documents):
            raise ValueError("Metadata length must match documents length")
        
        # Get embeddings
        embeddings = []
        for doc in documents:
            emb = self._get_embedding(doc, input_type="passage")
            embeddings.append(emb)
        
        embeddings_array = np.array(embeddings, dtype=np.float32)
        
        # Initialize or update FAISS index
        if self.index is None:
            self.dimension = embeddings_array.shape[1]
            self.index = faiss.IndexFlatL2(self.dimension)
        
        # Add to index
        self.index.add(embeddings_array)
        
        # Store documents and metadata
        self.documents.extend(documents)
        self.metadata.extend(metadata)
    
    def search(
        self,
        query: str,
        k: int = 5,
        score_threshold: Optional[float] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar documents.
        
        Args:
            query: Search query
            k: Number of results to return
            score_threshold: Optional minimum similarity score
            
        Returns:
            List of search results with document, metadata, and score
        """
        if self.index is None or len(self.documents) == 0:
            return []
        
        # Get query embedding
        query_embedding = self._get_embedding(query, input_type="query")
        query_vector = np.array([query_embedding], dtype=np.float32)
        
        # Search
        k = min(k, len(self.documents))
        distances, indices = self.index.search(query_vector, k)
        
        # Prepare results
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            # Convert L2 distance to similarity score (inverse)
            # Lower distance = higher similarity
            score = 1.0 / (1.0 + float(dist))
            
            if score_threshold is not None and score < score_threshold:
                continue
            
            results.append({
                "document": self.documents[idx],
                "metadata": self.metadata[idx],
                "score": score,
                "rank": i + 1
            })
        
        return results
    
    def clear(self) -> None:
        """Clear all documents and reset the index."""
        self.documents = []
        self.metadata = []
        self.index = None
        self.dimension = None
    
    def __len__(self) -> int:
        """Return the number of documents in the store."""
        return len(self.documents)
