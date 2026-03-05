"""
Transcription Embedder Module
Generates embeddings for transcription segments and stores them in ChromaDB.
"""

from typing import List, Dict, Any

from src.database import MongoManager
from src.database.vector_store import VectorStore
from src.llm.embedding_client import EmbeddingClient

class TranscriptionEmbedder:
    """
    Service to embed transcription segments.
    """
    
    def __init__(self):
        self.db = MongoManager()
        self.vector_store = VectorStore()
        self.embedding_client = EmbeddingClient()
        
    def embed_pending(self) -> int:
        """
        Process all segments that haven't been embedded yet.
        Returns number of segments processed.
        """
        # Find segments that are part of a processed transcription but not yet embedded
        # We can check 'embedded' flag on segments
        pending_segments = list(self.db.segments.find({
            "embedded": {"$ne": True},
            "topic_title": {"$ne": None} # Only embed segments that have been analyzed
        }))
        
        if not pending_segments:
            print("[INFO] No pending segments to embed.")
            return 0
            
        print(f"[INFO] Found {len(pending_segments)} segments to embed.")
        
        batch_size = 50
        count = 0
        
        for i in range(0, len(pending_segments), batch_size):
            batch = pending_segments[i:i+batch_size]
            self._process_batch(batch)
            count += len(batch)
            
        return count
        
    def _process_batch(self, batch: List[Dict[str, Any]]):
        """Process a batch of segments."""
        texts = []
        ids = []
        metadatas = []
        
        for seg in batch:
            # Prepare text content
            # We combine title and content for better context if available
            content = seg.get("content", "")
            topic = seg.get("topic_title", "General")
            text_to_embed = f"{topic}: {content}"
            
            texts.append(text_to_embed)
            ids.append(str(seg["_id"]))
            
            # Metadata for retrieval
            metadatas.append({
                "transcription_id": str(seg["transcription_id"]),
                "timestamp": seg["timestamp"],
                "topic": topic,
                "sequence": seg["sequence"]
            })
            
        try:
            # Generate embeddings
            embeddings = self.embedding_client.get_embeddings(texts, input_type="passage")
            
            # Store in ChromaDB
            self.vector_store.add_documents(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
            
            # Update MongoDB
            segment_ids = [seg["_id"] for seg in batch]
            self.db.segments.update_many(
                {"_id": {"$in": segment_ids}},
                {"$set": {"embedded": True}}
            )
            
        except Exception as e:
            print(f"[ERROR] Failed to process batch: {e}")
