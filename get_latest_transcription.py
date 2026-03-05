
import os
import sys
from pymongo import DESCENDING

# Ensure current working directory and src/backend are in python path
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'src'))
sys.path.append(os.path.join(os.getcwd(), 'backend'))

try:
    from src.database.mongo_manager import MongoManager
    
    manager = MongoManager()
    collection = manager.get_collection('transcriptions')
    
    # In MongoDB -1 represents DESCENDING
    latest_doc = collection.find_one(sort=[('ingested_at', -1)])

    if latest_doc:
        print("--- LATEST TRANSCRIPTION FOUND ---")
        print(f"ID: {latest_doc.get('_id')}")
        print(f"Filename: {latest_doc.get('filename') or 'N/A'}")
        
        # Determine the content to display (snippet)
        content = latest_doc.get('formatted_content') or latest_doc.get('raw_content') or latest_doc.get('edited_content') or ""
        content_str = str(content)
        snippet = content_str[:250] + ("..." if len(content_str) > 250 else "")
        
        print("\nContent Snippet:")
        print(snippet)
        print("\nIngested at:", latest_doc.get('ingested_at'))
        print("----------------------------------")
    else:
        print("Warning: No transcriptions found in the 'transcriptions' collection.")

except Exception as e:
    import traceback
    print("An error occurred during MongoDB operation:")
    traceback.print_exc()
