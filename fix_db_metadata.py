import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.database import MongoManager

def fix_metadata():
    db = MongoManager()
    col = db.transcriptions
    
    # 1. Ensure all docs have is_deleted: False if missing
    res1 = col.update_many({"is_deleted": {"$exists": False}}, {"$set": {"is_deleted": False}})
    print(f"Set is_deleted: False for {res1.modified_count} docs")
    
    # 2. Set is_formatted: True for docs with formatted_content
    res2 = col.update_many({"formatted_content": {"$exists": True, "$ne": ""}}, {"$set": {"is_formatted": True}})
    print(f"Set is_formatted: True for {res2.modified_count} docs")
    
    # 3. Ensure processed: True for docs with content
    res3 = col.update_many({"$or": [{"formatted_content": {"$exists": True}}, {"raw_content": {"$exists": True}}]}, {"$set": {"processed": True}})
    print(f"Set processed: True for {res3.modified_count} docs")

if __name__ == "__main__":
    fix_metadata()
