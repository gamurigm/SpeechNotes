
import sys
import os
import asyncio

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.services.transcription_service import TranscriptionService
from backend.repositories.transcription_repository import TranscriptionRepository
from backend.services.content_renderer import ContentRenderer

async def test_transcription_service():
    print("Initializing service...")
    try:
        service = TranscriptionService(
            repository=TranscriptionRepository(),
            renderer=ContentRenderer()
        )
        print("Service initialized.")

        print("Testing list_recent(limit=50)...")
        items = service.list_recent(limit=50)
        print(f"Success! Retrieved {len(items)} items.")
        for item in items[:3]:
            print(f" - {item}")

    except Exception as e:
        print(f"Error testing service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_transcription_service())
