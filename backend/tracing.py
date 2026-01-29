"""
Logfire Observability setup for SpeechNotes.
Centralized configuration for tracing and logging.
"""
import os
import logfire
from typing import Optional

def init_tracing(service_name: Optional[str] = None):
    """
    Initialize Logfire with automatic instrumentation.
    """
    token = os.getenv("LOGFIRE_TOKEN")
    project_name = os.getenv("LOGFIRE_PROJECT_NAME", "speechnotes")
    service_name = service_name or os.getenv("OTEL_SERVICE_NAME", "speechnotes-backend")

    if not token:
        print("⚠️ Logfire token not found. Tracing will be disabled.")
        return

    # Configure Logfire
    logfire.configure(
        token=token,
        service_name=service_name,
        send_to_logfire=True
    )

    # Automatic instrumentation
    try:
        logfire.instrument_requests()
        logfire.instrument_httpx()
        logfire.instrument_pymongo()
        logfire.instrument_pydantic_ai()
        print(f"✅ Logfire initialized for {service_name}")
    except Exception as e:
        print(f"⚠️ Error during Logfire instrumentation: {e}")

def instrument_fastapi(app):
    """
    Instrument the FastAPI app with Logfire.
    """
    try:
        logfire.instrument_fastapi(app)
    except Exception as e:
        print(f"⚠️ Failed to instrument FastAPI with Logfire: {e}")
