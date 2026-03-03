"""
NVIDIA Embedding Client
Singleton wrapper for NVIDIA's Embedding API.
"""

import os
from typing import List, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
from src.database.config_service import ConfigService


class EmbeddingClient:
    """
    Singleton client for NVIDIA Embedding API.
    """
    
    _instance: Optional['EmbeddingClient'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'EmbeddingClient':
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the Embedding client (only once)."""
        if not self._initialized:
            _cfg = ConfigService()
            self.api_key = _cfg.get("NVIDIA_EMBEDDING_API_KEY") or _cfg.get("NVIDIA_API_KEY")
            self.base_url = _cfg.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            self.model_name = "nvidia/llama-3.2-nemoretriever-300m-embed-v2"
            
            if not self.api_key:
                raise ValueError("NVIDIA_EMBEDDING_API_KEY or NVIDIA_API_KEY not found in environment variables")
            
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            EmbeddingClient._initialized = True
    
    def get_embedding(self, text: str, input_type: str = "query") -> List[float]:
        """
        Generate embedding for a single text string.
        
        Args:
            text: The text to embed.
            input_type: 'query' or 'passage'. Default is 'query'.
            
        Returns:
            List of floats representing the embedding.
        """
        return self.get_embeddings([text], input_type)[0]

    def get_embeddings(self, texts: List[str], input_type: str = "query") -> List[List[float]]:
        """
        Generate embeddings for a list of texts.
        
        Args:
            texts: List of strings to embed.
            input_type: 'query' or 'passage'. Default is 'query'.
            
        Returns:
            List of embeddings (lists of floats).
        """
        try:
            # Truncate texts if they are too long (simple check, API handles truncation usually)
            # But we pass truncate="NONE" as per user request, so we rely on the model/API.
            
            response = self.client.embeddings.create(
                input=texts,
                model=self.model_name,
                encoding_format="float",
                extra_body={"input_type": input_type, "truncate": "NONE"}
            )
            
            return [data.embedding for data in response.data]
            
        except Exception as e:
            print(f"[ERROR] Failed to generate embeddings: {e}")
            raise
