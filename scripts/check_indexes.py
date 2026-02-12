from src.database import MongoManager
from pymongo import ASCENDING

def check_indexes():
    db = MongoManager()
    
    print("\n--- Transcriptions Indexes ---")
    for name, info in db.transcriptions.index_information().items():
        print(f"{name}: {info}")
        
    print("\n--- Segments Indexes ---")
    for name, info in db.segments.index_information().items():
        print(f"{name}: {info}")
        
    # Check if index on transcription_id exists in segments
    if "transcription_id_1" not in db.segments.index_information():
        print("\n[WARN] Index on transcription_id in segments collection is MISSING!")
        print("Creating index now...")
        db.segments.create_index([("transcription_id", ASCENDING)])
        print("Index created.")
    else:
        print("\n[INFO] Index on transcription_id in segments exists.")

if __name__ == "__main__":
    check_indexes()
