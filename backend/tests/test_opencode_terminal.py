from types import SimpleNamespace
from queue import Queue

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.services.opencode_terminal import DocumentWorkspace
from backend.services.knowledge.content_renderer import ContentRenderer
from backend.routers import opencode


class Notes:
    def __init__(self, content):
        self.content = content
        self.deleted = False
        self.saved = []
        self.repo = self

    def get_by_id(self, doc_id):
        return {"content": self.content, "is_deleted": self.deleted}

    def update_content(self, doc_id, content):
        self.content = content
        self.saved.append(content)
        return True


def test_opencode_edit_roundtrips_without_touching_backup(tmp_path):
    notes = Notes("# Clase\nOriginal")
    workspace = DocumentWorkspace(tmp_path / "session", "note-1", notes.content, notes)
    workspace.path.write_text("# Clase\nEditada por OpenCode", encoding="utf-8")
    event = workspace.sync(final=True)
    assert event == {"type": "document", "doc_id": "note-1", "content": notes.content}
    assert notes.content.endswith("Editada por OpenCode")
    assert (workspace.root / "original.md").read_text(encoding="utf-8") == "# Clase\nOriginal"
    assert workspace.sync(final=True) is None


def test_manual_edit_conflict_keeps_both_versions(tmp_path):
    notes = Notes("Original")
    workspace = DocumentWorkspace(tmp_path / "session", "note-1", notes.content, notes)
    notes.content = "Cambio en el visor"
    workspace.path.write_text("Borrador de OpenCode", encoding="utf-8")
    assert workspace.sync(final=True)["type"] == "conflict"
    assert notes.saved == []
    assert notes.content == "Cambio en el visor"
    assert workspace.path.read_text(encoding="utf-8") == "Borrador de OpenCode"


def test_deleted_note_is_not_recreated(tmp_path):
    notes = Notes("Original")
    workspace = DocumentWorkspace(tmp_path / "session", "note-1", notes.content, notes)
    notes.deleted = True
    workspace.path.write_text("Nueva", encoding="utf-8")
    with pytest.raises(ValueError, match="eliminada"):
        workspace.sync(final=True)
    assert notes.saved == []


def test_partial_writes_are_debounced(tmp_path, monkeypatch):
    notes = Notes("Original")
    workspace = DocumentWorkspace(tmp_path / "session", "note-1", notes.content, notes)
    workspace.path.write_text("Edición", encoding="utf-8")
    monkeypatch.setattr("backend.services.opencode_terminal.time.monotonic", lambda: 10.0)
    assert workspace.sync() is None
    monkeypatch.setattr("backend.services.opencode_terminal.time.monotonic", lambda: 10.8)
    assert workspace.sync()["type"] == "document"


def test_edited_content_takes_priority_over_formatted_content():
    renderer = object.__new__(ContentRenderer)
    assert renderer.render_transcription({"edited_content": "Editada", "formatted_content": "Antigua", "is_formatted": True}, []) == "Editada"
    assert renderer.render_transcription({"edited_content": ""}, []) == ""


@pytest.fixture
def client():
    app = FastAPI()
    app.include_router(opencode.router, prefix="/api/opencode")
    opencode.sessions.clear()
    with TestClient(app, client=("127.0.0.1", 50000)) as client:
        yield client
    opencode.close_all_sessions()


def test_development_api_key_cannot_start_a_process(client):
    response = client.post("/api/opencode/sessions", json={"doc_id": "note-1"}, headers={"origin": "http://localhost:3006", "x-api-key": "dev-secret-api-key"})
    assert response.status_code == 401
    assert opencode.sessions == {}


def test_untrusted_origin_rejected_before_authentication(client):
    response = client.post("/api/opencode/sessions", json={"doc_id": "note-1"}, headers={"origin": "https://example.org"})
    assert response.status_code == 403


def test_websocket_requires_single_use_ticket(client, monkeypatch):
    session = opencode.TerminalSession("owner", "valid-ticket", SimpleNamespace(), float("inf"))
    opencode.sessions["test"] = session
    spawned = []
    monkeypatch.setattr(opencode, "spawn_opencode", lambda *args: spawned.append(args))
    with client.websocket_connect("/api/opencode/sessions/test/ws", headers={"origin": "http://localhost:3006"}) as ws:
        ws.send_json({"token": "wrong-ticket"})
        assert ws.receive()["code"] == 1008
    assert not spawned
    assert not session.connected
    opencode.sessions.clear()


def test_authenticated_terminal_saves_final_edit_and_stops(client, monkeypatch, tmp_path):
    notes = Notes("Original")
    workspace = DocumentWorkspace(tmp_path / "session", "note-1", notes.content, notes)
    output = Queue()
    output.put("OpenCode")
    process = SimpleNamespace(read=lambda size: output.get(), write=lambda data: None)
    stopped = []
    def close(pty):
        stopped.append(pty)
        output.put("")
    monkeypatch.setattr(opencode, "spawn_opencode", lambda *args: process)
    monkeypatch.setattr(opencode, "close_process", close)
    opencode.sessions["test"] = opencode.TerminalSession("owner", "ticket", workspace, float("inf"))
    with client.websocket_connect("/api/opencode/sessions/test/ws", headers={"origin": "http://localhost:3006"}) as ws:
        ws.send_json({"token": "ticket", "cols": 100, "rows": 30})
        assert ws.receive_json()["type"] == "ready"
        assert ws.receive_json() == {"type": "output", "data": "OpenCode"}
        workspace.path.write_text("Editada", encoding="utf-8")
        ws.send_json({"type": "stop"})
        assert ws.receive_json() == {"type": "document", "doc_id": "note-1", "content": "Editada"}
    assert notes.content == "Editada"
    assert stopped == [process]
    assert not opencode.sessions
