"""
Pydantic AI Agent for Document-Aware Chat

This module implements a chat agent using Pydantic AI that:
1. Receives the active document context via dependency injection
2. Uses Logfire for observability
3. Responds based ONLY on the current document
"""

import os
import asyncio
import logging
import time
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv

from pydantic import BaseModel
from pydantic_ai import Agent, RunContext

import logfire
logger = logging.getLogger(__name__)


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


# Load environment variables
# Look for .env in the current directory and up
load_dotenv(os.path.join(os.getcwd(), '.env'))
# Also look in one directory up (if running from backend/services)
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))
load_dotenv() # Fallback for any other standard search path

# --- Agent Configuration ---

# Get model configuration from environment
NVIDIA_API_KEY_THINKING = os.getenv("NVIDIA_API_KEY_THINKING")
NVIDIA_API_KEY_FAST = os.getenv("NVIDIA_API_KEY_FAST")
NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY") # Keep for compatibility
NVIDIA_BASE_URL = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("CHAT_MODEL_THINKING", "minimaxai/minimax-m2")
MODEL_NAME_FAST = os.getenv("CHAT_MODEL_FAST", "nvidia/nvidia-nemotron-nano-9b-v2")
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")

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
    # Select model and key based on mode
    current_model = MODEL_NAME if thinking else MODEL_NAME_FAST
    current_key = NVIDIA_API_KEY_THINKING if thinking else NVIDIA_API_KEY_FAST
    # Fallback to MINIMAX_API_KEY if specific thinking key is missing
    current_key = current_key or os.getenv("MINIMAX_API_KEY")
    
    if not current_key:
        yield f"Error: API Key for {'Thinking' if thinking else 'Fast'} mode not configured"
        return
    
    # Increase timeout to 120s for thinking models (504 prevention)
    client = AsyncOpenAI(
        base_url=NVIDIA_BASE_URL,
        api_key=current_key,
        timeout=120.0 
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
        # Default parameters
        if not thinking:
            # Nemotron Nano 9B v2 (Fast Mode)
            temp = 0.6
            top_p = 0.95
            max_tokens = 2048
            system_prefix = "" 
            completion_kwargs = {
                "frequency_penalty": 0,
                "presence_penalty": 0
            }
        else:
            # Minimax M2 (Thinking Mode) - Optimized for speed as per user snippet
            temp = 1.0
            top_p = 0.95
            max_tokens = 8192
            system_prefix = ""
            completion_kwargs = {} # Remove extra_body to avoid slowing down generation

        final_system_content = f"{system_prefix}\n{system_msg}".strip()
        logger.info(f"Starting direct stream: model={current_model}, thinking={thinking}")
        
        # We'll use a queue to handle the stream and send heartbeats independently
        queue = asyncio.Queue()
        
        async def stream_producer():
            try:
                # Execute chat stream
                stream = await client.chat.completions.create(
                    model=current_model,
                    messages=[
                        {"role": "system", "content": final_system_content},
                        {"role": "user", "content": query}
                    ],
                    temperature=temp,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    stream=True,
                    **completion_kwargs
                )
                async for chunk in stream:
                    await queue.put(chunk)
                await queue.put(None) # End sentinel
            except Exception as e:
                logger.error(f"Error in stream producer: {e}")
                await queue.put(e)

        # Start the producer task
        producer_task = asyncio.create_task(stream_producer())
        start_time = time.time()
        first_token_time = None
        
        try:
            token_count = 0
            while True:
                try:
                    # Wait for a chunk from the producer with a 5s timeout
                    chunk = await asyncio.wait_for(queue.get(), timeout=5.0)
                    
                    if chunk is None:
                        break # End of stream
                        
                    if isinstance(chunk, Exception):
                        # The router expects content strings which it will wrap in JSON
                        yield f"\n\n[Error: {str(chunk)}]"
                        break

                    if not chunk.choices:
                        continue
                        
                    delta = chunk.choices[0].delta
                    
                    # If skipping reasoning tokens, we yield a periodic space 
                    # to signal to the proxy that we are still alive.
                    reasoning = getattr(delta, "reasoning_content", None)
                    if reasoning and not delta.content:
                        # Heartbeat for reasoning tokens
                        yield " "
                        continue

                    if delta.content:
                        if token_count == 0:
                            first_token_time = time.time() - start_time
                            logger.info(f"First content chunk received for {current_model} in {first_token_time:.2f}s")
                            # Inform user about the delay if it's long
                            if first_token_time > 10:
                                yield f" [Tiempo de respuesta Kimi: {first_token_time:.1f}s]\n\n"
                        token_count += 1
                        yield delta.content
                    
                except asyncio.TimeoutError:
                    # No chunk received in 5s - send a space to keep the connection alive
                    logger.debug("Sending keep-alive heartbeat...")
                    yield " "
                    
            logger.info(f"Direct stream finished: {current_model}, total tokens: {token_count}")
        finally:
            if not producer_task.done():
                producer_task.cancel()
                
    except Exception as e:
        logger.exception(f"Error in direct chat stream: {e}")
        if _logfire_available and logfire:
            logfire.error("Chat stream error", error=str(e), doc_id=document.doc_id)
        yield f"\n\nError: {str(e)}"

