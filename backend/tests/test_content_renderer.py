from unittest.mock import MagicMock

import backend.services.knowledge.content_renderer as renderer_module
from backend.services.knowledge.content_renderer import (
    ContentRenderer,
    FormattedContentStrategy,
    RawContentStrategy,
    SegmentDocumentStrategy,
)


def test_individual_content_strategies():
    assert FormattedContentStrategy().render({"formatted_content": "formatted"}, []) == "formatted"
    assert RawContentStrategy().render({"edited_content": "edited"}, []) == "edited"
    assert RawContentStrategy().render({"formatted_content": "formatted"}, []) == "formatted"
    assert RawContentStrategy().render({"raw_content": "raw"}, []) == "raw"
    assert RawContentStrategy().render({}, []) == ""


def test_segment_strategy_handles_missing_success_and_error():
    assert SegmentDocumentStrategy().render({}, [{"content": "text"}]) == ""
    generator = MagicMock()
    generator._group_by_topic.return_value = {"Topic": []}
    generator._build_markdown.return_value = "# Generated"
    strategy = SegmentDocumentStrategy(generator)

    assert strategy.render({"id": "doc"}, [{"content": "text"}]) == "# Generated"
    generator._build_markdown.side_effect = RuntimeError("bad segment")
    assert strategy.render({}, []) == ""


def test_renderer_selects_processing_formatted_segment_and_fallback_paths(monkeypatch):
    monkeypatch.setattr(renderer_module, "_has_generator", False)
    renderer = ContentRenderer()

    assert renderer.generator is None
    assert renderer.render_transcription({"processed": False, "raw_content": "partial"}, []) == "partial"
    assert "Procesando" in renderer.render_transcription({"processed": False}, [])
    assert renderer.render_transcription(
        {"formatted_content": "# Ready", "is_formatted": True, "raw_content": "raw"}, []
    ) == "# Ready"
    assert renderer.render_transcription({"formatted_content": "# Only"}, []) == "# Only"

    renderer.segment_strategy.render = MagicMock(return_value="# From segments")
    assert renderer.render_transcription({"raw_content": "raw"}, [{"topic": "one"}]) == "# From segments"
    renderer.segment_strategy.render.return_value = ""
    assert renderer.render_transcription({"edited_content": "edited"}, [{}]) == "edited"
    assert renderer.render_transcription({}, []) == "# Sin contenido disponible"


def test_renderer_constructs_generator_when_available(monkeypatch):
    generator = MagicMock()
    monkeypatch.setattr(renderer_module, "_has_generator", True)
    monkeypatch.setattr(renderer_module, "DocumentGenerator", MagicMock(return_value=generator))

    renderer = ContentRenderer()

    assert renderer.generator is generator
    assert renderer.segment_strategy.generator is generator
