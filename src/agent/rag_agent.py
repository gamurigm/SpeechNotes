"""RAG Agent Module using NVIDIA NIM (OpenAI-compatible API)."""

import os
from typing import List
from dotenv import load_dotenv
from smolagents import ToolCallingAgent, tool
from langchain_chroma import Chroma
from openai import OpenAI
from opentelemetry import trace

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
    db_dir = os.path.join(project_root, "knowledge_base", "chroma_db")

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
                return f"Contexto no disponible (embeddings no inicializados: {embeddings_error})"
            return "Contexto no disponible (vectordb no inicializado)"

        docs = vectordb.similarity_search(query, k=4)
        if not docs:
            return "No relevant documents found."

        context = "\n\n".join(
            f"[Source: {doc.metadata.get('source', 'Unknown')}]\n{doc.page_content}" 
            for doc in docs
        )
        return context
    except Exception as e:
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
                return f"Contexto no disponible (embeddings no inicializados: {embeddings_error})"
            return "Contexto no disponible (vectordb no inicializado)"

        # retrieve a larger set and then filter by filename
        docs = vectordb.similarity_search(query, k=k)
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
        return f"Error searching knowledge base by file: {str(e)}"

class RagAgent:
    def __init__(self):
        """Initialize RAG Agent and NVIDIA NIM client."""

        if not LLM_API_KEY:
            raise ValueError("NVIDIA_API_KEY is not set in environment variables")

        # OpenAI-compatible client for NVIDIA NIM
        self.client = OpenAI(
            base_url=NVIDIA_BASE_URL,
            api_key=LLM_API_KEY,
        )

        self.model_name = MODEL_NAME
        self.temperature = TEMPERATURE
        self.top_p = TOP_P
        self.max_tokens = MAX_TOKENS

        # SmolAgents ToolCallingAgent will orchestrate calls to tools and LLM
        # We'll provide a simple wrapper that calls the NVIDIA client when needed.
        self.agent = ToolCallingAgent(
            tools=[search_knowledge_base],
            model=None,
            max_steps=3,
        )

    def _call_llm(self, prompt: str) -> str:
        """Call NVIDIA NIM DeepSeek model with the given prompt."""
        with _tracer.start_as_current_span("llm.call", attributes={"model": self.model_name}):
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                top_p=self.top_p,
                max_tokens=self.max_tokens,
                stream=False,
            )

        return completion.choices[0].message.content

    def chat(self, user_query: str) -> str:
        """Run the agent with a user query using NVIDIA NIM."""
        try:
            # For ahora usamos el LLM directamente con la KB como contexto.
            context = search_knowledge_base(user_query)
            prompt = (
                "Usa el siguiente contexto para responder la pregunta del usuario. "
                "Si el contexto no contiene la respuesta, dilo explícitamente.\n\n"
                f"Contexto:\n{context}\n\n"
                f"Pregunta del usuario: {user_query}"
            )
            answer = self._call_llm(prompt)
            return answer
        except Exception as e:
            return f"Error generating response: {str(e)}"

    def search_file_context(self, query: str, filename: str, k: int = 50) -> str:
        """Return contextual passages from the vector store filtered by `filename`."""
        return search_knowledge_base_by_file(query, filename, k=k)

    def chat_stream(self, user_query: str):
        """
        Stream the agent's response using NVIDIA NIM streaming API.
        """
        try:
            context = search_knowledge_base(user_query)
            prompt = (
                "Usa el siguiente contexto para responder la pregunta del usuario. "
                "Si el contexto no contiene la respuesta, dilo explícitamente.\n\n"
                f"Contexto:\n{context}\n\n"
                f"Pregunta del usuario: {user_query}"
            )

            # Stream LLM response and create a span for streaming
            with _tracer.start_as_current_span("llm.stream", attributes={"model": self.model_name}):
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=self.temperature,
                    top_p=self.top_p,
                    max_tokens=self.max_tokens,
                    stream=True,
                )

                for chunk in stream:
                    if not chunk.choices:
                        continue
                    delta = chunk.choices[0].delta
                    if delta and getattr(delta, "content", None):
                        yield delta.content
        except Exception as e:
            yield f"Error generating streamed response: {str(e)}"
