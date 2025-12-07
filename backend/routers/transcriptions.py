"""
Transcriptions REST API Router
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from fastapi import APIRouter, HTTPException
import traceback
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

        # If there are no segments but the document already contains formatted content
        # (inserted by the formatter), return that directly to avoid generator errors.
        if not segments and doc.get("formatted_content"):
            content = doc.get("formatted_content")
        else:
            try:
                topics = generator._group_by_topic(segments)
                content = generator._build_markdown(doc, topics)
            except Exception as e:
                # Log and fallback to formatted_content or raw_content if available
                print(f"[ERROR] DocumentGenerator failed for {doc.get('filename')}: {e}")
                if doc.get("formatted_content"):
                    content = doc.get("formatted_content")
                elif doc.get("raw_content"):
                    content = doc.get("raw_content")
                else:
                    content = "# Error generating document\n\nNo content available."
        
        # Safely read fields with defaults to avoid KeyError
        return {
            "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content
        }
    except Exception as e:
        # Print full traceback to server logs for debugging
        print("[ERROR] /api/transcriptions/latest exception:")
        traceback.print_exc()
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
