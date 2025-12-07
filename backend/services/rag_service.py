import os
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np
from openai import OpenAI

from src.database.vector_store import VectorStore
from src.database.mongo_manager import MongoManager
from src.llm.nvidia_client import NvidiaInferenceClient

logger = logging.getLogger(__name__)

class RagService:
    """
    Service for RAG (Retrieval Augmented Generation) operations.
    Handles indexing from MongoDB to ChromaDB and chat queries.
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        self.mongo_manager = MongoManager()
        self.llm_client = NvidiaInferenceClient()
        
        # Initialize embedding client (using NVIDIA API via OpenAI client)
        self.embedding_api_key = os.getenv("NVIDIA_EMBEDDING_API_KEY")
        self.embedding_base_url = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
        self.embedding_model = "nvidia/nv-embedqa-e5-v5"
        
        if not self.embedding_api_key:
            logger.warning("NVIDIA_EMBEDDING_API_KEY not found. RAG features may fail.")
            
        self.embedding_client = OpenAI(
            base_url=self.embedding_base_url,
            api_key=self.embedding_api_key
        )

    def _get_embedding(self, text: str, input_type: str = "query") -> List[float]:
        """Generate embedding for text using NVIDIA API."""
        try:
            response = self.embedding_client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float",
                extra_body={"input_type": input_type, "truncate": "END"}
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def index_documents_from_mongo(self):
        """
        Fetch processed transcriptions from MongoDB and index them in ChromaDB.
        Only indexes documents that are not already in the vector store.
        """
        try:
            # Get processed transcriptions
            transcriptions_coll = self.mongo_manager.get_collection("transcriptions")
            docs = list(transcriptions_coll.find({"processed": True}))
            
            if not docs:
                logger.info("No processed transcriptions found in MongoDB.")
                return 0

            # Check existing IDs in ChromaDB
            # ChromaDB collection.get() returns dict with 'ids'
            existing = self.vector_store.collection.get()
            existing_ids = set(existing['ids']) if existing and 'ids' in existing else set()
            
            new_docs = []
            new_ids = []
            new_embeddings = []
            new_metadatas = []
            
            for doc in docs:
                doc_id = str(doc["_id"])
                if doc_id in existing_ids:
                    continue
                
                # Prepare content for embedding
                # We might want to fetch the full markdown content if stored, 
                # or construct it from segments.
                # For now, let's assume 'summary' or 'content' field exists, 
                # or we use the filename and some metadata.
                # Based on regenerate_from_mongo.py, it seems we might need to reconstruct 
                # or check if there is a 'markdown_content' field.
                
                # Let's check if 'markdown_content' exists in the doc, otherwise use filename + summary
                content = doc.get("markdown_content", "")
                if not content:
                    # Fallback: try to fetch segments
                    segments_coll = self.mongo_manager.get_collection("segments")
                    segments = list(segments_coll.find({"transcription_id": doc["_id"]}).sort("sequence", 1))
                    content = "\n".join([s.get("text", "") for s in segments])
                
                if not content:
                    logger.warning(f"Skipping doc {doc_id}: No content found.")
                    continue
                
                # Generate embedding
                try:
                    embedding = self._get_embedding(content, input_type="passage")
                except Exception as e:
                    logger.error(f"Failed to embed doc {doc_id}: {e}")
                    continue
                
                # Prepare metadata
                metadata = {
                    "filename": doc.get("filename", "unknown"),
                    "created_at": doc.get("created_at", datetime.now()).isoformat(),
                    "duration": doc.get("duration", 0),
                    "source": "mongodb"
                }
                
                new_ids.append(doc_id)
                new_docs.append(content)
                new_embeddings.append(embedding)
                new_metadatas.append(metadata)
            
            # Add to ChromaDB
            if new_ids:
                self.vector_store.add_documents(
                    ids=new_ids,
                    documents=new_docs,
                    embeddings=new_embeddings,
                    metadatas=new_metadatas
                )
                logger.info(f"Indexed {len(new_ids)} new documents.")
                return len(new_ids)
            else:
                logger.info("No new documents to index.")
                return 0
                
        except Exception as e:
            logger.error(f"Error indexing documents: {e}")
            raise

    def _prepare_context_and_sources(self, query: str, k: int = 3):
        """Prepare context and sources for RAG."""
        # 1. Generate query embedding
        query_embedding = self._get_embedding(query, input_type="query")
        
        # 2. Search Vector Store
        results = self.vector_store.query_similar(
            query_embedding=query_embedding,
            n_results=k
        )
        
        # 3. Construct Context
        context_parts = []
        sources = []
        
        if results and results['documents']:
            for i, doc_text in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i]
                
                # Format date nicely
                created_at = meta.get('created_at', 'Fecha desconocida')
                if created_at != 'Fecha desconocida':
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        fecha_formateada = dt.strftime("%d de %B de %Y, %H:%M:%S")
                    except:
                        fecha_formateada = created_at
                else:
                    fecha_formateada = created_at
                
                filename = meta.get('filename', 'Sin nombre')
                duration = meta.get('duration', 0)
                
                source_info = (
                    f"📄 Documento: {filename}\n"
                    f"📅 Fecha de creación: {fecha_formateada}\n"
                    f"⏱️ Duración: {duration:.1f}s"
                )
                
                context_parts.append(f"{source_info}\n\nContenido:\n{doc_text}")
                
                # Add to sources for response
                sources.append({
                    **meta,
                    'fecha_formateada': fecha_formateada
                })
        
        context = "\n\n---\n\n".join(context_parts)
        
        return context, sources

    def chat(self, query: str, k: int = 3) -> Dict[str, Any]:
        """
        Answer a query using RAG.
        """
        context, sources = self._prepare_context_and_sources(query, k)
        
        if not context:
            return {
                "answer": "No encontré información relevante en los documentos para responder tu pregunta.",
                "sources": []
            }
            
        # Generate Answer with LLM
        system_prompt = (
            "Eres un asistente inteligente especializado en responder preguntas sobre transcripciones de clases y documentos educativos.\n\n"
            "INSTRUCCIONES:\n"
            "- Responde en español de manera clara y concisa\n"
            "- Usa la información del contexto proporcionado\n"
            "- Cuando te pregunten CUÁNDO se generó/grabó un documento o clase, usa la 'Fecha de creación' del contexto\n"
            "- Menciona el nombre del archivo cuando sea relevante\n"
            "- Si la información no está en el contexto, indícalo claramente\n"
            "- Sé preciso con fechas y horas cuando las menciones\n"
        )
        
        user_prompt = f"Contexto de documentos:\n\n{context}\n\n---\n\nPregunta del usuario: {query}\n\nRespuesta:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        answer = self.llm_client.generate(prompt=user_prompt, messages=messages)
        
        return {
            "answer": answer,
            "sources": sources
        }
    
    async def chat_stream(self, query: str, k: int = 3):
        """
        Answer a query using RAG with streaming response.
        """
        context, sources = self._prepare_context_and_sources(query, k)
        
        if not context:
            yield "No encontré información relevante en los documentos para responder tu pregunta."
            return
            
        # Generate Answer with LLM (streaming)
        system_prompt = (
            "Eres un asistente inteligente especializado en responder preguntas sobre transcripciones de clases y documentos educativos.\n\n"
            "INSTRUCCIONES:\n"
            "- Responde en español de manera clara y concisa\n"
            "- Usa la información del contexto proporcionado\n"
            "- Cuando te pregunten CUÁNDO se generó/grabó un documento o clase, usa la 'Fecha de creación' del contexto\n"
            "- Menciona el nombre del archivo cuando sea relevante\n"
            "- Si la información no está en el contexto, indícalo claramente\n"
            "- Sé preciso con fechas y horas cuando las menciones\n"
        )
        
        user_prompt = f"Contexto de documentos:\n\n{context}\n\n---\n\nPregunta del usuario: {query}\n\nRespuesta:"
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        # Stream the response
        for chunk in self.llm_client.stream_generate(prompt=user_prompt, messages=messages):
            yield chunk
