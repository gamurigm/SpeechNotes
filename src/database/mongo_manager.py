"""
MongoDB Manager Module
Handles connection and operations with MongoDB.
"""

import os
from typing import Any, Dict, List, Optional
from pymongo import MongoClient
from pymongo.collection import Collection
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()


class MongoManager:
    """
    Singleton class to manage MongoDB connection and collections.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection."""
        self.uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        self.db_name = os.getenv("MONGO_DB_NAME", "agent_knowledge_base")
        
        try:
            self.client = MongoClient(self.uri)
            self.db: Database = self.client[self.db_name]
            print(f"[INFO] Connected to MongoDB at {self.uri} (DB: {self.db_name})")
        except Exception as e:
            print(f"[ERROR] Failed to connect to MongoDB: {e}")
            raise
            
    def get_collection(self, collection_name: str) -> Collection:
        """Get a specific collection."""
        return self.db[collection_name]
    
    def close(self):
        """Close MongoDB connection."""
        if self.client:
            self.client.close()
            print("[INFO] MongoDB connection closed")

    # --- Helper methods for Transcriptions ---
    
    @property
    def transcriptions(self) -> Collection:
        """Get transcriptions collection."""
        return self.db.transcriptions
        
    @property
    def segments(self) -> Collection:
        """Get segments collection."""
        return self.db.segments
