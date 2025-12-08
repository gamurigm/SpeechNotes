import os
import logging
from typing import List, Dict, Any, Optional

# Use the new SmolAgents-based RAG Agent
from src.agent.rag_agent import RagAgent

logger = logging.getLogger(__name__)

class RagService:
    """
    Service for RAG (Retrieval Augmented Generation) operations.
    Uses SmolAgents and ChromaDB.
    """
    
    def __init__(self):
        try:
            self.agent = RagAgent()
            logger.info("RagAgent initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize RagAgent: {e}")
            self.agent = None

    def chat(self, query: str) -> Dict[str, Any]:
        """
        Answer a query using the RAG Agent.
        """
        if not self.agent:
            return {
                "answer": "El servicio de chat no está disponible en este momento.",
                "sources": []
            }
            
        answer = self.agent.chat(query)
        
        # SmolAgents currently returns a string. 
        # Source tracking would require parsing the agent's steps or modifying the tool to return structured data.
        # For now, we return empty sources or could try to extract them from the answer if formatted.
        
        return {
            "answer": answer,
            "sources": [] # TODO: Extract sources from agent execution logs if possible
        }
    
    async def chat_stream(self, query: str):
        """
        Answer a query using RAG with streaming response.
        """
        if not self.agent:
            yield "El servicio de chat no está disponible en este momento."
            return
            
        # The agent's chat_stream currently yields the full response
        for chunk in self.agent.chat_stream(query):
            yield chunk
