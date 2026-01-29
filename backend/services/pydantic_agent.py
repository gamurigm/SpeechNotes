"""
Pydantic AI Agent for Document-Aware Chat

This module implements a chat agent using Pydantic AI that:
1. Receives the active document context via dependency injection
2. Uses Logfire for observability
3. Responds based ONLY on the current document
"""

import os
import logging
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

# Configure Logfire BEFORE importing pydantic_ai instrumentation
load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Logfire if token is available
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")
if LOGFIRE_TOKEN:
    try:
        import logfire
        logfire.configure(
            token=LOGFIRE_TOKEN,
            service_name="speechnotes-chat",
            send_to_logfire=True
        )
        logfire.instrument_pydantic_ai()
        logger.info("Logfire configured successfully for Pydantic AI")
    except Exception as e:
        logger.warning(f"Failed to configure Logfire: {e}")
else:
    logger.info("Logfire token not found, running without observability")


# --- Models ---

class DocumentContext(BaseModel):
    """Context about the currently active document"""
    doc_id: str
    filename: Optional[str] = None
    title: Optional[str] = None
    content: str
    content_type: str  # 'formatted', 'raw', 'edited', 'segments'


@dataclass
class ChatDependencies:
    """Dependencies injected into the agent at runtime"""
    active_document: DocumentContext


class ChatResponse(BaseModel):
    """Structured response from the chat agent"""
    answer: str
    confidence: float = 1.0
    referenced_doc: Optional[str] = None


# --- Agent Configuration ---

# Get model configuration from environment
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "moonshotai/kimi-k2-thinking")

# System prompt that enforces document-focused responses
SYSTEM_PROMPT = """Eres Kimi, un asistente experto en analizar transcripciones de clases universitarias.

TU REGLA MÁS IMPORTANTE: Solo puedes responder basándote en el documento que te proporciono.

Cuando recibes una pregunta:
1. Analiza el contenido del documento activo que está en el contexto
2. Responde ÚNICAMENTE con información de ese documento
3. Si la información no está en el documento, dilo claramente
4. Nunca inventes información que no esté en el documento

Al inicio de tu respuesta, confirma brevemente qué documento estás analizando.
Ejemplo: "Analizando la clase de [título o fecha]..."

Responde en español de manera clara y estructurada."""


# Create the Pydantic AI Agent
# Note: We'll use OpenAI-compatible endpoint with NVIDIA NIM
def create_agent() -> Agent[ChatDependencies, str]:
    """Create and configure the Pydantic AI agent"""
    
    # For NVIDIA NIM, we use the openai model type with custom base URL
    # The model string format is: openai:<model_name>
    model_str = f"openai:{MODEL_NAME}"
    
    agent = Agent(
        model_str,
        deps_type=ChatDependencies,
        output_type=str,  # Simple string output for streaming
        system_prompt=SYSTEM_PROMPT,
    )
    
    # Add dynamic system prompt that includes document context
    @agent.system_prompt
    async def add_document_context(ctx: RunContext[ChatDependencies]) -> str:
        doc = ctx.deps.active_document
        return f"""
DOCUMENTO ACTIVO:
- ID: {doc.doc_id}
- Archivo: {doc.filename or 'Sin nombre'}
- Título: {doc.title or 'Sin título'}
- Tipo de contenido: {doc.content_type}

CONTENIDO DEL DOCUMENTO:
{doc.content}

---
Responde SOLO basándote en el contenido anterior.
"""
    
    return agent


# Singleton agent instance
_agent: Optional[Agent[ChatDependencies, str]] = None


def get_agent() -> Agent[ChatDependencies, str]:
    """Get or create the agent singleton"""
    global _agent
    if _agent is None:
        _agent = create_agent()
        logger.info(f"Pydantic AI Agent created with model: {MODEL_NAME}")
    return _agent


# --- Service Functions ---

