"""Local OpenCode PTY and a Markdown bridge to transcription storage."""

import json
import os
from pathlib import Path
import shutil
import subprocess
import time

MAX_DOCUMENT_BYTES = 4 * 1024 * 1024


class DocumentWorkspace:
    def __init__(self, root: Path, doc_id: str, content: str, service):
        self.root = root.resolve()
        self.doc_id = doc_id
        self.service = service
        self.baseline = content
        self.pending = None
        self.pending_since = 0.0
        self.last_conflict = None
        self.path = self.root / "document.md"
        self.root.mkdir(parents=True, exist_ok=False)
        self.path.write_text(content, encoding="utf-8")
        (self.root / "original.md").write_text(content, encoding="utf-8")
        (self.root / "AGENTS.md").write_text(
            "# SpeechNotes\n\nEdita document.md según las instrucciones del usuario. "
            "Responde en español. No inventes información ausente en la nota. "
            "Los cambios de document.md se sincronizan con el visor de SpeechNotes. "
            "original.md es una copia de recuperación; no la modifiques.\n",
            encoding="utf-8",
        )
        (self.root / "opencode.json").write_text(json.dumps({
            "$schema": "https://opencode.ai/config.json",
            "permission": {
                "edit": {"*": "deny", "document.md": "allow"},
                "bash": "ask",
                "external_directory": "deny",
            },
        }), encoding="utf-8")

    def sync(self, *, final=False):
        # Reject symlinks/junction replacements and oversized writes.
        if self.path.resolve() != self.path or self.path.stat().st_size > MAX_DOCUMENT_BYTES:
            raise ValueError("El borrador debe ser un Markdown local de hasta 4 MB.")
        content = self.path.read_text(encoding="utf-8-sig")
        if content == self.baseline:
            self.pending = None
            return None
        if not final and (content != self.pending or time.monotonic() - self.pending_since < 0.7):
            if content != self.pending:
                self.pending, self.pending_since = content, time.monotonic()
            return None
        raw = self.service.repo.get_by_id(self.doc_id)
        if not raw or raw.get("is_deleted"):
            raise ValueError("La nota fue eliminada. El borrador se conserva en la carpeta de la terminal.")
        current = self.service.get_by_id(self.doc_id)["content"]
        if current != self.baseline and current != content:
            if self.last_conflict == content:
                return None
            self.last_conflict = content
            return {"type": "conflict", "message": "La nota cambió fuera de OpenCode. El borrador se conserva sin reemplazar esos cambios."}
        if current != content and not self.service.update_content(self.doc_id, content):
            raise ValueError("No se pudo guardar la nota.")
        self.baseline = content
        self.pending = None
        return {"type": "document", "doc_id": self.doc_id, "content": content}


def workspace_root() -> Path:
    base = os.environ.get("LOCALAPPDATA") or os.environ.get("XDG_DATA_HOME")
    return (Path(base) if base else Path.home() / ".local" / "share") / "SpeechNotes" / "opencode"


def find_opencode() -> str:
    executable = shutil.which("opencode.exe") or shutil.which("opencode.cmd") or shutil.which("opencode")
    if not executable:
        raise FileNotFoundError("OpenCode no está instalado o no está disponible en PATH.")
    return executable


def spawn_opencode(workspace: Path, rows: int, cols: int):
    if os.name != "nt":
        raise RuntimeError("Esta integración de terminal requiere Windows (ConPTY).")
    from winpty import PtyProcess
    executable = find_opencode()
    # Keep application .env secrets out of the terminal; OpenCode uses its own
    # user credentials/configuration. Launch only the resolved CLI, never a
    # command or working directory supplied by the renderer.
    system_keys = {
        "PATH", "PATHEXT", "SYSTEMROOT", "WINDIR", "COMSPEC", "USERPROFILE",
        "APPDATA", "LOCALAPPDATA", "TEMP", "TMP", "HOMEDRIVE", "HOMEPATH",
        "PROGRAMFILES", "PROGRAMFILES(X86)", "PROGRAMDATA", "OS",
        "PROCESSOR_ARCHITECTURE", "NUMBER_OF_PROCESSORS", "USERNAME",
    }
    env = {k: v for k, v in os.environ.items() if k.upper() in system_keys}
    env.update({"TERM": "xterm-256color", "COLORTERM": "truecolor"})
    if executable.lower().endswith((".cmd", ".bat")):
        command = [os.environ.get("COMSPEC", "cmd.exe"), "/d", "/c", executable]
    else:
        command = [executable]
    return PtyProcess.spawn(command, cwd=str(workspace), env=env, dimensions=(rows, cols))


def close_process(process):
    if process is not None:
        try:
            # OpenCode's npm launcher creates child processes. Stop this PTY's
            # complete tree rather than leaving the agent behind its cmd host.
            if os.name == "nt" and process.isalive():
                subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               creationflags=subprocess.CREATE_NO_WINDOW, timeout=5)
        except (OSError, EOFError, subprocess.TimeoutExpired):
            pass
        finally:
            try:
                process.close(force=True)
            except (OSError, EOFError):
                pass
