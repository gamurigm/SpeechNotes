from fastapi import APIRouter, HTTPException
import traceback
from pydantic import BaseModel
from backend.repositories.transcription_repository import TranscriptionRepository
from backend.services.content_renderer import ContentRenderer

router = APIRouter()
repo = TranscriptionRepository()
renderer = ContentRenderer()

class TranscriptionUpdate(BaseModel):
    content: str

@router.get("/latest")
async def get_latest_transcription():
    """Get the latest processed transcription using Repository/Strategy Pattern"""
    try:
        doc = repo.get_latest()
        if not doc:
            return {
                "id": None,
                "filename": None,
                "date": None,
                "content": "# No hay transcripciones disponibles\n\nGraba tu primera clase para comenzar."
            }
        
        segments = repo.get_segments(doc["_id"])
        content = renderer.render_transcription(doc, segments)
        
        return {
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content,
            "is_formatted": doc.get("is_formatted", False)
        }
    except Exception as e:
        print(f"[ERROR] /api/transcriptions/latest: {e}")
        traceback.print_exc()
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/")
async def list_transcriptions(limit: int = 50):
    """List recent processed transcriptions (metadata only)"""
    try:
        items_raw = repo.list_recent(limit)
        items = [{
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "is_formatted": doc.get("is_formatted", False)
        } for doc in items_raw]
        return {"items": items}
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.get("/search")
async def search_transcriptions(q: str):
    """Global search using Repository logic"""
    if not q or len(q) < 2:
        return {"items": []}
    
    try:
        res = repo.search(q)
        results = []
        
        # Format Document results
        for doc in res["documents"]:
            content = doc.get("formatted_content", "") or ""
            idx = content.lower().find(q.lower())
            snippet = (content[max(0, idx-40):idx+60].replace("\n", " ") + "...") if idx != -1 else ""
            
            results.append({
                "id": str(doc["_id"]),
                "filename": doc.get("filename"),
                "date": doc.get("date"),
                "snippet": snippet,
                "type": "document"
            })
            
        # Format Segment results
        parent_ids = set([r["id"] for r in results])
        for seg in res["segments"]:
            t_id = str(seg["transcription_id"])
            if t_id in parent_ids: continue
            
            doc = repo.get_by_id(t_id)
            if doc:
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
        raise HTTPException(500, f"Search error: {str(e)}")

@router.get("/{transcription_id}")
async def get_transcription_by_id(transcription_id: str):
    """Get a specific processed transcription by id"""
    try:
        doc = repo.get_by_id(transcription_id)
        if not doc:
            raise HTTPException(404, "Not found")

        segments = repo.get_segments(doc["_id"])
        content = renderer.render_transcription(doc, segments)

        return {
            "id": str(doc["_id"]),
            "filename": doc.get("filename"),
            "date": doc.get("date"),
            "content": content,
            "is_formatted": doc.get("is_formatted", False)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Error: {str(e)}")

@router.put("/{transcription_id}")
async def update_transcription(transcription_id: str, update: TranscriptionUpdate):
    """Update transcription content"""
    if repo.update_content(transcription_id, update.content):
        return {"status": "updated"}
    raise HTTPException(404, "Not found")

@router.delete("/{transcription_id}")
async def delete_transcription(transcription_id: str):
    """Logically delete a transcription"""
    if repo.delete(transcription_id):
        return {"status": "deleted"}
    raise HTTPException(404, "Not found")
