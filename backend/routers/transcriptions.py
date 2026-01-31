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
            {"processed": True, "is_deleted": {"$ne": True}},
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

        # 1. Prefer formatted content if available (Professional/Kimi Format)
        if doc.get("is_formatted") and doc.get("formatted_content"):
            content = doc.get("formatted_content")
        # 2. Fallback if no segments but formatted content exists 
        elif not segments and doc.get("formatted_content"):
            content = doc.get("formatted_content")
        # 3. Last fallback: Build from segments (Automatic/General Format)
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
            "content": content,
            "is_formatted": doc.get("is_formatted", False)
        }
    except Exception as e:
        # Print full traceback to server logs for debugging
        print("[ERROR] /api/transcriptions/latest exception:")
        traceback.print_exc()
        raise HTTPException(500, f"Error: {str(e)}")


@router.get("/")
async def list_transcriptions(limit: int = 50):
    """List recent processed transcriptions (metadata only)"""
    try:
        cursor = db.transcriptions.find({"processed": True, "is_deleted": {"$ne": True}}).sort("ingested_at", -1).limit(limit)
        items = []
        for doc in cursor:
            items.append({
                "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
                "filename": doc.get("filename"),
                "date": doc.get("date"),
                "is_formatted": doc.get("is_formatted", False)
            })

        return {"items": items}
    except Exception as e:
        print("[ERROR] /api/transcriptions list exception:")
        traceback.print_exc()
        raise HTTPException(500, f"Error: {str(e)}")


    except Exception as e:
        print("[ERROR] /api/transcriptions/{id} exception:")
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

@router.delete("/{transcription_id}")
async def delete_transcription(transcription_id: str):
    """Logically delete a transcription"""
    try:
        # Cast to ObjectId to match MongoDB _id type
        oid = ObjectId(transcription_id)
        result = db.transcriptions.update_one(
            {"_id": oid},
            {"$set": {"is_deleted": True}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(404, "Not found")
        
        return {"status": "deleted"}
    except Exception as e:
        print(f"[ERROR] delete_transcription: {e}")
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/search")
async def search_transcriptions(q: str):
    """Global search across all documents and segments"""
    if not q or len(q) < 2:
        return {"items": []}
    
    try:
        query = {"$regex": q, "$options": "i"}
        results = []
        
        # 1. Search in transcriptions (formatted_content)
        docs = db.transcriptions.find({
            "is_deleted": {"$ne": True},
            "processed": True,
            "$or": [
                {"formatted_content": query},
                {"filename": query}
            ]
        }).limit(20)
        
        for doc in docs:
            content = doc.get("formatted_content", "") or ""
            # Get snippet
            idx = content.lower().find(q.lower())
            snippet = ""
            if idx != -1:
                start = max(0, idx - 40)
                end = min(len(content), idx + 60)
                snippet = content[start:end].replace("\n", " ") + "..."
            
            results.append({
                "id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "date": doc.get("date"),
                "snippet": snippet,
                "type": "document"
            })
            
        # 2. Search in segments
        segments = db.segments.find({"content": query}).limit(30)
        parent_ids = set([res["id"] for res in results])
        
        for seg in segments:
            t_id = str(seg["transcription_id"])
            if t_id in parent_ids:
                continue
            
            # Get doc metadata
            doc = db.transcriptions.find_one({"_id": seg["transcription_id"], "is_deleted": {"$ne": True}})
            if not doc:
                continue
                
            results.append({
                "id": t_id,
                "filename": doc.get("filename"),
                "date": doc.get("date"),
                "snippet": seg["content"],
                "timestamp": seg.get("timestamp"),
                "type": "segment"
            })
            
        return {"items": results}
    except Exception as e:
        print(f"[ERROR] search_transcriptions: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Search error: {str(e)}")

@router.get("/{transcription_id}")
async def get_transcription_by_id(transcription_id: str):
    """Get a specific processed transcription by id"""
    try:
        doc = db.transcriptions.find_one({"_id": ObjectId(transcription_id)})
        if not doc:
            raise HTTPException(404, "Not found")

        segments = list(db.segments.find({"transcription_id": doc["_id"]}).sort("sequence", 1))

        # 1. Prefer formatted content if available (Professional/Kimi Format)
        if doc.get("is_formatted") and doc.get("formatted_content"):
             content = doc.get("formatted_content")
        # 2. Fallback if no segments but formatted content exists
        elif not segments and doc.get("formatted_content"):
            content = doc.get("formatted_content")
        # 3. Last fallback: Build from segments (Automatic/General Format)
        else:
            try:
                topics = generator._group_by_topic(segments)
                content = generator._build_markdown(doc, topics)
            except Exception as e:
                print(f"[ERROR] DocumentGenerator failed for {doc.get('filename')}: {e}")
                if doc.get("formatted_content"):
                    content = doc.get("formatted_content")
                elif doc.get("raw_content"):
                    content = doc.get("raw_content")
                else:
                    content = "# Error generating document\n\nNo content available."

        return {
            "id": str(doc.get("_id")) if doc.get("_id") is not None else None,
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content,
            "is_formatted": doc.get("is_formatted", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        print("[ERROR] /api/transcriptions/{id} exception:")
        traceback.print_exc()
        raise HTTPException(500, f"Error: {str(e)}")
