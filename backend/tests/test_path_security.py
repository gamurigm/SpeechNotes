"""Unit tests for path traversal protections used by upload and output flows."""

import importlib.util
from pathlib import Path

import pytest


# Load this leaf module directly so these security unit tests do not require the
# optional NVIDIA Riva runtime imported by ``src.__init__``.
MODULE_PATH = Path(__file__).resolve().parents[2] / "src" / "core" / "path_security.py"
SPEC = importlib.util.spec_from_file_location("path_security", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
path_security = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(path_security)

path_within = path_security.path_within
sanitize_filename = path_security.sanitize_filename
validate_path_within = path_security.validate_path_within


def test_sanitize_filename_removes_directory_components() -> None:
    assert sanitize_filename("../../private/recording.wav") == "recording.wav"
    assert sanitize_filename(r"..\..\private\recording.wav") == "recording.wav"
    assert sanitize_filename("recording<script>.wav") == "recording_script_.wav"


def test_path_within_rejects_parent_traversal(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="escapes the allowed directory"):
        path_within(tmp_path, "../outside.md")


def test_validate_path_within_accepts_child_and_rejects_outside(tmp_path: Path) -> None:
    child = tmp_path / "notes" / "safe.md"
    child.parent.mkdir()

    assert validate_path_within(tmp_path, child) == child.resolve()

    with pytest.raises(ValueError, match="escapes the allowed directory"):
        validate_path_within(tmp_path, tmp_path.parent / "outside.md")
