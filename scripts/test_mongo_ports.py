
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

def test_specific_connection(uri, name):
    print(f"Testing {name} at {uri}...")
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=2000)
        client.admin.command('ping')
        print(f"[SUCCESS] Connected to {name}!")
        return True
    except Exception as e:
        print(f"[FAILED] Could not connect to {name}: {e}")
        return False

if __name__ == "__main__":
    # Test configured port (27018)
    test_specific_connection("mongodb://localhost:27018/", "Custom Port (27018)")
    
    # Test default port (27017)
    test_specific_connection("mongodb://localhost:27017/", "Default Port (27017)")
