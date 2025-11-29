
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def test_mongo_connection():
    uris = [
        os.getenv("MONGO_URI"),
        
        "mongodb://localhost:27018/"
    ]
    
    print("Testing MongoDB connections...")
    
    for uri in uris:
        if not uri: continue
        print(f"\nTrying URI: {uri}")
        try:
            client = MongoClient(uri, serverSelectionTimeoutMS=2000)
            client.admin.command('ping')
            print(f"[SUCCESS] Connected to {uri}")
            return
        except Exception as e:
            print(f"[FAILED] Could not connect to {uri}: {e}")

if __name__ == "__main__":
    test_mongo_connection()
