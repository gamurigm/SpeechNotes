"""
Transcriptions REST API Router
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from bson import ObjectId
from src.database import MongoManager
from src.agent.document_generator import DocumentGenerator

router = APIRouter()
db = MongoManager()
generator = DocumentGenerator()

class TranscriptionUpdate(BaseModel):
    content: str

@router.get("/latest")
async def get_latest_transcription():
    """Get the latest processed transcription"""
    try:
        doc = db.transcriptions.find_one(
            {"processed": True},
            sort=[("ingested_at", -1)]
        )
        
        if not doc:
            return {
                "id": None,
                "filename": None,
                "date": None,
                "content": "# No hay transcripciones disponibles\n\nGraba tu primera clase para comenzar."
            }
        
        segments = list(db.segments.find(
            {"transcription_id": doc["_id"]}
        ).sort("sequence", 1))
        
        topics = generator._group_by_topic(segments)
        content = generator._build_markdown(doc, topics)
        
        return {
            "id": str(doc["_id"]),
            "filename": doc["filename"],
            "date": doc["date"],
            "content": content
        }
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.put("/{transcription_id}")
async def update_transcription(transcription_id: str, update: TranscriptionUpdate):
    """Update transcription content"""
    try:
        result = db.transcriptions.update_one(
            {"_id": ObjectId(transcription_id)},
            {"$set": {"edited_content": update.content}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(404, "Not found")
        
        return {"status": "updated"}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")
