#!/usr/bin/env python3
"""High-confidence secret scan for tracked repository files."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_ENV_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
}
SENSITIVE_SUFFIXES = {".pem", ".p12", ".pfx", ".key"}
BINARY_SUFFIXES = {
    ".db",
    ".gif",
    ".ico",
    ".jpeg",
    ".jpg",
    ".pdf",
    ".png",
    ".sqlite",
    ".webp",
}
ALLOWLIST_FRAGMENTS = {
    "dev-secret-api-key",
    "e2e-test-secret",
    "demo123",
    "sk-test",
    "sk-example",
    "AKIAIOSFODNN7EXAMPLE",
}
SECRET_PATTERNS = {
    "private key block": re.compile(r"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----"),
    "aws access key": re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    "github token": re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}\b|\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    "openai api key": re.compile(r"\bsk-[A-Za-z0-9_-]{32,}\b"),
    "nvidia api key": re.compile(r"\bnvapi-[A-Za-z0-9_-]{32,}\b"),
    "slack token": re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b"),
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    return [ROOT / entry.decode("utf-8") for entry in result.stdout.split(b"\0") if entry]


def is_sensitive_filename(path: Path) -> bool:
    name = path.name.lower()
    if name in SENSITIVE_ENV_NAMES:
        return True
    if name.startswith(".env.") and not name.endswith(('.example', '.sample', '.template')):
        return True
    return path.suffix.lower() in SENSITIVE_SUFFIXES


def read_text(path: Path) -> str | None:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return None
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None


def allowed(line: str) -> bool:
    return any(fragment in line for fragment in ALLOWLIST_FRAGMENTS)


def main() -> int:
    findings: list[str] = []

    for path in tracked_files():
        rel = path.relative_to(ROOT).as_posix()
        if is_sensitive_filename(path):
            findings.append(f"{rel}: tracked sensitive filename")
            continue

        text = read_text(path)
        if text is None:
            continue

        for line_number, line in enumerate(text.splitlines(), start=1):
            if allowed(line):
                continue
            for label, pattern in SECRET_PATTERNS.items():
                if pattern.search(line):
                    findings.append(f"{rel}:{line_number}: possible {label}")

    if findings:
        print("Security scan failed. Review these high-confidence secret findings:")
        for finding in findings:
            print(f"- {finding}")
        return 1

    print("Security scan passed: no tracked secrets or sensitive files detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())