import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from backend.services.nim import DetectionResult, TranslationResult
from backend.services.translation.detector import LanguageDetectionService
from backend.services.translation.translator import TranslationRequest, TranslationService


def test_language_detector_handles_empty_text():
    registry = MagicMock()

    result = asyncio.run(LanguageDetectionService(registry).detect("   "))

    assert result == DetectionResult("unknown", "Unknown", 0.0)
    registry.get_text.assert_not_called()


def test_language_detector_calls_model_and_parses_json():
    client = MagicMock()
    client.generate = AsyncMock(
        return_value='```json\n{"language_code":"ES","language_name":"Spanish","confidence":0.98}\n```'
    )
    registry = MagicMock()
    registry.get_text.return_value = client

    result = asyncio.run(LanguageDetectionService(registry).detect(" hola " * 100))

    assert result == DetectionResult("es", "Spanish", 0.98)
    messages = client.generate.await_args.args[0]
    assert len(messages[0]["content"].split("Text: ", 1)[1]) == 400
    client.generate.assert_awaited_once_with(messages, temperature=0.0, max_tokens=64)


def test_language_detector_returns_null_object_on_client_error():
    client = MagicMock()
    client.generate = AsyncMock(side_effect=RuntimeError("offline"))
    registry = MagicMock()
    registry.get_text.return_value = client

    assert asyncio.run(LanguageDetectionService(registry).detect("hello")) == DetectionResult(
        "unknown", "Unknown", 0.0
    )


def test_language_detector_parser_uses_defaults_and_heuristics():
    assert LanguageDetectionService._parse('{"language_code":"fr"}') == DetectionResult(
        "fr", "French", 1.0
    )
    assert LanguageDetectionService._parse("detected language: Spanish (es)") == DetectionResult(
        "es", "Spanish", 0.7
    )
    assert LanguageDetectionService._parse("???") == DetectionResult(
        "unknown", "Unknown", 0.0
    )


def test_translation_request_defaults_are_explicit():
    request = TranslationRequest("hello")
    assert request.target_language == "es"
    assert request.source_language == "auto"
    assert request.preserve_formatting is True
    assert request.domain == "academic"


def test_translation_service_handles_empty_text():
    registry = MagicMock()

    result = asyncio.run(TranslationService(registry).translate(" ", target_language="fr"))

    assert result == TranslationResult("", "auto", "fr", "none")
    registry.get_text.assert_not_called()


def test_translation_service_builds_request_and_returns_metadata():
    client = MagicMock()
    client.generate = AsyncMock(return_value="  Hola mundo  ")
    registry = MagicMock()
    registry.get_text.return_value = client
    registry._configs = {"translator": SimpleNamespace(model_id="model-1")}

    result = asyncio.run(
        TranslationService(registry).translate(
            "Hello world", target_language="es", source_language="en", domain="technical"
        )
    )

    assert result == TranslationResult("Hola mundo", "en", "es", "model-1")
    messages = client.generate.await_args.args[0]
    assert "source language is English" in messages[0]["content"]
    assert "technical documentation" in messages[0]["content"]
    assert messages[1] == {"role": "user", "content": "Hello world"}
    client.generate.assert_awaited_once_with(
        messages, temperature=0.15, top_p=1.0, max_tokens=33
    )


def test_translation_service_uses_fallback_model_and_plain_general_prompt():
    client = MagicMock()
    client.generate = AsyncMock(return_value="bonjour")
    registry = MagicMock()
    registry.get_text.return_value = client
    registry._configs = {}

    result = asyncio.run(
        TranslationService(registry).translate(
            "hello",
            target_language="fr",
            preserve_formatting=False,
            domain="general",
        )
    )

    prompt = client.generate.await_args.args[0][0]["content"]
    assert "auto-detected" in prompt
    assert "general audiences" in prompt
    assert "plain text" in prompt
    assert result.model_used == "mistralai/mistral-large-3"


def test_translation_prompt_handles_custom_domain_and_language():
    prompt = TranslationService._build_system_prompt(
        target_name="Klingon",
        source_name="Spanish",
        preserve_formatting=True,
        domain="custom",
    )
    assert "source language is Spanish" in prompt
    assert "accurate and fluent" in prompt
    assert "Preserve all markdown" in prompt
