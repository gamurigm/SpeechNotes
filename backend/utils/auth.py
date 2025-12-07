from fastapi import Header, HTTPException
from typing import Optional
import os


async def require_api_key(x_api_key: Optional[str] = Header(None)) -> bool:
    """Dependency to require an API key via `x-api-key` header.

    Reads `API_KEY` from environment (or uses a default for local dev).
    Raises HTTPException(401) if missing or invalid.
    """
    expected = os.environ.get("API_KEY", "dev-secret-api-key")

    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key (x-api-key header)")

    if x_api_key != expected:
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True
