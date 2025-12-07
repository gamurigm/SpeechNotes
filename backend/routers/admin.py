from fastapi import APIRouter, Depends, HTTPException
from typing import Dict
import os

try:
    from backend.utils.auth import require_api_key
except Exception:
    from ..utils.auth import require_api_key

from src.database.mongo_manager import MongoManager

router = APIRouter()


@router.delete("/clear_transcriptions")
async def clear_transcriptions(api_ok: bool = Depends(require_api_key)) -> Dict[str, int]:
    """Delete all documents in the `transcriptions` collection.

    Protected by API key. Use with caution.
    """
    try:
        db = MongoManager()
        result = db.transcriptions.delete_many({})
        return {"deleted_count": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear transcriptions: {e}")
