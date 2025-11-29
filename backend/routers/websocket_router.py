"""
WebSocket Router
Handles real-time audio streaming and transcription
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.audio_processor import AudioProcessor
import json

router = APIRouter()

@router.websocket("/transcribe")
async def websocket_transcribe(websocket: WebSocket):
    """WebSocket endpoint for real-time transcription"""
    await websocket.accept()
    processor = AudioProcessor()
    
    try:
        print("[WebSocket] Client connected")
        
        while True:
            # Receive audio chunk from browser
            data = await websocket.receive()
            
            if "bytes" in data:
                audio_data = data["bytes"]
                print(f"[WebSocket] Received audio chunk: {len(audio_data)} bytes")
                
                # Process and transcribe
                result = await processor.transcribe_chunk(audio_data)
                
                if result:
                    # Send transcribed text back
                    await websocket.send_json({
                        "type": "transcription",
                        "text": result["text"],
                        "timestamp": result["timestamp"]
                    })
                    print(f"[WebSocket] Sent transcription: {result['text'][:50]}...")
            
            elif "text" in data:
                # Handle control messages
                message = json.loads(data["text"])
                
                if message.get("type") == "stop":
                    print("[WebSocket] Stop recording requested")
                    # Save final transcription
                    await processor.finalize()
                    await websocket.send_json({
                        "type": "complete",
                        "message": "Transcription saved"
                    })
                    break
                    
    except WebSocketDisconnect:
        print("[WebSocket] Client disconnected")
    except Exception as e:
        print(f"[WebSocket] Error: {e}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })
    finally:
        await processor.cleanup()