async def chat_with_document(
    query: str,
    document: DocumentContext,
) -> str:
    """
    Send a query to the agent with document context.
    
    Args:
        query: User's question
        document: The active document context
        
    Returns:
        Agent's response as a string
    """
    agent = get_agent()
    deps = ChatDependencies(active_document=document)
    
    try:
        result = await agent.run(query, deps=deps)
        logger.info(f"Chat completed for doc {document.doc_id}, response length: {len(result.output)}")
        return result.output
    except Exception as e:
        logger.exception(f"Error in chat_with_document: {e}")
        raise


async def chat_stream_with_document(
    query: str,
    document: DocumentContext,
):
    """
    Stream a response from the agent with document context.
    
    Args:
        query: User's question
        document: The active document context
        
    Yields:
        Chunks of the agent's response
    """
    agent = get_agent()
    deps = ChatDependencies(active_document=document)
    
    try:
        async with agent.run_stream(query, deps=deps) as stream:
            async for chunk in stream.stream_text():
                yield chunk
                
        logger.info(f"Stream completed for doc {document.doc_id}")
    except Exception as e:
        logger.exception(f"Error in chat_stream_with_document: {e}")
        yield f"\n\nError: {str(e)}"


# --- Direct Kimi K2 API (Fallback) ---

from openai import AsyncOpenAI

# Try to get logfire for manual instrumentation
try:
    import logfire
    _logfire_available = LOGFIRE_TOKEN is not None
except ImportError:
    _logfire_available = False
    logfire = None

