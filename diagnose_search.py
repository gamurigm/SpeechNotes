import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.database import MongoManager

def check_status():
    db = MongoManager()
    trans_col = db.transcriptions
    
    docs = list(trans_col.find())
    print(f"Total documents: {len(docs)}")
    
    processed_count = 0
    not_processed_count = 0
    deleted_count = 0
    
    for d in docs:
        if d.get("processed"):
            processed_count += 1
        else:
            not_processed_count += 1
            
        if d.get("is_deleted"):
            deleted_count += 1
            
    print(f"Processed: {processed_count}")
    print(f"Not Processed: {not_processed_count}")
    print(f"Deleted (is_deleted: True): {deleted_count}")
    
    # Check specifically for search matches with different filters
    q = "minimax"
    docs_with_minimax = list(trans_col.find({
        "$or": [
            {"formatted_content": {"$regex": q, "$options": "i"}},
            {"raw_content": {"$regex": q, "$options": "i"}},
            {"edited_content": {"$regex": q, "$options": "i"}}
        ]
    }))
    print(f"\nDocs containing '{q}' (any status): {len(docs_with_minimax)}")
    
    for d in docs_with_minimax:
        print(f"  - File: {d.get('filename')} | P: {d.get('processed')} | D: {d.get('is_deleted')}")

if __name__ == "__main__":
    check_status()
