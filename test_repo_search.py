import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, os.path.abspath('.'))

from backend.repositories.transcription_repository import TranscriptionRepository

def test_repo_search():
    repo = TranscriptionRepository()
    query = "minimax"
    print(f"Searching for: '{query}'")
    
    res = repo.search(query)
    
    print(f"Found {len(res['documents'])} documents")
    for doc in res['documents']:
        print(f"  - {doc.get('filename')}")
        
    print(f"Found {len(res['segments'])} segments")
    for seg in res['segments']:
        print(f"  - {seg.get('content')[:50]}...")

if __name__ == "__main__":
    test_repo_search()
