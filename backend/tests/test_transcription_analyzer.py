import sys
from unittest.mock import patch, MagicMock
import pytest

def _ensure_mock(mod_name):
    if mod_name not in sys.modules:
        try:
            __import__(mod_name)
        except ImportError:
            sys.modules[mod_name] = MagicMock()

for mod in ["logfire", "dotenv", "pymongo", "openai", "requests"]:
    _ensure_mock(mod)

if isinstance(sys.modules.get("logfire"), MagicMock):
    sys.modules["logfire"].instrument = lambda f=None: (f if f else lambda x: x)

from src.agent.transcription_analyzer import TranscriptionAnalyzer


def test_parse_llm_response_valid_format():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    response_text = "00:00:00 | Introducción a la clase\n00:05:00 | Conceptos Principales"
    
    topics = analyzer._parse_llm_response(response_text)
    assert len(topics) == 2
    assert topics[0] == {"timestamp": "00:00:00", "title": "Introducción a la clase"}
    assert topics[1] == {"timestamp": "00:05:00", "title": "Conceptos Principales"}


def test_parse_llm_response_fallback_on_invalid():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    response_text = "formato invalido sin separador"
    
    topics = analyzer._parse_llm_response(response_text)
    assert topics == [{"timestamp": "00:00:00", "title": "Clase General"}]


def test_analyze_pending_processes_unprocessed_docs():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    mock_db = MagicMock()
    mock_llm = MagicMock()
    
    mock_db.transcriptions.find.return_value = [
        {"_id": "doc1", "filename": "audio1.mp3", "processed": False}
    ]
    
    analyzer.db = mock_db
    analyzer.llm = mock_llm
    
    with patch.object(analyzer, "_analyze_transcription") as mock_analyze:
        count = analyzer.analyze_pending()
        assert count == 1
        mock_analyze.assert_called_once_with("doc1")
        mock_db.transcriptions.update_one.assert_called_once_with(
            {"_id": "doc1"},
            {"$set": {"processed": True}}
        )
