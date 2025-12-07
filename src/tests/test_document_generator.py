import unittest
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Set dummy API keys *before* importing the application modules
os.environ["NVIDIA_EMBEDDING_API_KEY"] = "test_key"
os.environ["NVIDIA_API_KEY"] = "test_key"
os.environ["MINIMAX_API_KEY"] = "test_key"

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.agent.document_generator import DocumentGenerator

class TestDocumentGenerator(unittest.TestCase):
    def setUp(self):
        # Set dummy API keys for testing
        os.environ["NVIDIA_EMBEDDING_API_KEY"] = "test_key"
        os.environ["NVIDIA_API_KEY"] = "test_key"
        os.environ["MINIMAX_API_KEY"] = "test_key"

        # Mock the database manager to avoid actual DB calls
        self.mock_db_patcher = patch('src.agent.document_generator.MongoManager')
        self.mock_mongo_manager = self.mock_db_patcher.start()

        self.generator = DocumentGenerator(output_dir="temporal_docs/test_output")

    def tearDown(self):
        self.mock_db_patcher.stop()
        # Clean up any created files
        output_dir = Path("temporal_docs/test_output")
        if output_dir.exists():
            for f in output_dir.glob("*.md"):
                f.unlink()
            output_dir.rmdir()

    def test_initialization(self):
        """Test that the DocumentGenerator initializes correctly."""
        self.assertIsNotNone(self.generator)
        self.assertTrue(Path("temporal_docs/test_output").exists())

    def test_group_by_topic(self):
        """Test that segments are correctly grouped by topic."""
        segments = [
            {"topic_title": "Introduction", "timestamp": "00:00:01", "content": "First part of intro."},
            {"topic_title": "Introduction", "timestamp": "00:00:10", "content": "Second part of intro."},
            {"topic_title": "Core Concepts", "timestamp": "00:01:00", "content": "First core concept."},
            {"topic_title": "Conclusion", "timestamp": "00:02:00", "content": "Final remarks."},
        ]

        topics = self.generator._group_by_topic(segments)

        self.assertEqual(len(topics), 3)
        self.assertEqual(topics[0]["title"], "Introduction")
        self.assertEqual(len(topics[0]["content"]), 2)
        self.assertEqual(topics[1]["title"], "Core Concepts")
        self.assertEqual(len(topics[1]["content"]), 1)
        self.assertEqual(topics[2]["title"], "Conclusion")

    def test_build_markdown(self):
        """Test the standard markdown generation."""
        metadata = {
            "filename": "test_transcription.md",
            "date": "2025-01-01",
            "time": "12:00:00",
            "word_count": 100,
            "duration": "10 minutes"
        }
        topics = [
            {"title": "Topic 1", "start_time": "00:00:05", "content": ["Content for topic 1."]},
            {"title": "Topic 2", "start_time": "00:02:00", "content": ["Content for topic 2."]},
        ]

        markdown = self.generator._build_markdown(metadata, topics)

        self.assertIn("# Transcripción: 2025-01-01", markdown)
        self.assertIn("## Tema 1: Topic 1", markdown)
        self.assertIn("Content for topic 2.", markdown)
        self.assertIn("palabras: 100", markdown)

    @patch('src.agent.document_generator.OpenAI')
    def test_minimax_fallback(self, mock_openai):
        """Test that minimax generation falls back to standard markdown on API failure."""
        # Configure the mock client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        mock_openai.return_value = mock_client

        # Re-initialize the generator to use the mocked client
        generator_with_fallback = DocumentGenerator(output_dir="temporal_docs/test_output")

        metadata = {"filename": "fallback_test.md", "date": "2025-01-02", "time": "10:00:00"}
        topics = [{"title": "Fallback Topic", "start_time": "00:00:01", "content": ["Fallback content."]}]

        # This should fail and trigger the fallback
        markdown = generator_with_fallback._generate_with_minimax(metadata, topics)

        # Verify that the fallback markdown was generated
        self.assertIn("# Transcripción: 2025-01-02", markdown)
        self.assertIn("## Tema 1: Fallback Topic", markdown)
        self.assertIn("Fallback content.", markdown)
        self.assertNotIn("generado_con: Minimax M2", markdown)

if __name__ == '__main__':
    unittest.main()
