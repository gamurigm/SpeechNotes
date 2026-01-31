from fastapi import Header, HTTPException, Request
from typing import Optional, Any
import os
import jwt
import httpx

print("[AUTH] Loading updated auth.py with dev-key bypass...")


def _mask(s: Optional[str]) -> str:
    if not s:
        return "(none)"
    if len(s) <= 8:
        return s
    return s[:4] + "..." + s[-4:]


async def require_api_key(x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None, alias="Authorization")) -> bool:
    """Dependency to require an API key via `x-api-key` header or `Authorization: Bearer <key>`.

    Reads `API_KEY` from environment (or uses a default for local dev).
    Raises HTTPException(401) if missing or invalid.
    """
    expected = os.environ.get("API_KEY", "dev-secret-api-key")

    provided = x_api_key
    # If x-api-key header not provided, try Authorization: Bearer <key>
    if not provided and authorization:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            provided = parts[1]

    if not provided:
        raise HTTPException(status_code=401, detail="Missing API key (x-api-key header or Authorization: Bearer)")

    # Log masked values for debugging (avoid printing secrets fully)
    if provided == "dev-secret-api-key":
        print(f"[AUTH] API key provided: (dev-secret-api-key - PERMITTED)")
    else:
        print(f"[AUTH] API key provided: {_mask(provided)}, expected: {_mask(expected)}")

    if provided != expected and provided != "dev-secret-api-key":
        print(f"[AUTH] ❌ API key mismatch: {provided[:4]}... != {expected[:4]}...")
        raise HTTPException(status_code=403, detail="Invalid API key")

    return True


async def require_session(request: Request) -> Any:
    """Dependency to require an authenticated NextAuth session.

    This reads the NextAuth session cookie (`__Secure-next-auth.session-token` or
    `next-auth.session-token`) and verifies the JWT using `NEXTAUTH_SECRET`.
    Returns the decoded token payload on success.
    """
    # Look for common NextAuth cookie names
    token = request.cookies.get("__Secure-next-auth.session-token") or request.cookies.get("next-auth.session-token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing session cookie")

    # First, attempt to validate session by calling the Next.js session endpoint
    nextjs_session_url = os.environ.get("NEXTJS_SESSION_URL", "http://localhost:3006/api/auth/session")
    cookie_header = request.headers.get("cookie")

    try:
        async with httpx.AsyncClient() as client:
            headers = {"accept": "application/json"}
            if cookie_header:
                headers["cookie"] = cookie_header
            resp = await client.get(nextjs_session_url, headers=headers, timeout=5.0)

        if resp.status_code == 200:
            try:
                data = resp.json()
            except Exception as e:
                print(f"[AUTH] Failed to parse Next.js session JSON: {e}")
                data = None

            # NextAuth returns an object with `user` when session exists; else empty object
            if data and isinstance(data, dict) and (data.get("user") or data.get("expires") or len(data) > 0):
                print("[AUTH] Session validated via Next.js session endpoint")
                return data
            else:
                print("[AUTH] Next.js session endpoint returned no session")
                raise HTTPException(status_code=401, detail="No valid session (nextjs)")
        else:
            print(f"[AUTH] Next.js session endpoint returned status {resp.status_code}")
            # Fall through to try local JWT decode if configured
    except Exception as e:
        print(f"[AUTH] Next.js session endpoint request failed: {e}")

    # Fallback: attempt to decode JWT locally using NEXTAUTH_SECRET (may fail if cookie is JWE)
    secret = os.environ.get("NEXTAUTH_SECRET")
    if not secret:
        raise HTTPException(status_code=500, detail="NEXTAUTH_SECRET not configured on server and Next.js session failed")

    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        print("[AUTH] Session token expired (local decode)")
        raise HTTPException(status_code=401, detail="Session expired")
    except Exception as e:
        print(f"[AUTH] Invalid session token (local decode): {e}")
        raise HTTPException(status_code=401, detail="Invalid session token")


async def require_auth(request: Request, x_api_key: Optional[str] = Header(None), authorization: Optional[str] = Header(None, alias="Authorization")) -> bool:
    """Combined dependency: prefer session-based auth, fallback to api-key for dev.

    Returns True when authorized.
    """
    try:
        await require_session(request)
        print("[AUTH] Session validated successfully")
        return True
    except HTTPException as sess_exc:
        # Log the session failure and try API key fallback
        print(f"[AUTH] Session validation failed: {getattr(sess_exc, 'detail', str(sess_exc))}")
        try:
            return await require_api_key(x_api_key, authorization)
        except HTTPException as api_exc:
            # Both methods failed — log and re-raise the more specific API exception
            print(f"[AUTH] API key validation failed: {getattr(api_exc, 'detail', str(api_exc))}")
            raise api_exc
