"""
Database Module

Provides both the legacy MongoManager and the new SQLiteManager.
SQLiteManager is the default for the desktop app.
ConfigService manages API keys and settings.
"""
from .sqlite_manager import SQLiteManager
from .config_service import ConfigService

# Alias: code that imports MongoManager now transparently gets SQLiteManager
MongoManager = SQLiteManager

__all__ = ["MongoManager", "SQLiteManager", "ConfigService"]
