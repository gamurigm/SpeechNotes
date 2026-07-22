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


def test_analyze_pending_continues_after_one_failure():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    analyzer.db = MagicMock()
    analyzer.db.transcriptions.find.return_value = [
        {"_id": "bad", "filename": "bad.md"},
        {"_id": "good", "filename": "good.md"},
    ]
    with patch.object(analyzer, "_analyze_transcription", side_effect=[RuntimeError("x"), None]):
        assert analyzer.analyze_pending() == 1
    analyzer.db.transcriptions.update_one.assert_called_once_with(
        {"_id": "good"}, {"$set": {"processed": True}}
    )


def test_analyze_transcription_skips_empty_and_applies_topics():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    analyzer.db = MagicMock()
    analyzer.db.segments.find.return_value.sort.return_value = []
    analyzer._analyze_transcription("empty")
    analyzer.db.segments.update_one.assert_not_called()

    segments = [
        {"_id": "s1", "timestamp": "00:00:00", "content": "inicio"},
        {"_id": "s2", "timestamp": "00:10:00", "content": "final"},
    ]
    analyzer.db.segments.find.return_value.sort.return_value = segments
    analyzer._detect_topics = MagicMock(return_value=[
        {"timestamp": "00:00:00", "title": "Primero"},
        {"timestamp": "00:05:00", "title": "Segundo"},
    ])
    analyzer._analyze_transcription("doc")
    assert analyzer.db.segments.update_one.call_count == 2
    assert analyzer.db.segments.update_one.call_args_list[1].args[1]["$set"]["topic_title"] == "Segundo"


def test_detect_topics_falls_back_on_provider_error():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    analyzer.llm = MagicMock()
    analyzer.llm.generate.side_effect = RuntimeError("403 forbidden")
    assert analyzer._detect_topics("texto") == [{"timestamp": "00:00:00", "title": "Clase General"}]


def test_parse_llm_response_sorts_and_discards_invalid_lines():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    topics = analyzer._parse_llm_response(
        "00:10:00 | Tarde\nincorrecto\n00:00:00 | Inicio\n99:99:99 | raro"
    )
    assert [topic["title"] for topic in topics] == ["Inicio", "Tarde", "raro"]


def test_apply_topics_updates_same_topic_until_boundary():
    analyzer = TranscriptionAnalyzer.__new__(TranscriptionAnalyzer)
    analyzer.db = MagicMock()
    segments = [
        {"_id": "a", "timestamp": "00:00:01"},
        {"_id": "b", "timestamp": "00:04:59"},
        {"_id": "c", "timestamp": "00:05:00"},
    ]
    analyzer._apply_topics_to_segments(segments, [
        {"timestamp": "00:00:00", "title": "A"},
        {"timestamp": "00:05:00", "title": "B"},
    ])
    titles = [call.args[1]["$set"]["topic_title"] for call in analyzer.db.segments.update_one.call_args_list]
    assert titles == ["A", "A", "B"]
