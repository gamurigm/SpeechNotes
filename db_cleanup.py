import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.database import MongoManager

def cleanup_database():
    db = MongoManager()
    trans_col = db.transcriptions
    seg_col = db.segments
    
    print(f"Initial transcription count: {trans_col.count_documents({})}")
    print(f"Initial segment count: {seg_col.count_documents({})}")
    
    all_trans = list(trans_col.find())
    deleted_count = 0
    
    for doc in all_trans:
        t_id = doc["_id"]
        filename = doc.get("filename", "Unknown")
        
        # Check transcription document content fields
        raw = (doc.get("raw_content", "") or "").replace("\ufeff", "").strip()
        fmt = (doc.get("formatted_content", "") or "").replace("\ufeff", "").strip()
        edt = (doc.get("edited_content", "") or "").replace("\ufeff", "").strip()
        
        # Check segments
        segments = list(seg_col.find({"transcription_id": t_id}))
        has_segment_content = any((s.get("content", "") or "").replace("\ufeff", "").strip() for s in segments)
        
        # If all content fields are empty AND there is no content in segments
        is_empty = (not raw and not fmt and not edt and not has_segment_content)
        
        if is_empty:
            print(f"🗑️ Deleting empty transcription: {filename} ({t_id})")
            # Delete segments first
            seg_col.delete_many({"transcription_id": t_id})
            # Delete transcription
            trans_col.delete_one({"_id": t_id})
            deleted_count += 1
            
    print(f"\nCleanup finished.")
    print(f"Deleted {deleted_count} empty transcriptions.")
    print(f"Final transcription count: {trans_col.count_documents({})}")
    print(f"Final segment count: {seg_col.count_documents({})}")

if __name__ == "__main__":
    cleanup_database()
