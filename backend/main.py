"""
FastAPI Backend with Socket.IO for SpeechNotes
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI
# Initialize tracing as early as possible
try:
    from backend.tracing import init_tracing, instrument_fastapi
    init_tracing()
except Exception:
    init_tracing = None
    instrument_fastapi = None
from fastapi.middleware.cors import CORSMiddleware
import socketio
from routers import transcriptions
from routers import debug
from routers import admin

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=['http://localhost:3006']
)

# Create FastAPI app
app = FastAPI(
    title="SpeechNotes API",
    description="Backend API for real-time transcription",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3006",
        "http://127.0.0.1:3006",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include REST API routers
app.include_router(transcriptions.router, prefix="/api/transcriptions", tags=["transcriptions"])

# Debug routes
app.include_router(debug.router, prefix="/api/debug", tags=["debug"])
app.include_router(admin.router, prefix="/api/admin", tags=["admin"])

# Import and include formatter router
from routers import formatter
app.include_router(formatter.router, prefix="/api/format", tags=["formatter"])

# Import and include chat router
from routers import chat
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])

# Instrument FastAPI app for tracing (if available)
try:
    if instrument_fastapi:
        instrument_fastapi(app)
except Exception:
    pass

# Socket.IO event handlers
from services.socket_handler import register_socket_events
register_socket_events(sio)

# Combine FastAPI and Socket.IO
socket_app = socketio.ASGIApp(sio, app)

@app.get("/")
def read_root():
    return {
        "status": "ok",
        "message": "SpeechNotes API with Socket.IO",
        "version": "1.0.0"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(socket_app, host="0.0.0.0", port=8000, reload=False)
