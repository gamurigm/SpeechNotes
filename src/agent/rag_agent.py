"""RAG Agent Module using NVIDIA NIM (OpenAI-compatible API)."""

import os
from typing import List
from dotenv import load_dotenv
from smolagents import ToolCallingAgent, tool
from langchain_chroma import Chroma
from openai import OpenAI
from opentelemetry import trace
import logging

logger = logging.getLogger(__name__)

_tracer = trace.get_tracer(__name__)

# Load environment variables
load_dotenv()

# Optional kill-switch to avoid embeddings DB usage in restricted networks
DISABLE_RAG = os.getenv("DISABLE_RAG", "0") == "1"

# NVIDIA configuration from .env
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "deepseek-ai/deepseek-v3.1-terminus")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nvidia/nv-embedqa-e5-v5")
LLM_API_KEY = os.getenv("NVIDIA_API_KEY")
EMBED_API_KEY = os.getenv("NVIDIA_EMBEDDING_API_KEY") or LLM_API_KEY

TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))
TOP_P = float(os.getenv("TOP_P", 0.7))
MAX_TOKENS = int(os.getenv("MAX_TOKENS", 8192))


class NvidiaEmbeddings:
    """Minimal embedding wrapper calling NVIDIA NIM via OpenAI-compatible API."""

    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url)

    def embed_documents(self, texts: List[str]):
        resp = self.client.embeddings.create(
            model=self.model,
            input=texts,
            encoding_format="float",
            extra_body={"input_type": "passage", "truncate": "NONE"},
        )
        return [item.embedding for item in resp.data]

    def embed_query(self, text: str):
        resp = self.client.embeddings.create(
            model=self.model,
            input=[text],
            encoding_format="float",
            extra_body={"input_type": "query", "truncate": "NONE"},
        )
        return resp.data[0].embedding


# Initialize embeddings (must match ingestion) with graceful fallback if embedding service fails
try:
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
    db_dir = os.path.join(project_root, "knowledge_base", "chroma_db_new")

    if DISABLE_RAG:
        vectordb = None
        embeddings_error = "RAG deshabilitado por DISABLE_RAG"
    elif not EMBED_API_KEY:
        vectordb = None
        embeddings_error = "NVIDIA_EMBEDDING_API_KEY no definido"
    else:
        embeddings = NvidiaEmbeddings(
            model=EMBEDDING_MODEL,
            api_key=EMBED_API_KEY,
            base_url=NVIDIA_BASE_URL,
        )

        # Initialize Vector Store (assumes DB already created by the ingestion script)
        vectordb = Chroma(
            persist_directory=db_dir,
            embedding_function=embeddings
        )
        embeddings_error = None
except Exception as e:
    vectordb = None
    embeddings_error = str(e)
    logger.exception("Failed to initialize embeddings/vectordb: %s", embeddings_error)

if vectordb is None:
    logger.warning("Vector DB not initialized: %s", embeddings_error)
else:
    logger.info("Vector DB initialized at %s", db_dir)

@tool
def search_knowledge_base(query: str) -> str:
    """
    Searches the knowledge base for relevant documents to answer the user's query.
    Use this tool when the user asks questions about class transcriptions, notes, or project documentation.
    
    Args:
        query: The search query string.
    """
    try:
        if not vectordb:
            if embeddings_error:
                logger.debug("search_knowledge_base: embeddings_error=%s", embeddings_error)
                return f"Contexto no disponible (embeddings no inicializados: {embeddings_error})"
            logger.debug("search_knowledge_base: vectordb is None and no embeddings_error")
            return "Contexto no disponible (vectordb no inicializado)"

        docs = vectordb.similarity_search(query, k=4)
        logger.debug("search_knowledge_base: similarity_search returned %s docs", len(docs) if docs else 0)
        if not docs:
            return "No relevant documents found."

        context = "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" 
            for doc in docs
        )
        return context
    except Exception as e:
        logger.exception("Error searching knowledge base: %s", str(e))
        return f"Error searching knowledge base: {str(e)}"


def search_knowledge_base_by_file(query: str, filename: str, k: int = 50) -> str:
    """
    Search the knowledge base for results that originate from a specific filename.
    This is done by performing a similarity search and then filtering results by
    the `filename` stored in each document's metadata.

    Args:
        query: search query
        filename: filename to filter results by (exact match)
        k: number of candidates to retrieve from the vector store before filtering
    """
    try:
        if not vectordb:
            if embeddings_error:
                logger.debug("search_by_file: embeddings_error=%s", embeddings_error)
                return f"Contexto no disponible (embeddings no inicializados: {embeddings_error})"
            return "Contexto no disponible (vectordb no inicializado)"

        # retrieve a larger set and then filter by filename
        docs = vectordb.similarity_search(query, k=k)
        logger.debug("search_knowledge_base_by_file: similarity_search returned %s docs before filtering", len(docs) if docs else 0)
        if not docs:
            return "No relevant documents found."

        # filter
        filtered = [doc for doc in docs if doc.metadata.get('filename') == filename]
        if not filtered:
            return f"No documents found for file '{filename}'."

        context = "\n\n".join(
            f"[Source: {doc.metadata.get('source','Unknown')} | file: {doc.metadata.get('filename')} ]\n{doc.page_content}"
            for doc in filtered
        )
        return context
    except Exception as e:
        logger.exception("Error searching knowledge base by file: %s", str(e))
        return f"Error searching knowledge base by file: {str(e)}"

