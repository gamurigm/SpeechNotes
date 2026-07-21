"""Utilities for safely handling externally supplied file names and paths."""

from __future__ import annotations

import re
from pathlib import Path


_UNSAFE_FILENAME_CHARS = re.compile(r"[^\w. -]", flags=re.UNICODE)
_REPEATED_WHITESPACE = re.compile(r"\s+")


def sanitize_filename(value: str | None, fallback: str = "upload") -> str:
    """Return a display-safe basename without directory or control characters."""
    raw_value = (value or "").replace("\\", "/")
    basename = raw_value.rsplit("/", maxsplit=1)[-1]
    basename = _REPEATED_WHITESPACE.sub(" ", basename).strip()
    basename = _UNSAFE_FILENAME_CHARS.sub("_", basename).strip(" .")

    if not basename or basename in {".", ".."}:
        basename = fallback

    return basename[:128]


def path_within(root: Path, filename: str) -> Path:
    """Build a path and reject any result that escapes ``root``."""
    resolved_root = root.resolve()
    candidate = (resolved_root / filename).resolve()
    try:
        candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("The requested path escapes the allowed directory") from exc
    return candidate


def validate_path_within(root: Path, candidate: Path) -> Path:
    """Validate an existing or generated path against an allowed root."""
    resolved_root = root.resolve()
    resolved_candidate = candidate.resolve()
    try:
        resolved_candidate.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError("The requested path escapes the allowed directory") from exc
    return resolved_candidate
