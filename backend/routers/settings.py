"""
Settings Router
REST API for managing application settings (API keys, model config, etc.)
Used by the desktop app's Settings page.
"""

from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from src.database.config_service import ConfigService
from utils.auth import require_auth

router = APIRouter()


# ---------- Request / Response Models ----------

class SettingUpdate(BaseModel):
    key: str
    value: str


class SettingBulkUpdate(BaseModel):
    settings: list[SettingUpdate]


# ---------- Endpoints ----------

@router.get("/")
async def list_settings(category: Optional[str] = None, _=Depends(require_auth)):
    """Return all settings (values masked for secrets)."""
    cfg = ConfigService()
    return {"settings": cfg.get_masked(category)}


@router.get("/categories")
async def list_categories(_=Depends(require_auth)):
    """Return all setting categories."""
    cfg = ConfigService()
    return {"categories": cfg.get_categories()}


@router.get("/validate")
async def validate_settings(_=Depends(require_auth)):
    """Check which required settings are missing."""
    cfg = ConfigService()
    missing = cfg.validate_required()
    return {
        "valid": len(missing) == 0,
        "missing": missing,
    }


@router.get("/{key}")
async def get_setting(key: str, _=Depends(require_auth)):
    """Get a single setting (masked if secret)."""
    cfg = ConfigService()
    items = cfg.get_masked()
    for item in items:
        if item["key"] == key:
            return item
    raise HTTPException(status_code=404, detail=f"Setting '{key}' not found")


@router.put("/{key}")
async def update_setting(key: str, body: SettingUpdate, _=Depends(require_auth)):
    """Update a single setting."""
    cfg = ConfigService()
    cfg.set(body.key, body.value)
    return {"ok": True, "key": body.key}


@router.put("/")
async def bulk_update(body: SettingBulkUpdate, _=Depends(require_auth)):
    """Update multiple settings at once."""
    cfg = ConfigService()
    for s in body.settings:
        cfg.set(s.key, s.value)
    return {"ok": True, "updated": len(body.settings)}


@router.delete("/{key}")
async def clear_setting(key: str, _=Depends(require_auth)):
    """Clear (reset) a setting value."""
    cfg = ConfigService()
    cfg.set(key, "")
    return {"ok": True, "key": key}
