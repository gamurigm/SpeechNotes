import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from src.database import MongoManager

def inspect_database():
    db = MongoManager()
    trans_col = db.transcriptions
    
    docs = list(trans_col.find())
    print(f"Total entries: {len(docs)}")
    
    for d in docs:
        raw = d.get("raw_content", "") or ""
        fmt = d.get("formatted_content", "") or ""
        edt = d.get("edited_content", "") or ""
        
        raw_len = len(raw)
        fmt_len = len(fmt)
        edt_len = len(edt)
        
        # Check for meaningful content
        has_meaningful = any(c.replace("\ufeff", "").strip() for c in [raw, fmt, edt])
        
        status = "MEANINGFUL" if has_meaningful else "EMPTY"
        print(f"[{status}] File: {d.get('filename')} | R:{raw_len} F:{fmt_len} E:{edt_len}")

if __name__ == "__main__":
    inspect_database()
