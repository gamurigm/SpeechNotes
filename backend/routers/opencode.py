"""Authenticated, loopback-only terminal sessions. No generic shell endpoint."""

import asyncio
from contextlib import suppress
from dataclasses import dataclass
import os
import secrets
import time

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from backend.services.audio.transcription_service import TranscriptionService
from backend.services.opencode_terminal import DocumentWorkspace, close_process, find_opencode, spawn_opencode, workspace_root

router = APIRouter()


def allowed_origins():
    port = int(os.environ.get("FRONTEND_PORT", "3006"))
    return {f"http://localhost:{port}", f"http://127.0.0.1:{port}"}


async def terminal_user(request: Request):
    # Do not inherit the API's development-key bypass for process execution.
    if request.headers.get("origin") not in allowed_origins():
        raise HTTPException(403, "Origen de terminal no permitido.")
    if request.client is None or request.client.host not in {"127.0.0.1", "::1"}:
        raise HTTPException(403, "La terminal solo está disponible localmente.")
    cookie = request.headers.get("cookie", "")
    if not cookie:
        raise HTTPException(401, "Inicia sesión para abrir OpenCode.")
    try:
        port = int(os.environ.get("FRONTEND_PORT", "3006"))
        async with httpx.AsyncClient(trust_env=False) as client:
            response = await client.get(f"http://127.0.0.1:{port}/api/auth/session", headers={"cookie": cookie}, timeout=5)
        user = response.json().get("user", {}) if response.status_code == 200 else {}
        owner = user.get("id") or user.get("email")
        if not owner:
            raise ValueError("missing user")
        return str(owner)
    except (httpx.HTTPError, ValueError, AttributeError):
        raise HTTPException(401, "La sesión expiró. Vuelve a iniciar sesión.") from None


class StartTerminal(BaseModel):
    doc_id: str = Field(min_length=1, max_length=128)


@dataclass
class TerminalSession:
    owner: str
    token: str
    workspace: DocumentWorkspace
    expires: float
    connected: bool = False
    process: object = None


sessions: dict[str, TerminalSession] = {}


@router.post("/sessions")
async def create_session(body: StartTerminal, owner: str = Depends(terminal_user)):
    for sid, session in list(sessions.items()):
        if not session.connected and session.expires < time.monotonic():
            sessions.pop(sid, None)
    if len(sessions) >= 4 or any(s.workspace.doc_id == body.doc_id for s in sessions.values()):
        raise HTTPException(409, "Ya hay una terminal para esta nota. Ciérrala antes de iniciar otra.")
    service = TranscriptionService()
    raw = service.repo.get_by_id(body.doc_id)
    if not raw or raw.get("is_deleted"):
        raise HTTPException(404, "Nota no encontrada.")
    try:
        find_opencode()
        import winpty  # noqa: F401 - readiness check before allocating a session
    except (FileNotFoundError, ImportError) as exc:
        raise HTTPException(503, "Instala OpenCode y la dependencia pywinpty del backend para abrir la terminal.") from exc
    doc = service.get_by_id(body.doc_id)
    sid, token = secrets.token_hex(16), secrets.token_urlsafe(32)
    workspace = DocumentWorkspace(workspace_root() / sid, body.doc_id, doc["content"], service)
    sessions[sid] = TerminalSession(owner, token, workspace, time.monotonic() + 30)
    return {"id": sid, "token": token, "workspace": str(workspace.root), "filename": doc.get("filename")}


@router.delete("/sessions/{sid}")
async def stop_session(sid: str, owner: str = Depends(terminal_user)):
    session = sessions.get(sid)
    if session and session.owner == owner:
        close_process(session.process)
        sessions.pop(sid, None)
    return {"status": "closed"}


@router.websocket("/sessions/{sid}/ws")
async def terminal_socket(websocket: WebSocket, sid: str):
    session = sessions.get(sid)
    if (websocket.headers.get("origin") not in allowed_origins()
            or websocket.client is None or websocket.client.host not in {"127.0.0.1", "::1"}
            or session is None or session.connected or session.expires < time.monotonic()):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    tasks = []
    authenticated = False
    try:
        # Ticket travels in the first frame, never in URLs/access logs.
        hello = await asyncio.wait_for(websocket.receive_json(), 5)
        if not isinstance(hello, dict) or not secrets.compare_digest(str(hello.get("token", "")), session.token):
            await websocket.close(code=1008)
            return
        authenticated = True
        session.connected = True
        session.token = ""
        cols = max(20, min(300, int(hello.get("cols", 80))))
        rows = max(5, min(120, int(hello.get("rows", 24))))
        session.process = await asyncio.to_thread(spawn_opencode, session.workspace.root, rows, cols)
        send_lock = asyncio.Lock()

        async def send(payload):
            async with send_lock:
                await websocket.send_json(payload)

        async def output():
            while True:
                try:
                    data = await asyncio.to_thread(session.process.read, 32768)
                except (EOFError, OSError):
                    break
                if data:
                    await send({"type": "output", "data": data})

        async def inputs():
            while True:
                payload = await websocket.receive_json()
                if not isinstance(payload, dict):
                    continue
                if payload.get("type") == "input":
                    data = payload.get("data", "")
                    if isinstance(data, str) and len(data) <= 65536:
                        session.process.write(data)
                elif payload.get("type") == "resize":
                    session.process.setwinsize(max(5, min(120, int(payload["rows"]))), max(20, min(300, int(payload["cols"]))))
                elif payload.get("type") == "stop":
                    return

        async def documents():
            while True:
                await asyncio.sleep(0.8)
                try:
                    event = session.workspace.sync()
                    if event:
                        await send(event)
                except (OSError, UnicodeError, ValueError) as exc:
                    await send({"type": "conflict", "message": str(exc)})
                    return

        await send({"type": "ready"})
        tasks = [asyncio.create_task(output()), asyncio.create_task(inputs()), asyncio.create_task(documents())]
        done, _ = await asyncio.wait(tasks[:2], return_when=asyncio.FIRST_COMPLETED)
        for task in done:
            task.result()
    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception:
        with suppress(Exception):
            await websocket.send_json({"type": "error", "message": "No se pudo iniciar o mantener OpenCode. Revisa su instalación y vuelve a abrir la terminal."})
    finally:
        if authenticated:
            close_process(session.process)
            for task in tasks:
                task.cancel()
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            with suppress(Exception):
                event = session.workspace.sync(final=True)
                if event:
                    await websocket.send_json(event)
            sessions.pop(sid, None)
        with suppress(Exception):
            await websocket.close()


def close_all_sessions():
    for session in list(sessions.values()):
        close_process(session.process)
    sessions.clear()
