import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.database import MongoManager

def undelete_all():
    db = MongoManager()
    col = db.transcriptions
    print(f"Total documents: {col.count_documents({})}")
    print(f"Deleted documents: {col.count_documents({'is_deleted': True})}")
    
    result = col.update_many({}, {"$set": {"is_deleted": False}})
    print(f"Updated {result.modified_count} documents. is_deleted is now False for all.")
    
    print(f"New deleted count: {col.count_documents({'is_deleted': True})}")

if __name__ == "__main__":
    undelete_all()
