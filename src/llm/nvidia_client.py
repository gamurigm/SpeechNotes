"""
NVIDIA NIM Inference Client
Singleton wrapper for NVIDIA's API using OpenAI client.
"""

import os
from typing import Optional, List, Dict, Any, Iterator
from openai import OpenAI
from dotenv import load_dotenv
import logfire

# Load environment variables, overriding system vars to ensure .env is used
load_dotenv(override=True)
from src.database.config_service import ConfigService


class NvidiaInferenceClient:
    """
    Singleton client for NVIDIA NIM API.
    Provides inference capabilities using DeepSeek-V3.1-Terminus model.
    """
    
    _instance: Optional['NvidiaInferenceClient'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'NvidiaInferenceClient':
        """Ensure only one instance exists (Singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the NVIDIA client (only once)."""
        if not self._initialized:
            _cfg = ConfigService()
            self.api_key = _cfg.get("NVIDIA_API_KEY")
            # Clean API key (remove comments and whitespace)
            if self.api_key:
                self.api_key = self.api_key.split('#')[0].strip()

            self.base_url = _cfg.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
            self.model_name = _cfg.get("MODEL_NAME", "deepseek-ai/deepseek-v3.1-terminus")
            
            if not self.api_key:
                raise ValueError("NVIDIA_API_KEY not found in environment variables")
            
            # Log initialization (masked key)
            masked_key = f"{self.api_key[:10]}...{self.api_key[-5:]}" if self.api_key else "None"
            print(f"[NVIDIA Client] Initialized with model: {self.model_name}")
            print(f"[NVIDIA Client] Base URL: {self.base_url}")
            print(f"[NVIDIA Client] API Key: {masked_key}")

            if not self.api_key.startswith("nvapi-"):
                print(f"[NVIDIA Client] WARNING: API Key does not start with 'nvapi-'. It might be invalid.")
            
            self.client = OpenAI(
                base_url=self.base_url,
                api_key=self.api_key
            )
            
            # Default parameters
            self.temperature = float(_cfg.get("TEMPERATURE", "0.2"))
            self.top_p = float(_cfg.get("TOP_P", "0.7"))
            self.max_tokens = int(_cfg.get("MAX_TOKENS", "8192"))
            
            NvidiaInferenceClient._initialized = True
    
    @logfire.instrument
    def generate(
        self,
        prompt: str,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Generate a response using NVIDIA NIM API.
        
        Args:
            prompt: User prompt/question
            messages: Optional list of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text response
        """
        # Build messages list
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        elif not any(msg.get("content") == prompt for msg in messages):
            messages.append({"role": "user", "content": prompt})
        
        # Use provided parameters or defaults
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                top_p=tp,
                max_tokens=max_tok,
                stream=False,
                **kwargs
            )
            
            return completion.choices[0].message.content
        
        except Exception as e:
            raise RuntimeError(f"Error generating response from NVIDIA NIM: {str(e)}")
    
    def stream_generate(
        self,
        prompt: str,
        messages: Optional[List[Dict[str, str]]] = None,
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate a streaming response using NVIDIA NIM API.
        
        Args:
            prompt: User prompt/question
            messages: Optional list of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Yields:
            Text chunks as they are generated
        """
        # Build messages list
        if messages is None:
            messages = [{"role": "user", "content": prompt}]
        elif not any(msg.get("content") == prompt for msg in messages):
            messages.append({"role": "user", "content": prompt})
        
        # Use provided parameters or defaults
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            with logfire.span("nvidia_stream_generate", prompt_preview=prompt[:50]):
                stream = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=temp,
                    top_p=tp,
                    max_tokens=max_tok,
                    stream=True,
                    **kwargs
                )
                
                for chunk in stream:
                    if chunk.choices[0].delta.content is not None:
                        yield chunk.choices[0].delta.content
        
        except Exception as e:
            raise RuntimeError(f"Error streaming response from NVIDIA NIM: {str(e)}")
    
    @logfire.instrument
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        top_p: Optional[float] = None,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Chat completion with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            top_p: Nucleus sampling parameter
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters for the API
            
        Returns:
            Generated text response
        """
        temp = temperature if temperature is not None else self.temperature
        tp = top_p if top_p is not None else self.top_p
        max_tok = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temp,
                top_p=tp,
                max_tokens=max_tok,
                stream=False,
                **kwargs
            )
            
            return completion.choices[0].message.content
        
        except Exception as e:
            raise RuntimeError(f"Error in chat completion: {str(e)}")
