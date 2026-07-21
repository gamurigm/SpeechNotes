"""
http_client.py - Thin wrapper around requests.Session for backend integration tests.

Centralises:
    * Base URL handling
    * Default headers (x-api-key, Accept, Content-Type)
    * Timeout enforcement
    * Optional verbose logging of every request/response
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Optional

import requests


DEFAULT_TIMEOUT = 10
DEBUG = os.environ.get("PYTEST_DEBUG_HTTP") == "1"


class BackendHttpClient:
    """Pre-configured HTTP client targeting the SpeechNotes backend."""

    def __init__(self, base_url: str, api_key: str, timeout: int = DEFAULT_TIMEOUT):
        # Strip trailing slash to make urljoin predictable
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "x-api-key": api_key,
            }
        )

    def _url(self, path: str) -> str:
        if not path.startswith("/"):
            path = "/" + path
        return f"{self.base_url}{path}"

    def _log(self, method: str, url: str, response: Optional[requests.Response] = None, exc: Optional[Exception] = None) -> None:
        if not DEBUG:
            return
        ts = time.strftime("%H:%M:%S")
        if exc is not None:
            print(f"[{ts}] {method} {url} -> ERROR: {exc}")
            return
        if response is not None:
            body_preview = ""
            try:
                body_preview = json.dumps(response.json())[:200]
            except Exception:
                body_preview = (response.text or "")[:200]
            print(f"[{ts}] {method} {url} -> {response.status_code} | {body_preview}")

    # ── HTTP verb wrappers ───────────────────────────────────────────────

    def get(self, path: str, params: Optional[dict] = None, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.get(url, params=params, **kwargs)
        except Exception as exc:
            self._log("GET", url, exc=exc)
            raise
        self._log("GET", url, response=resp)
        return resp

    def post(self, path: str, json_body: Optional[dict] = None, data: Any = None, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.post(url, json=json_body, data=data, **kwargs)
        except Exception as exc:
            self._log("POST", url, exc=exc)
            raise
        self._log("POST", url, response=resp)
        return resp

    def put(self, path: str, json_body: Optional[dict] = None, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.put(url, json=json_body, **kwargs)
        except Exception as exc:
            self._log("PUT", url, exc=exc)
            raise
        self._log("PUT", url, response=resp)
        return resp

    def delete(self, path: str, **kwargs) -> requests.Response:
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        try:
            resp = self.session.delete(url, **kwargs)
        except Exception as exc:
            self._log("DELETE", url, exc=exc)
            raise
        self._log("DELETE", url, response=resp)
        return resp

    def get_with_headers(self, path: str, headers: dict, **kwargs) -> requests.Response:
        """GET with custom headers (used by auth tests)."""
        url = self._url(path)
        kwargs.setdefault("timeout", self.timeout)
        merged = {**self.session.headers, **headers}
        resp = requests.get(url, headers=merged, **kwargs)
        self._log("GET", url, response=resp)
        return resp
