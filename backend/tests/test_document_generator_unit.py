from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.agent.document_generator as module


class SortedRows:
    def __init__(self, rows):
        self.rows = rows
        self.sort_args = None

    def sort(self, *args):
        self.sort_args = args
        return self.rows


def _metadata(filename="audio.wav"):
    return {
        "_id": "doc-1",
        "filename": filename,
        "date": "2026-07-22",
        "time": "10:00",
        "duration": "00:10",
        "word_count": 12,
    }


def _generator(tmp_path, monkeypatch, api_key=None):
    database = MagicMock()
    config = MagicMock()
    values = {
        "MINIMAX_API_KEY": api_key,
        "MINIMAX_BASE_URL": "https://minimax.test/v1",
        "MINIMAX_MODEL_NAME": "minimax-test",
    }
    config.get.side_effect = lambda key, default=None: values.get(key, default)
    openai = MagicMock()
    monkeypatch.setattr(module, "MongoManager", lambda: database)
    monkeypatch.setattr(module, "ConfigService", lambda: config)
    monkeypatch.setattr(module, "OpenAI", openai)
    generator = module.DocumentGenerator(str(tmp_path))
    return generator, database, openai


def test_initialization_without_and_with_llm(tmp_path, monkeypatch):
    generator, _, openai = _generator(tmp_path / "plain", monkeypatch)
    assert generator.client is None
    assert (tmp_path / "plain").is_dir()
    openai.assert_not_called()

    generator, _, openai = _generator(tmp_path / "llm", monkeypatch, "secret")
    assert generator.client is openai.return_value
    openai.assert_called_once_with(base_url="https://minimax.test/v1", api_key="secret")


def test_generate_all_counts_successes_and_continues_after_error(tmp_path, monkeypatch):
    generator, database, _ = _generator(tmp_path, monkeypatch)
    database.transcriptions.find.return_value = [_metadata("one.wav"), _metadata("two.wav")]
    generator._generate_document = MagicMock(side_effect=[None, RuntimeError("bad")])
    assert generator.generate_all() == 1
    assert generator._generate_document.call_count == 2


def test_generate_document_returns_when_no_segments(tmp_path, monkeypatch):
    generator, database, _ = _generator(tmp_path, monkeypatch)
    rows = SortedRows([])
    database.segments.find.return_value = rows
    generator._save_document = MagicMock()
    generator._generate_document(_metadata())
    assert rows.sort_args == ("sequence", 1)
    generator._save_document.assert_not_called()


@pytest.mark.parametrize("content", ["", "[No se detectó audio o no se pudo transcribir]"])
def test_generate_document_handles_empty_audio(tmp_path, monkeypatch, content):
    generator, database, _ = _generator(tmp_path, monkeypatch)
    database.segments.find.return_value = SortedRows([{"content": content}])
    generator._save_document = MagicMock()
    generator._generate_document(_metadata())
    saved = generator._save_document.call_args.args
    assert "No se detectó audio" in saved[1]


def test_generate_document_selects_plain_short_and_full_paths(tmp_path, monkeypatch):
    generator, database, _ = _generator(tmp_path / "plain", monkeypatch)
    database.segments.find.return_value = SortedRows([
        {"content": "contenido", "topic_title": "Tema", "timestamp": "00:01"}
    ])
    generator._build_markdown = MagicMock(return_value="plain-md")
    generator._save_document = MagicMock()
    generator._generate_document(_metadata())
    generator._save_document.assert_called_once_with(_metadata(), "plain-md")

    generator, database, _ = _generator(tmp_path / "llm", monkeypatch, "key")
    generator._save_document = MagicMock()
    generator._generate_short_summary_with_minimax = MagicMock(return_value="short-md")
    database.segments.find.return_value = SortedRows([
        {"content": "corto", "topic_title": "Tema", "timestamp": "00:01"}
    ])
    generator._generate_document(_metadata())
    generator._save_document.assert_called_with(_metadata(), "short-md")

    generator._generate_with_minimax = MagicMock(return_value="full-md")
    database.segments.find.return_value = SortedRows([
        {"content": "x" * 301, "topic_title": "Tema", "timestamp": "00:01"}
    ])
    generator._generate_document(_metadata())
    generator._save_document.assert_called_with(_metadata(), "full-md")


def test_save_document_creates_server_named_file(tmp_path, monkeypatch):
    generator, _, _ = _generator(tmp_path, monkeypatch)
    generator._save_document(_metadata("../../unsafe.md"), "contenido")
    files = list(tmp_path.glob("processed_*.md"))
    assert len(files) == 1
    assert files[0].read_text(encoding="utf-8") == "contenido"


def test_group_by_topic_and_build_markdown(tmp_path, monkeypatch):
    generator, _, _ = _generator(tmp_path, monkeypatch)
    topics = generator._group_by_topic([
        {"topic_title": "Uno, Dos", "timestamp": "00:01", "content": "a"},
        {"topic_title": "Uno, Dos", "timestamp": "00:02", "content": "b"},
        {"timestamp": "00:03", "content": "c"},
    ])
    assert topics == [
        {"title": "Uno, Dos", "start_time": "00:01", "content": ["a", "b"]},
        {"title": "General", "start_time": "00:03", "content": ["c"]},
    ]
    markdown = generator._build_markdown(_metadata(), topics)
    assert "# Transcripción: 2026-07-22" in markdown
    assert "[Uno, Dos](#tema-1-uno-dos)" in markdown
    assert "a\n\nb" in markdown


def test_no_audio_markdown_contains_metadata(tmp_path, monkeypatch):
    generator, _, _ = _generator(tmp_path, monkeypatch)
    result = generator._generate_no_audio_markdown(_metadata())
    assert "estado: Sin Audio Detectado" in result
    assert "audio.wav" in result and "10:00" in result


@pytest.mark.parametrize("method_name, token_limit, marker", [
    ("_generate_short_summary_with_minimax", 1000, "tipo: Resumen Breve"),
    ("_generate_with_minimax", 8192, "generado_con: Minimax M2"),
])
def test_llm_generation_success_and_fallback(tmp_path, monkeypatch, method_name, token_limit, marker):
    generator, _, _ = _generator(tmp_path, monkeypatch, "key")
    generator.client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content="# Resultado"))]
    )
    topics = [{"title": "Tema", "start_time": "00:01", "content": ["a", "b"]}]
    method = getattr(generator, method_name)
    result = method(_metadata(), topics)
    assert marker in result and result.endswith("# Resultado")
    assert generator.client.chat.completions.create.call_args.kwargs["max_tokens"] == token_limit

    generator.client.chat.completions.create.side_effect = RuntimeError("provider")
    generator._build_markdown = MagicMock(return_value="fallback")
    assert method(_metadata(), topics) == "fallback"
    generator._build_markdown.assert_called_once_with(_metadata(), topics)
