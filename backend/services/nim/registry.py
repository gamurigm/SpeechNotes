"""
NIM Client Registry — Infrastructure Layer

Central factory and singleton registry for all NIM clients.

Design Patterns:
    - Factory Method (Creational): NIMRegistry.get() creates the
      correct client class based on NIMClientType.
    - Singleton (Creational): Each NIMConfig maps to exactly one
      client instance. Subsequent calls for the same config return
      the cached instance (no re-authentication overhead).
    - Registry (Creational / Structural): Maintains a name-indexed
      catalogue so application services can resolve clients by their
      logical names ("asr", "translator", etc.) rather than wiring
      config objects manually.

Architecture Layer: Infrastructure / IoC Container
"""

from __future__ import annotations

import logging
import os
from typing import Dict, Optional, Type, Union

from backend.services.nim.protocols import (
    AudioEnhancementPort,
    AudioTranscriptionPort,
    NIMClientType,
    NIMConfig,
    TextGenerationPort,
)

logger = logging.getLogger(__name__)

# Type alias for any NIM client (union of all capability ports)
AnyNIMClient = Union[TextGenerationPort, AudioTranscriptionPort, AudioEnhancementPort]


class NIMRegistry:
    """
    Thread-safe singleton registry for NIM client instances.

    Usage:
        registry = NIMRegistry.instance()
        translator = registry.get("translator")  # TextGenerationPort
        asr        = registry.get_asr()          # AudioTranscriptionPort
        bnr        = registry.get_bnr()          # AudioEnhancementPort
    """

    _instance: Optional["NIMRegistry"] = None
    _clients: Dict[str, AnyNIMClient] = {}
    _configs: Dict[str, NIMConfig] = {}

    # ── Singleton ────────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> "NIMRegistry":
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls._instance._clients = {}
            cls._instance._configs = {}
            cls._instance._build_from_env()
        return cls._instance

    # ── Factory: build NIMConfig from environment / ConfigService ────────

    def _build_from_env(self) -> None:
        """
        Bootstrap all NIM configs from environment / ConfigService.
        Called once at first access.
        """
        try:
            from src.database.config_service import ConfigService
            cfg = ConfigService()
            _g = cfg.get
        except Exception:
            _g = os.environ.get  # type: ignore

        base_url = _g("NVIDIA_BASE_URL") or "https://integrate.api.nvidia.com/v1"

        # ── Chat: Qwen 3.5 (thinking) ─────────────────────────────────
        self._register(NIMConfig(
            name="thinking",
            api_key=_g("NVIDIA_API_KEY_THINKING") or _g("NVIDIA_API_KEY") or "",
            base_url=base_url,
            model_id=_g("CHAT_MODEL_THINKING") or "qwen/qwen3.5-397b-a17b",
            client_type=NIMClientType.HTTP_OPENAI,
            extra={"chat_template_kwargs": {"enable_thinking": True},
                   "top_k": 20,
                   "repetition_penalty": 1},
        ))

        # ── Chat: Mistral Large (translator / formal text) ────────────
        self._register(NIMConfig(
            name="translator",
            api_key=_g("NVIDIA_API_KEY_TRANSLATOR") or _g("NVIDIA_API_KEY") or "",
            base_url=base_url,
            model_id=_g("TRANSLATOR_MODEL") or "mistralai/mistral-large-3-675b-instruct-2512",
            client_type=NIMClientType.HTTP_OPENAI,
            extra={"frequency_penalty": 0.0, "presence_penalty": 0.0},
        ))

        # ── Chat: Gemma 3n (language detection, fast multi-language) ──
        self._register(NIMConfig(
            name="detector",
            api_key=_g("NVIDIA_API_KEY_DETECTOR") or _g("NVIDIA_API_KEY") or "",
            base_url=base_url,
            model_id=_g("DETECTOR_MODEL") or "google/gemma-3n-e4b-it",
            client_type=NIMClientType.HTTP_OPENAI,
        ))

        # ── ASR: Whisper via Riva gRPC (English) ────────────────────────
        # integrate.api.nvidia.com does NOT support /audio/transcriptions.
        # Whisper hosted on NVCF via Riva gRPC is the correct endpoint.
        riva_server = _g("RIVA_SERVER") or "grpc.nvcf.nvidia.com:443"
        riva_host, _, riva_port_str = riva_server.rpartition(":")
        riva_port = int(riva_port_str) if riva_port_str.isdigit() else 443
        if not riva_host:
            riva_host = riva_server
            riva_port = 443
        riva_func_id = _g("RIVA_FUNCTION_ID_WHISPER") or ""

        self._register(NIMConfig(
            name="asr",
            api_key=_g("NVIDIA_API_KEY_ASR") or _g("API_KEY") or _g("NVIDIA_API_KEY") or "",
            base_url="",  # unused for gRPC
            model_id="whisper",
            client_type=NIMClientType.RIVA_ASR,
            grpc_host=riva_host,
            grpc_port=riva_port,
            grpc_function_id=riva_func_id,
        ))

        # ── ASR: Whisper via Riva gRPC (Spanish & multilingual) ──────────
        # Same Whisper function, different language_code passed at runtime.
        self._register(NIMConfig(
            name="asr_es",
            api_key=_g("NVIDIA_API_KEY_ASR_ES") or _g("NVIDIA_API_KEY_ASR") or _g("API_KEY") or _g("NVIDIA_API_KEY") or "",
            base_url="",  # unused for gRPC
            model_id="whisper",
            client_type=NIMClientType.RIVA_ASR,
            grpc_host=riva_host,
            grpc_port=riva_port,
            grpc_function_id=riva_func_id,
        ))

        # ── Audio Enhancement: BNR (gRPC) ─────────────────────────────
        self._register(NIMConfig(
            name="bnr",
            api_key=_g("NVIDIA_API_KEY_BNR") or "",
            base_url=base_url,
            model_id="nvidia/bnr",
            client_type=NIMClientType.GRPC,
            grpc_host=_g("BNR_GRPC_HOST") or "grpc.nvcf.nvidia.com",
            grpc_port=int(_g("BNR_GRPC_PORT") or "443"),
            grpc_function_id=_g("BNR_FUNCTION_ID") or "",
        ))

    # ── Registration ─────────────────────────────────────────────────────

    def _register(self, config: NIMConfig) -> None:
        """Store config; client is lazily instantiated on first get()."""
        self._configs[config.name] = config
        logger.debug("[NIMRegistry] Registered config '%s'", config.name)

    # ── Factory Method ───────────────────────────────────────────────────

    def get(self, name: str) -> AnyNIMClient:
        """
        Return the (lazily-created) client for a registered config name.

        Raises KeyError if name is not registered.
        """
        if name not in self._clients:
            config = self._configs[name]
            self._clients[name] = self._create(config)
        return self._clients[name]

    def _create(self, config: NIMConfig) -> AnyNIMClient:
        """
        Factory Method: creates the concrete client matching config.client_type.
        """
        if config.client_type == NIMClientType.GRPC:
            from backend.services.nim.grpc_client import BNRGrpcClient
            return BNRGrpcClient(config)

        if config.client_type == NIMClientType.RIVA_ASR:
            from backend.services.nim.riva_asr_client import RivaWhisperASRClient
            return RivaWhisperASRClient(config)

        if config.client_type == NIMClientType.GROQ_ASR:
            from backend.services.nim.groq_client import GroqASRClient
            return GroqASRClient(config)

        # Default: HTTP OpenAI-compatible
        # Use ThinkingClient for models that have enable_thinking
        from backend.services.nim.openai_client import OpenAINIMClient, ThinkingNIMClient

        if config.extra.get("chat_template_kwargs", {}).get("enable_thinking"):
            return ThinkingNIMClient(config)
        return OpenAINIMClient(config)

    # ── Convenience accessors (typed) ─────────────────────────────────────

    def get_text(self, name: str = "thinking") -> TextGenerationPort:
        return self.get(name)  # type: ignore[return-value]

    def get_asr(self, language: str | None = None) -> AudioTranscriptionPort:
        """Return the ASR client for the given language.

        - ``'es'`` → ``asr_es`` (Whisper via Riva gRPC, es-ES locale)
        - anything else → ``asr`` (Whisper via Riva gRPC, en-US locale)
        """
        name = "asr_es" if language and language.startswith("es") else "asr"
        return self.get(name)  # type: ignore[return-value]

    def get_bnr(self) -> AudioEnhancementPort:
        return self.get("bnr")  # type: ignore[return-value]
