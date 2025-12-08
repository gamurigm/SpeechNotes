from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import json
import os

router = APIRouter()

# Path to the VAD configuration file
# Adjust path relative to backend/routers/vad_config.py
# backend/routers/ -> backend/ -> root -> temporal_docs/configuracion/.vad_config.json
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_PATH = os.path.join(BASE_DIR, "temporal_docs", "configuracion", ".vad_config.json")

class VadConfig(BaseModel):
    voice_threshold: int
    silence_threshold: int

@router.get("/", response_model=VadConfig)
async def get_vad_config():
    if not os.path.exists(CONFIG_PATH):
        # Return default values if file doesn't exist
        # Defaults based on common RMS values
        return VadConfig(
            voice_threshold=500,
            silence_threshold=200
        )
    
    try:
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        # Handle case where file might have old keys
        return VadConfig(
            voice_threshold=data.get('voice_threshold', 500),
            silence_threshold=data.get('silence_threshold', 200)
        )
    except Exception as e:
        # If file is corrupt or has invalid data, return defaults
        print(f"Error reading config: {e}")
        return VadConfig(
            voice_threshold=500,
            silence_threshold=200
        )

@router.post("/", response_model=VadConfig)
async def save_vad_config(config: VadConfig):
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        
        with open(CONFIG_PATH, "w") as f:
            json.dump(config.dict(), f, indent=4)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving config: {str(e)}")
