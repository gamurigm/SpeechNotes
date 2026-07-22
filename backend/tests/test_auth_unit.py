import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import HTTPException

import backend.utils.auth as auth


def _request(token=None, cookie_header=None):
    cookies = {"next-auth.session-token": token} if token else {}
    headers = {"cookie": cookie_header} if cookie_header else {}
    return SimpleNamespace(cookies=cookies, headers=headers)


class FakeAsyncClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.get = AsyncMock(side_effect=error, return_value=response)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        return False


def test_mask_handles_empty_short_and_long_values():
    assert auth._mask(None) == "(none)"
    assert auth._mask("short") == "short"
    assert auth._mask("1234567890") == "1234...7890"


def test_require_api_key_accepts_header_and_bearer(monkeypatch):
    monkeypatch.setattr(auth._cfg, "get", lambda *_args: "secret-key")

    assert asyncio.run(auth.require_api_key("secret-key", None)) is True
    assert asyncio.run(auth.require_api_key(None, "Bearer secret-key")) is True
    assert asyncio.run(auth.require_api_key("dev-secret-api-key", None)) is True


def test_require_api_key_rejects_missing_or_invalid(monkeypatch):
    monkeypatch.setattr(auth._cfg, "get", lambda *_args: "expected-key")

    with pytest.raises(HTTPException) as missing:
        asyncio.run(auth.require_api_key(None, "Basic value"))
    assert missing.value.status_code == 401

    with pytest.raises(HTTPException) as invalid:
        asyncio.run(auth.require_api_key("wrong-key", None))
    assert invalid.value.status_code == 403


def test_require_session_requires_cookie():
    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_session(_request()))
    assert exc.value.status_code == 401


def test_require_session_accepts_nextjs_session(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.return_value = {"user": {"email": "qa@example.com"}}
    client = FakeAsyncClient(response=response)
    monkeypatch.setattr(auth.httpx, "AsyncClient", MagicMock(return_value=client))
    monkeypatch.setattr(
        auth._cfg,
        "get",
        lambda key, default="": "http://frontend/api/auth/session"
        if key == "NEXTJS_SESSION_URL"
        else default,
    )

    result = asyncio.run(auth.require_session(_request("token", "cookie=value")))

    assert result["user"]["email"] == "qa@example.com"
    client.get.assert_awaited_once_with(
        "http://frontend/api/auth/session",
        headers={"accept": "application/json", "cookie": "cookie=value"},
        timeout=5.0,
    )


def test_require_session_falls_back_to_local_jwt(monkeypatch):
    response = MagicMock(status_code=503)
    monkeypatch.setattr(
        auth.httpx, "AsyncClient", MagicMock(return_value=FakeAsyncClient(response=response))
    )
    monkeypatch.setattr(
        auth._cfg,
        "get",
        lambda key, default="": "jwt-secret" if key == "NEXTAUTH_SECRET" else default,
    )
    monkeypatch.setattr(auth.jwt, "decode", MagicMock(return_value={"sub": "user-1"}))

    assert asyncio.run(auth.require_session(_request("token"))) == {"sub": "user-1"}
    auth.jwt.decode.assert_called_once_with("token", "jwt-secret", algorithms=["HS256"])


def test_require_session_handles_invalid_nextjs_json_and_missing_secret(monkeypatch):
    response = MagicMock(status_code=200)
    response.json.side_effect = ValueError("invalid json")
    monkeypatch.setattr(
        auth.httpx, "AsyncClient", MagicMock(return_value=FakeAsyncClient(response=response))
    )
    monkeypatch.setattr(auth._cfg, "get", lambda _key, default="": default)

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_session(_request("token")))
    assert exc.value.status_code == 500


@pytest.mark.parametrize(
    ("error", "detail"),
    [
        (jwt.ExpiredSignatureError(), "Session expired"),
        (ValueError("bad token"), "Invalid session token"),
    ],
)
def test_require_session_maps_jwt_errors(monkeypatch, error, detail):
    monkeypatch.setattr(
        auth.httpx,
        "AsyncClient",
        MagicMock(return_value=FakeAsyncClient(error=RuntimeError("frontend unavailable"))),
    )
    monkeypatch.setattr(
        auth._cfg,
        "get",
        lambda key, default="": "jwt-secret" if key == "NEXTAUTH_SECRET" else default,
    )
    monkeypatch.setattr(auth.jwt, "decode", MagicMock(side_effect=error))

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_session(_request("token")))
    assert exc.value.detail == detail


def test_require_auth_bypasses_auth_for_default_dev_key(monkeypatch):
    monkeypatch.setattr(auth._cfg, "get", lambda *_args: "dev-secret-api-key")
    monkeypatch.setattr(auth, "require_session", AsyncMock())

    assert asyncio.run(auth.require_auth(_request())) is True
    auth.require_session.assert_not_awaited()


def test_require_auth_prefers_session_then_falls_back_to_api_key(monkeypatch):
    monkeypatch.setattr(auth._cfg, "get", lambda *_args: "production-key")
    monkeypatch.setattr(auth, "require_session", AsyncMock(return_value={"user": "qa"}))
    monkeypatch.setattr(auth, "require_api_key", AsyncMock(return_value=True))

    assert asyncio.run(auth.require_auth(_request())) is True
    auth.require_api_key.assert_not_awaited()

    auth.require_session = AsyncMock(side_effect=HTTPException(401, "no session"))
    assert asyncio.run(auth.require_auth(_request(), "production-key", None)) is True
    auth.require_api_key.assert_awaited_once_with("production-key", None)


def test_require_auth_propagates_api_key_failure(monkeypatch):
    monkeypatch.setattr(auth._cfg, "get", lambda *_args: "production-key")
    monkeypatch.setattr(
        auth, "require_session", AsyncMock(side_effect=HTTPException(401, "no session"))
    )
    monkeypatch.setattr(
        auth, "require_api_key", AsyncMock(side_effect=HTTPException(403, "bad key"))
    )

    with pytest.raises(HTTPException) as exc:
        asyncio.run(auth.require_auth(_request(), "bad", None))
    assert exc.value.status_code == 403
