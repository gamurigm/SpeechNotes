"""
App Configuration Service
Stores and retrieves API keys and settings from a local SQLite database.
Replaces direct os.getenv() calls for all configurable values.

Keys are stored in an 'app_settings' table. In the Electron desktop app,
values will be encrypted via safeStorage before being written here.
For development, plain-text fallback from .env is supported.
"""

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_CONFIG_SCHEMA = """
CREATE TABLE IF NOT EXISTS app_settings (
    key       TEXT PRIMARY KEY,
    value     TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT 'general',
    label     TEXT,
    required  INTEGER DEFAULT 0,
    secret    INTEGER DEFAULT 1       -- 1 = should be masked in UI
);
"""

# Default configuration entries (category, key, label, required, secret, env_fallback)
_DEFAULTS: List[tuple] = [
    # ---- LLM / Inference --------------------------------------------------
    ("llm", "NVIDIA_API_KEY",           "NVIDIA API Key (Principal)",    1, 1),
    ("llm", "NVIDIA_API_KEY_THINKING",  "NVIDIA API Key (Thinking)",     1, 1),
    ("llm", "NVIDIA_API_KEY_FAST",      "NVIDIA API Key (Fast)",         1, 1),
    ("llm", "NVIDIA_EMBEDDING_API_KEY", "NVIDIA Embedding API Key",      1, 1),
    ("llm", "MINIMAX_API_KEY",          "Minimax API Key",               1, 1),
    ("llm", "NVIDIA_BASE_URL",          "NVIDIA Base URL",               0, 0),
    ("llm", "MINIMAX_BASE_URL",         "Minimax Base URL",              0, 0),
    # ---- NIM Specialised Keys ---------------------------------------------
    ("llm", "NVIDIA_API_KEY_ASR",       "NVIDIA API Key (ASR / Parakeet)",   1, 1),
    ("llm", "NVIDIA_API_KEY_BNR",       "NVIDIA API Key (BNR gRPC)",         0, 1),
    ("llm", "NVIDIA_API_KEY_DETECTOR",  "NVIDIA API Key (Lang Detect / Gemma)", 1, 1),
    ("llm", "NVIDIA_API_KEY_TRANSLATOR","NVIDIA API Key (Translation / Mistral)", 1, 1),
    # ---- Models -----------------------------------------------------------
    ("models", "CHAT_MODEL_THINKING",   "Chat Model (Thinking)",         0, 0),
    ("models", "CHAT_MODEL_FAST",       "Chat Model (Fast)",             0, 0),
    ("models", "FORMATTER_MODEL",       "Formatter Model",               0, 0),
    ("models", "EMBEDDING_MODEL",       "Embedding Model",               0, 0),
    ("models", "MINIMAX_MODEL_NAME",    "Minimax Model Name",            0, 0),
    ("models", "MODEL_NAME",            "Default Model Name",            0, 0),
    # NIM specialised models
    ("models", "ASR_MODEL",             "ASR Model (Parakeet)",          0, 0),
    ("models", "DETECTOR_MODEL",        "Language Detector Model",       0, 0),
    ("models", "TRANSLATOR_MODEL",      "Translator Model (Mistral)",    0, 0),
    ("models", "BNR_FUNCTION_ID",       "BNR NVCF Function ID",          0, 0),
    ("models", "BNR_GRPC_HOST",         "BNR gRPC Host",                 0, 0),
    ("models", "BNR_GRPC_PORT",         "BNR gRPC Port",                 0, 0),
    # ---- Model parameters -------------------------------------------------
    ("models", "TEMPERATURE",           "Temperature",                   0, 0),
    ("models", "TOP_P",                 "Top P",                         0, 0),
    ("models", "MAX_TOKENS",            "Max Tokens",                    0, 0),
    # ---- Voice / Riva -----------------------------------------------------
    ("voice", "NGC_API_KEY",            "NGC / Riva API Key",            1, 1),
    ("voice", "API_KEY",                "Backend Auth API Key",          1, 1),
    ("voice", "canary_api",             "Canary API Key",                0, 1),
    ("voice", "RIVA_SERVER",            "Riva Server URL",               0, 0),
    ("voice", "RIVA_FUNCTION_ID_WHISPER", "Riva Whisper Function ID",   0, 0),
    # ---- Observability ----------------------------------------------------
    ("observability", "LOGFIRE_TOKEN",        "Logfire Token",           0, 1),
    ("observability", "LOGFIRE_PROJECT_NAME", "Logfire Project Name",    0, 0),
    # ---- Auth (OAuth) -----------------------------------------------------
    ("auth", "NEXTAUTH_SECRET",     "NextAuth Secret",                   1, 1),
    ("auth", "GOOGLE_CLIENT_ID",    "Google OAuth Client ID",            0, 1),
    ("auth", "GOOGLE_CLIENT_SECRET","Google OAuth Client Secret",        0, 1),
    ("auth", "GITHUB_ID",           "GitHub OAuth ID",                   0, 1),
    ("auth", "GITHUB_SECRET",       "GitHub OAuth Secret",               0, 1),
    # ---- Transcription pipeline -------------------------------------------
    ("pipeline", "TRANSCRIPTIONS_SOURCE_DIR",    "Source Dir (notas)",          0, 0),
    ("pipeline", "TRANSCRIPTIONS_PROCESSED_DIR", "Processed Dir",               0, 0),
    ("pipeline", "AUTO_INDEX_TRANSCRIPTIONS",    "Auto-Index Transcriptions",    0, 0),
    ("pipeline", "TRANSCRIPTION_CHUNK_SIZE",     "Chunk Size",                   0, 0),
    ("pipeline", "PRESERVE_ORIGINALS",           "Preserve Originals",           0, 0),
]


