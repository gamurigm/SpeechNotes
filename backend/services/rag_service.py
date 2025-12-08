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
        try:
            logger.debug("RagService.chat called with query: %s", query)
            answer = self.agent.chat(query)
            logger.debug("RagService.chat got answer (len=%d)", len(str(answer)))

            # SmolAgents currently returns a string.
            return {
                "answer": answer,
                "sources": []  # TODO: Extract sources from agent execution logs if possible
            }
        except Exception as e:
            # Log full exception with traceback for easier debugging
            logger.exception("Exception in RagService.chat for query: %s", query)
            return {
                "answer": f"Error generating response: {str(e)}",
                "sources": []
            }
    
    async def chat_stream(self, query: str):
        """
        Answer a query using RAG with streaming response.
        """
        if not self.agent:
            yield "El servicio de chat no está disponible en este momento."
            return
        try:
            logger.debug("RagService.chat_stream called with query: %s", query)
            for chunk in self.agent.chat_stream(query):
                yield chunk
        except Exception as e:
            logger.exception("Exception in RagService.chat_stream for query: %s", query)
            yield f"Error in stream: {str(e)}"

    def search_file(self, query: str, filename: str) -> Dict[str, Any]:
        """
        Search the knowledge base but restrict results to a specific filename.
        Returns a small dict with 'context' that can be used to prompt the LLM.
        """
        if not self.agent:
            return {"context": None, "error": "RAG agent not initialized"}
        try:
            logger.debug("RagService.search_file called with query=%s filename=%s", query, filename)
            context = self.agent.search_file_context(query, filename)
            return {"context": context}
        except Exception as e:
            logger.exception("Exception in RagService.search_file for query=%s file=%s", query, filename)
            return {"context": None, "error": str(e)}
