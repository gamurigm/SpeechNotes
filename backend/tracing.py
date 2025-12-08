"""OpenTelemetry tracing setup for the SpeechNotes backend.

Provides `init_tracing()` to configure a TracerProvider and exporters,
and `instrument_fastapi(app)` to instrument the FastAPI app for automatic spans.
"""
import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

try:
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
except Exception:
    FastAPIInstrumentor = None

try:
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
except Exception:
    RequestsInstrumentor = None

try:
    # Instrument OpenAI-compatible SDKs (including NVIDIA OpenAI-compatible client)
    from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
except Exception:
    OpenAIInstrumentor = None


def init_tracing(service_name: Optional[str] = None):
    """Initialize OpenTelemetry tracing with OTLP exporter (and console for local debugging).

    Reads `OTEL_EXPORTER_OTLP_ENDPOINT` env var or defaults to `http://localhost:4318/v1/traces`.
    """
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "speechnotes-backend")
    endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318/v1/traces")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    # OTLP exporter
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint)
    provider.add_span_processor(BatchSpanProcessor(otlp_exporter))

    # Console exporter for local debugging
    provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)

    # Instrument outgoing HTTP requests
    if RequestsInstrumentor is not None:
        try:
            RequestsInstrumentor().instrument()
        except Exception:
            pass

    # Instrument OpenAI / OpenAI-compatible calls if available
    if OpenAIInstrumentor is not None:
        try:
            # capture message content as log events via env var if desired
            os.environ.setdefault("OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "true")
            OpenAIInstrumentor().instrument()
        except Exception:
            pass


def instrument_fastapi(app):
    """Instrument the given FastAPI `app` (calls FastAPIInstrumentor)."""
    if FastAPIInstrumentor is None:
        return
    try:
        FastAPIInstrumentor().instrument_app(app)
    except Exception:
        pass
