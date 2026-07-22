import asyncio
from types import SimpleNamespace
from unittest.mock import MagicMock

import backend.routers.debug as debug


def _request(cookie=None, api_key=None):
    cookies = {"next-auth.session-token": cookie} if cookie else {}
    headers = {"x-api-key": api_key} if api_key else {}
    return SimpleNamespace(cookies=cookies, headers=headers)


def test_debug_auth_reports_missing_cookie_and_api_key(monkeypatch):
    monkeypatch.delenv("NEXTAUTH_SECRET", raising=False)
    monkeypatch.setenv("API_KEY", "expected")

    result = asyncio.run(debug.debug_auth(_request()))

    assert result == {
        "session_cookie_present": False,
        "session_valid": False,
        "session_error": "no_cookie",
        "api_key_provided": False,
        "api_key_value": None,
        "api_key_expected": "expected",
        "api_key_valid": False,
    }


def test_debug_auth_reports_missing_secret(monkeypatch):
    monkeypatch.delenv("NEXTAUTH_SECRET", raising=False)

    result = asyncio.run(debug.debug_auth(_request(cookie="token")))

    assert result["session_cookie_present"] is True
    assert result["session_valid"] is False
    assert result["session_error"] == "no_nextauth_secret"


def test_debug_auth_reports_valid_session_and_key(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", "secret")
    monkeypatch.setenv("API_KEY", "api-key")
    monkeypatch.setattr(debug.jwt, "decode", MagicMock(return_value={"sub": "user", "iat": 1}))

    result = asyncio.run(debug.debug_auth(_request(cookie="token", api_key="api-key")))

    assert result["session_valid"] is True
    assert result["session_payload_keys"] == ["sub", "iat"]
    assert result["api_key_valid"] is True
    debug.jwt.decode.assert_called_once_with("token", "secret", algorithms=["HS256"])


def test_debug_auth_reports_decode_error(monkeypatch):
    monkeypatch.setenv("NEXTAUTH_SECRET", "secret")
    monkeypatch.setattr(debug.jwt, "decode", MagicMock(side_effect=ValueError("bad token")))

    result = asyncio.run(debug.debug_auth(_request(cookie="token")))

    assert result["session_valid"] is False
    assert result["session_error"] == "bad token"
