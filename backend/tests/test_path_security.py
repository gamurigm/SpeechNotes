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


def test_sanitize_filename_handles_empty_string() -> None:
    """Empty string should return a fallback name, not crash."""
    result = sanitize_filename("")
    assert isinstance(result, str)
    assert len(result) > 0


def test_sanitize_filename_handles_only_special_chars() -> None:
    result = sanitize_filename("../../../")
    assert "/" not in result
    assert "\\" not in result


def test_sanitize_filename_preserves_normal_name() -> None:
    assert sanitize_filename("normal-file.wav") == "normal-file.wav"


def test_sanitize_filename_removes_html_tags() -> None:
    assert "<" not in sanitize_filename("<script>alert</script>.wav")
    assert ">" not in sanitize_filename("<script>alert</script>.wav")


def test_path_within_with_same_directory(tmp_path: Path) -> None:
    """A file directly in the allowed directory should be valid."""
    child = tmp_path / "safe.md"
    result = path_within(tmp_path, "safe.md")
    assert result == child.resolve()


def test_path_within_with_deeply_nested_path(tmp_path: Path) -> None:
    nested = tmp_path / "a" / "b" / "c" / "deep.md"
    nested.parent.mkdir(parents=True)
    result = path_within(tmp_path, "a/b/c/deep.md")
    assert result == nested.resolve()
