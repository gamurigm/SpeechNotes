
import unittest
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
import os
import sys

# Set a dummy API key for testing
os.environ["NVIDIA_EMBEDDING_API_KEY"] = "test_key"
os.environ["NVIDIA_API_KEY"] = "test_key"

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.services.socket_handler import register_socket_events

class TestSocketHandler(unittest.TestCase):
    def setUp(self):
        self.sio = MagicMock()
        self.sio.emit = AsyncMock()
        register_socket_events(self.sio)
        self.sid = "test_sid"

        # Clean up any old test files
        self.cleanup_files()

    def tearDown(self):
        self.cleanup_files()

    def cleanup_files(self):
        for path in Path("notas").glob("processed_transcripcion_*.md"):
            path.unlink()
        for path in Path("temporal_docs/raw_transcriptions").glob("transcripcion_*.md"):
            path.unlink()
        for path in Path("notas").glob("audio_*.wav"):
            path.unlink()

    @patch('backend.services.socket_handler.DocumentGenerator')
    @patch('backend.services.socket_handler.TranscriptionAnalyzer')
    @patch('backend.services.socket_handler.TranscriptionIngestor')
    @patch('backend.services.socket_handler.MongoManager')
    def test_full_transcription_flow(self, mock_mongo_manager, mock_ingestor, mock_analyzer, mock_generator):
        # Find the event handlers
        connect_handler = self.sio.event.call_args_list[0][0][0]
        start_recording_handler = self.sio.event.call_args_list[2][0][0]
        audio_chunk_handler = self.sio.event.call_args_list[3][0][0]
        stop_recording_handler = self.sio.event.call_args_list[4][0][0]

        async def run_test():
            # 1. Simulate client connection
            await connect_handler(self.sid, {})

            # 2. Simulate starting a recording
            await start_recording_handler(self.sid)

            # 3. Simulate receiving audio chunks
            with patch('backend.services.socket_handler.transcribe_audio_chunk', return_value="Test transcription."):
                await audio_chunk_handler(self.sid, b"fake_audio_data")

            # 4. Simulate stopping the recording
            await stop_recording_handler(self.sid)

            # 5. Verify that the DocumentGenerator was called
            mock_generator.return_value.generate_all.assert_called_once()

            # 6. Simulate the DocumentGenerator's behavior
            #    (Create a dummy file to verify the rest of the logic)
            final_path = Path("notas") / "processed_transcripcion_test.md"
            final_path.write_text("# Test Minimax Content")

            # 7. Verify the final file was created in the correct directory
            output_files = list(Path("notas").glob("processed_transcripcion_*.md"))
            self.assertEqual(len(output_files), 1, "The final processed markdown file was not created in notas/")

            # 8. Verify the content of the file
            content = output_files[0].read_text()
            self.assertIn("# Test Minimax Content", content)

        # Run the async test
        asyncio.run(run_test())

if __name__ == '__main__':
    unittest.main()