class RagAgent:
    def __init__(self):
        """Initialize RagAgent with NVIDIA NIM client for Kimi K2."""
        if not LLM_API_KEY:
            logger.error("NVIDIA_API_KEY is not set")
            raise ValueError("NVIDIA_API_KEY is not set")

        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=LLM_API_KEY,
        )
        self.model_name = MODEL_NAME
        self.temperature = 1.0 # Kimi K2 prefiere temp 1 según tu ejemplo
        self.top_p = 0.9
        self.max_tokens = 16384

        # Path to transcriptions
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
        self.notes_dir = os.path.join(project_root, "notas")

        logger.info("RagAgent: initialized with model=%s", self.model_name)

    def _get_context_text(self, active_file: Optional[str] = None) -> str:
        """Read only the active file with high precision, or the single most recent note."""
        context_parts = []
        if not os.path.exists(self.notes_dir):
            return "No se encontraron notas en el sistema."
        
        # 1. Búsqueda inteligente del archivo activo
        if active_file:
            # Limpiamos el nombre enviado por la UI (quitamos extensiones de audio y rutas)
            clean_name = active_file.replace('.wav', '').replace('.mp3', '').replace('.md', '').replace('transcription_', '')
            
            # Patrones de búsqueda en la carpeta notas/
            # Buscaremos cualquier archivo que CONTENGA el nombre base
            all_files = os.listdir(self.notes_dir)
            found_path = None
            found_name = None

            # Prioridad: 1. Formatted, 2. Transcription, 3. Cualquier match
            for filename in all_files:
                if not filename.endswith('.md'): continue
                
                if clean_name.lower() in filename.lower():
                    # Si encontramos una versión 'formatted', esa es la mejor
                    if '_formatted' in filename:
                        found_path = os.path.join(self.notes_dir, filename)
                        found_name = filename
                        break
                    # Si no, guardamos la primera que encontremos
                    if not found_path:
                        found_path = os.path.join(self.notes_dir, filename)
                        found_name = filename

            if found_path:
                try:
                    with open(found_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        context_parts.append(f"### [ESTÁS LEYENDO ESTA CLASE: {found_name}] ###\n{content}\n")
                        logger.info(f"RagAgent: Contexto único cargado: {found_name}")
                except Exception as e:
                    logger.error(f"Error leyendo {found_name}: {e}")

        # 2. Si no hay archivo activo o no se encontró, cargamos ÚNICAMENTE la nota más reciente del sistema
        if not context_parts:
            files = [f for f in os.listdir(self.notes_dir) if f.endswith(".md")]
            if files:
                files.sort(key=lambda x: os.path.getmtime(os.path.join(self.notes_dir, x)), reverse=True)
                latest = files[0]
                try:
                    with open(os.path.join(self.notes_dir, latest), "r", encoding="utf-8") as f:
                        content = f.read()
                        context_parts.append(f"### [CLASE RECIENTE (Auto-seleccionada): {latest}] ###\n{content}")
                except Exception as e:
                    logger.error(f"Error leyendo nota reciente {latest}: {e}")

        return "\n\n".join(context_parts)

    def chat(self, user_query: str) -> str:
        """Direct chat using only active context."""
        try:
            context = self._get_context_text()
            prompt = (
                "Utiliza el siguiente contexto para responder. Si no hay información, dilo.\n\n"
                f"CONTEXTO:\n{context}\n\n"
                f"PREGUNTA: {user_query}"
            )
            
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                top_p=0.9,
                max_tokens=self.max_tokens,
                stream=False
            )
            return completion.choices[0].message.content
        except Exception as e:
            logger.exception("Error in RagAgent.chat")
            return f"Error: {e}"

    def chat_stream(self, user_query: str, active_file: Optional[str] = None):
        """Stream response focusing EXCLUSIVELY on the active file."""
        try:
            context = self._get_context_text(active_file=active_file)
            
            # Sistema de instrucciones ultra-enfocado
            sys_prompt = (
                "Eres Kimi, un asistente experto en analizar clases. "
                "TU REGLA PRINCIPAL: Responde únicamente basándote en el texto de la [CLASE ACTUAL]. "
                "No menciones otros documentos a menos que te lo pregunten.\n\n"
                "Al iniciar, confirma qué clase estás leyendo (ej: 'Analizando la clase de [Nombre]...')."
            )

            prompt = (
                f"TEXTO DE LA CLASE:\n{context}\n\n"
                f"PREGUNTA DEL USUARIO: {user_query}"
            )

            stream = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=1.0,
                top_p=0.9,
                max_tokens=self.max_tokens,
                stream=True
            )

            for chunk in stream:
                if not chunk.choices: continue
                delta = chunk.choices[0].delta
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield reasoning
                if delta.content:
                    yield delta.content
                    
        except Exception as e:
            logger.exception("Error in chat_stream")
            yield f"\n\nError: No se pudo cargar el archivo o conectar con la IA ({e})"
