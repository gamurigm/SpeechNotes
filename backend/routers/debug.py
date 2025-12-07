from fastapi import APIRouter, Request
import os
import jwt

router = APIRouter()


@router.get("/auth")
async def debug_auth(request: Request):
    """Return debug information about session cookie and API key validation."""
    info = {}

    # Check cookies
    session_cookie = request.cookies.get("__Secure-next-auth.session-token") or request.cookies.get("next-auth.session-token")
    info["session_cookie_present"] = bool(session_cookie)

    secret = os.environ.get("NEXTAUTH_SECRET")
    if not session_cookie:
        info["session_valid"] = False
        info["session_error"] = "no_cookie"
    else:
        if not secret:
            info["session_valid"] = False
            info["session_error"] = "no_nextauth_secret"
        else:
            try:
                payload = jwt.decode(session_cookie, secret, algorithms=["HS256"])
                info["session_valid"] = True
                info["session_payload_keys"] = list(payload.keys())
            except Exception as e:
                info["session_valid"] = False
                info["session_error"] = str(e)

    # Check API key
    api_key = request.headers.get("x-api-key")
    expected = os.environ.get("API_KEY", "dev-secret-api-key")
    info["api_key_provided"] = bool(api_key)
    info["api_key_value"] = api_key
    info["api_key_expected"] = expected
    info["api_key_valid"] = (api_key == expected)

    return info