async def chat_stream_direct(
    query: str,
    document: DocumentContext,
    thinking: bool = True,
):
    """
    Direct streaming using OpenAI-compatible API.
    Fallback if Pydantic AI streaming has issues.
    """
    if not NVIDIA_API_KEY:
        yield "Error: NVIDIA_API_KEY not configured"
        return
    
    client = AsyncOpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=NVIDIA_API_KEY,
    )
    
    # Build the prompt with document context
    system_msg = SYSTEM_PROMPT + f"""

DOCUMENTO ACTIVO:
- Archivo: {document.filename or 'Sin nombre'}
- Título: {document.title or 'Sin título'}

CONTENIDO:
{document.content}
"""
    
    try:
        # Log the chat request with Logfire
        if _logfire_available and logfire:
            with logfire.span(
                "chat_stream_direct",
                doc_id=document.doc_id,
                doc_filename=document.filename,
                query_preview=query[:100],
                model=MODEL_NAME,
            ):
                logfire.info(
                    "Starting chat stream",
                    doc_id=document.doc_id,
                    query=query,
                    content_length=len(document.content),
                )
                
                # Conditional parameters based on model family
                is_mistral = "mistral" in MODEL_NAME.lower()
                is_devstral = "devstral" in MODEL_NAME.lower()
                is_ministral = "ministral" in MODEL_NAME.lower()
                is_nemotron_nano = "nemotron-nano" in MODEL_NAME.lower()
                is_kimi_instruct = "kimi-k2-instruct" in MODEL_NAME.lower()
                is_qwen = "qwen" in MODEL_NAME.lower()
                
                # Default parameters
                temp = 1.0
                top_p = 0.9
                max_tokens = 16384
                system_prefix = ""
                
                # Model-specific overrides
                if is_qwen:
                    temp, top_p, max_tokens = 0.6, 0.7, 4096
                elif is_kimi_instruct:
                    temp, top_p, max_tokens = 0.6, 0.9, 4096
                elif is_nemotron_nano:
                    temp, top_p, max_tokens = 0.6, 0.95, 2048
                    if thinking: system_prefix = "/think"
                elif is_devstral:
                    temp, top_p, max_tokens = 0.15, 0.95, 8192
                elif is_ministral:
                    temp, top_p, max_tokens = 0.15, 1.0, 2048
                elif is_mistral:
                    temp, top_p, max_tokens = 0.20, 0.70, 512

                completion_kwargs = {
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": f"{system_prefix}\n{system_msg}".strip()},
                        {"role": "user", "content": query}
                    ],
                    "temperature": temp,
                    "top_p": top_p,
                    "max_tokens": max_tokens,
                    "stream": True
                }
                
                # Special Extra Body parameters
                if is_nemotron_nano and thinking:
                    completion_kwargs["extra_body"] = {
                        "min_thinking_tokens": 1024,
                        "max_thinking_tokens": 2048
                    }
                elif is_devstral:
                    completion_kwargs["seed"] = 42
                elif not is_mistral and not is_kimi_instruct and ("deepseek" in MODEL_NAME.lower() or "kimi" in MODEL_NAME.lower()):
                    completion_kwargs["extra_body"] = {
                        "reasoning_budget": 16384 if thinking else 0,
                        "chat_template_kwargs": {"enable_thinking": thinking, "thinking": thinking}
                    }

                stream = await client.chat.completions.create(**completion_kwargs)
                
                chunk_count = 0
                async for chunk in stream:
                    if not getattr(chunk, "choices", None):
                        continue
                        
                    delta = chunk.choices[0].delta
                    
                    # Stream reasoning if available (DeepSeek/Kimi thinking)
                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning:
                        yield reasoning
                        
                    if delta.content:
                        chunk_count += 1
                        yield delta.content
                
                logfire.info(
                    "Chat stream completed",
                    doc_id=document.doc_id,
                    chunks_sent=chunk_count,
                )
        else:
            # No Logfire, just stream normally
            # Conditional parameters same as above for the non-logfire branch
            is_mistral = "mistral" in MODEL_NAME.lower()
            is_devstral = "devstral" in MODEL_NAME.lower()
            is_ministral = "ministral" in MODEL_NAME.lower()
            is_nemotron_nano = "nemotron-nano" in MODEL_NAME.lower()
            is_kimi_instruct = "kimi-k2-instruct" in MODEL_NAME.lower()
            is_qwen = "qwen" in MODEL_NAME.lower()
            
            temp, top_p, max_tokens = 1.0, 0.9, 16384
            system_prefix = ""
            
            if is_qwen:
                temp, top_p, max_tokens = 0.6, 0.7, 4096
            elif is_kimi_instruct:
                temp, top_p, max_tokens = 0.6, 0.9, 4096
            elif is_nemotron_nano:
                temp, top_p, max_tokens = 0.6, 0.95, 2048
                if thinking: system_prefix = "/think"
            elif is_devstral:
                temp, top_p, max_tokens = 0.15, 0.95, 8192
            elif is_ministral:
                temp, top_p, max_tokens = 0.15, 1.0, 2048
            elif is_mistral:
                temp, top_p, max_tokens = 0.20, 0.70, 512

            completion_kwargs = {
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": f"{system_prefix}\n{system_msg}".strip()},
                    {"role": "user", "content": query}
                ],
                "temperature": temp,
                "top_p": top_p,
                "max_tokens": max_tokens,
                "stream": True
            }
            
            # Special Extra Body parameters
            if is_nemotron_nano and thinking:
                completion_kwargs["extra_body"] = {
                    "min_thinking_tokens": 1024,
                    "max_thinking_tokens": 2048
                }
            elif is_devstral:
                completion_kwargs["seed"] = 42
            elif not is_mistral and not is_kimi_instruct and ("deepseek" in MODEL_NAME.lower() or "kimi" in MODEL_NAME.lower()):
                completion_kwargs["extra_body"] = {
                    "reasoning_budget": 16384 if thinking else 0,
                    "chat_template_kwargs": {"enable_thinking": thinking, "thinking": thinking}
                }

            stream = await client.chat.completions.create(**completion_kwargs)
            
            async for chunk in stream:
                if not getattr(chunk, "choices", None):
                    continue
                    
                delta = chunk.choices[0].delta
                
                # Stream reasoning if available
                reasoning = getattr(delta, "reasoning_content", None)
                if reasoning:
                    yield reasoning
                    
                if delta.content:
                    yield delta.content
                
    except Exception as e:
        logger.exception(f"Error in direct chat stream: {e}")
        if _logfire_available and logfire:
            logfire.error("Chat stream error", error=str(e), doc_id=document.doc_id)
        yield f"\n\nError: {str(e)}"