# ---------------------------------------------------------------------------
# ConfigService (Singleton)
# ---------------------------------------------------------------------------

class ConfigService:
    """
    Centralized configuration backed by SQLite.

    Usage::

        cfg = ConfigService()
        key = cfg.get("NVIDIA_API_KEY")
        cfg.set("NVIDIA_API_KEY", "nvapi-xxx")
    """

    _instance: Optional["ConfigService"] = None

    def __new__(cls) -> "ConfigService":
        if cls._instance is None:
            instance = super().__new__(cls)
            try:
                instance._initialize()
            except Exception:
                raise
            cls._instance = instance
        return cls._instance

    # ---- lifecycle --------------------------------------------------------

    def _initialize(self) -> None:
        db_dir = os.getenv("SQLITE_DB_DIR", "data")
        Path(db_dir).mkdir(parents=True, exist_ok=True)
        self._db_path = os.path.join(db_dir, "speechnotes.db")

        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(_CONFIG_SCHEMA)
        self._conn.commit()

        self._seed_defaults()
        print(f"[INFO] ConfigService ready ({self._db_path})")

    def _seed_defaults(self) -> None:
        """Insert default rows if they don't exist yet.

        On first run, copies values from .env so existing users keep
        their configuration seamlessly.
        """
        for category, key, label, required, secret in _DEFAULTS:
            existing = self._conn.execute(
                "SELECT 1 FROM app_settings WHERE key = ?", (key,)
            ).fetchone()
            if existing:
                continue

            # Seed from .env / environment
            env_value = os.getenv(key, "")
            self._conn.execute(
                "INSERT INTO app_settings (key, value, category, label, required, secret) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (key, env_value, category, label, required, secret),
            )
        self._conn.commit()

    # ---- public API -------------------------------------------------------

    def get(self, key: str, default: str = "") -> str:
        """Return the value for *key*, falling back to env then *default*."""
        row = self._conn.execute(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        ).fetchone()
        if row and row["value"]:
            return row["value"]
        # Fallback to environment (useful during development)
        return os.getenv(key, default)

    def set(self, key: str, value: str, category: str = "general") -> None:
        """Create or update a setting."""
        self._conn.execute(
            "INSERT INTO app_settings (key, value, category) VALUES (?, ?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value, category),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        self._conn.execute("DELETE FROM app_settings WHERE key = ?", (key,))
        self._conn.commit()

    def get_all(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all settings, optionally filtered by category."""
        if category:
            rows = self._conn.execute(
                "SELECT * FROM app_settings WHERE category = ? ORDER BY key", (category,)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT * FROM app_settings ORDER BY category, key"
            ).fetchall()
        return [dict(r) for r in rows]

    def get_categories(self) -> List[str]:
        rows = self._conn.execute(
            "SELECT DISTINCT category FROM app_settings ORDER BY category"
        ).fetchall()
        return [r["category"] for r in rows]

    def get_masked(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return settings with secret values masked (for UI display)."""
        items = self.get_all(category)
        for item in items:
            if item.get("secret") and item.get("value"):
                v = item["value"]
                if len(v) > 8:
                    item["value"] = v[:4] + "•" * (len(v) - 8) + v[-4:]
                else:
                    item["value"] = "•" * len(v)
        return items

    def validate_required(self) -> List[str]:
        """Return list of required keys that are empty or missing."""
        rows = self._conn.execute(
            "SELECT key FROM app_settings WHERE required = 1 AND (value IS NULL OR value = '')"
        ).fetchall()
        return [r["key"] for r in rows]

    def close(self) -> None:
        if self._conn:
            self._conn.close()
