import asyncio
import importlib
import sys
from collections import deque
from datetime import datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest


class FakeAudioUtils:
    @staticmethod
    def calculate_rms(data):
        return 100.0 if data else 0.0

    @staticmethod
    def apply_gain(data, _gain):
        return data


class FakeAdapter:
    def to_pcm(self, data):
        return bytes(data)


class FakeVADConfig:
    def __init__(self, voice_threshold=500, silence_threshold=200, silence_chunks_to_end=4):
        self.voice_threshold = voice_threshold
        self.silence_threshold = silence_threshold
        self.silence_chunks_to_end = silence_chunks_to_end


class FakeVAD:
    def __init__(self, config=None):
        self.config = config or FakeVADConfig()
        self.result = SimpleNamespace(
            rms=500.0,
            should_buffer=True,
            phrase_ended=True,
            state=SimpleNamespace(name="SPEECH"),
        )
        self.reset = MagicMock()

    def process_chunk(self, _data):
        return self.result


def _load_socket_handler():
    dependencies = {}
    audio = ModuleType("backend.services.audio.audio_service")
    audio.AudioProcessorPort = object
    audio.WebMAudioAdapter = FakeAdapter
    audio.PCMPassthroughAdapter = FakeAdapter
    audio.AudioUtils = FakeAudioUtils
    dependencies[audio.__name__] = audio

    vad = ModuleType("backend.services.audio.vad_service")
    vad.ThresholdVADStrategy = FakeVAD
    vad.VADConfig = FakeVADConfig
    vad.VADStrategy = object
    dependencies[vad.__name__] = vad

    transcription = ModuleType("src.transcription")
    transcription.FormatterFactory = MagicMock()
    dependencies[transcription.__name__] = transcription

    asr = ModuleType("backend.services.audio.asr")
    asr.ASRService = MagicMock
    asr.ASRRequest = MagicMock
    dependencies[asr.__name__] = asr

    saved = {name: sys.modules.get(name) for name in dependencies}
    sys.modules.update(dependencies)
    module = importlib.import_module("backend.services.realtime.socket_handler")
    for name, previous in saved.items():
        if previous is None:
            sys.modules.pop(name, None)
        else:
            sys.modules[name] = previous
    return module


socket_handler = _load_socket_handler()


class FakeSio:
    def __init__(self):
        self.handlers = {}
        self.emit = AsyncMock()

    def event(self, func):
        self.handlers[func.__name__] = func
        return func


def _segment(
    text_bytes=b"x" * 160000,
    *,
    segment_id=1,
    avg_rms=500.0,
    voiced_ratio=0.8,
):
    return socket_handler.ASRSegment(
        segment_id=segment_id,
        pcm_bytes=text_bytes,
        language="es",
        timestamp="00:00:01",
        start_seconds=1.0,
        end_seconds=6.0,
        avg_rms=avg_rms,
        voiced_ratio=voiced_ratio,
        diarize=False,
        reason="test",
    )


@pytest.fixture(autouse=True)
def clear_sessions():
    socket_handler.active_sessions.clear()
    yield
    socket_handler.active_sessions.clear()


def test_segment_duration_pcm_seconds_normalization_and_timestamp():
    assert _segment(b"x" * 32000).duration_seconds == 1.0
    assert _segment(b"").duration_seconds == 0.0
    assert socket_handler._seconds_from_pcm(b"x" * 64000) == 2.0
    assert socket_handler._seconds_from_pcm(b"") == 0.0
    assert socket_handler._normalize_text("  ¡Sí, ÁRBOL!  ") == "si arbol"
    assert socket_handler.format_timestamp(3661.9) == "01:01:01"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", True),
        ("Gracias por ver el video", True),
        ("Estos subtitulos realizados por alguien", True),
        ("contenido académico válido", False),
    ],
)
def test_known_hallucination_detection(text, expected):
    assert socket_handler._is_known_hallucination(
        socket_handler._normalize_text(text)
    ) is expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("one two three", False),
        ("hola hola hola hola", True),
        ("uno dos uno dos uno dos uno dos uno dos", True),
        ("uno dos tres cuatro cinco seis siete ocho nueve diez", False),
    ],
)
def test_repetitive_text_detection(text, expected):
    assert socket_handler._is_repetitive_text(text) is expected


def test_overlap_trimming_and_duplicate_detection():
    recent = deque(["uno dos tres cuatro cinco"], maxlen=6)
    assert socket_handler._trim_overlap("tres cuatro cinco seis siete", recent) == "seis siete"
    assert socket_handler._trim_overlap("texto diferente", recent) == "texto diferente"
    assert socket_handler._trim_overlap("", recent) == ""
    assert socket_handler._is_duplicate_text("texto corto", recent) is False
    assert socket_handler._is_duplicate_text("uno dos tres cuatro cinco", recent) is True
    assert socket_handler._is_duplicate_text(
        "uno dos tres cuatro cinco adicional", recent
    ) is False


@pytest.mark.parametrize(
    ("text", "segment", "accepted"),
    [
        ("gracias por ver", _segment(), False),
        ("sí", _segment(), False),
        ("hola hola", _segment(), False),
        ("contenido válido con varias palabras", _segment(b"x" * 16000), False),
        ("contenido válido con varias palabras", _segment(b"x" * 64000, avg_rms=100), False),
        (
            "contenido válido con varias palabras",
            _segment(b"x" * 160000, avg_rms=10, voiced_ratio=0.01),
            False,
        ),
        ("esta es una transcripción académica completamente válida", _segment(), True),
    ],
)
def test_sanitize_asr_text_filters_bad_segments(text, segment, accepted):
    session = {}
    result = socket_handler._sanitize_asr_text(text, session, segment)
    assert bool(result) is accepted
    assert session.get("dropped_segments", 0) == (0 if accepted else 1)


def test_sanitize_asr_text_trims_overlap_and_rejects_duplicate():
    session = {"recent_transcripts": deque(["uno dos tres cuatro cinco"], maxlen=6)}
    text = "tres cuatro cinco y ahora continuamos con contenido nuevo"
    assert socket_handler._sanitize_asr_text(text, session, _segment()) == (
        "y ahora continuamos con contenido nuevo"
    )

    session = {"recent_transcripts": deque(["contenido exactamente duplicado aquí"], maxlen=6)}
    assert socket_handler._sanitize_asr_text(
        "contenido exactamente duplicado aquí", session, _segment()
    ) == ""


def test_incremental_writer_and_close_helper(monkeypatch, tmp_path):
    wav = MagicMock()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(socket_handler.wave, "open", MagicMock(return_value=wav))
    writer = socket_handler.IncrementalWavWriter("audio.wav", 8000)

    writer.write(b"pcm")
    writer.write(b"")
    writer.close()
    writer.close()

    wav.setnchannels.assert_called_once_with(1)
    wav.setsampwidth.assert_called_once_with(2)
    wav.setframerate.assert_called_once_with(8000)
    wav.writeframes.assert_called_once_with(b"pcm")
    wav.close.assert_called_once_with()

    assert socket_handler._close_audio_writer({"audio_filename": "fallback.wav"}) == "fallback.wav"
    session = {"audio_writer": writer}
    assert socket_handler._close_audio_writer(session) == "audio.wav"
    assert session["audio_writer"] is None


def test_close_writer_and_status_emit_contain_errors(capsys):
    writer = MagicMock(filename="bad.wav")
    writer.close.side_effect = OSError("locked")
    assert socket_handler._close_audio_writer({"audio_writer": writer}) == "bad.wav"

    sio = MagicMock()
    sio.emit = AsyncMock(side_effect=RuntimeError("closed"))
    asyncio.run(socket_handler._emit_transcription_status(sio, "sid", "event", value=1))
    output = capsys.readouterr().out
    assert "Error closing WAV writer" in output
    assert "emit transcription_status error" in output


def test_asr_transcribe_normalizes_wraps_and_returns_text(monkeypatch):
    service = MagicMock()
    service.transcribe = AsyncMock(return_value=SimpleNamespace(text="  transcript  "))
    request_cls = MagicMock(return_value="request")
    monkeypatch.setattr(socket_handler.AudioUtils, "calculate_rms", MagicMock(return_value=90))
    monkeypatch.setattr(socket_handler.AudioUtils, "apply_gain", MagicMock(return_value=b"gain"))
    monkeypatch.setattr(socket_handler, "ASRService", MagicMock(return_value=service))
    monkeypatch.setattr(socket_handler, "ASRRequest", request_cls)

    result = asyncio.run(socket_handler._asr_transcribe(b"pcm", "es", True))

    assert result == "transcript"
    socket_handler.AudioUtils.apply_gain.assert_called_once()
    request = request_cls.call_args.kwargs
    assert request["audio_bytes"].startswith(b"RIFF")
    assert request["sample_rate"] == 16000
    assert request["language"] == "es"
    assert request["diarize"] is True


def test_asr_transcribe_handles_empty_and_errors(monkeypatch):
    service = MagicMock()
    service.transcribe = AsyncMock(return_value=SimpleNamespace(text=""))
    monkeypatch.setattr(socket_handler, "ASRService", MagicMock(return_value=service))
    monkeypatch.setattr(socket_handler, "ASRRequest", MagicMock())
    monkeypatch.setattr(socket_handler.AudioUtils, "calculate_rms", MagicMock(return_value=0))
    assert asyncio.run(socket_handler._asr_transcribe(b"pcm")) == ""

    service.transcribe.side_effect = RuntimeError("ASR offline")
    assert asyncio.run(socket_handler._asr_transcribe(b"pcm")) == ""


def test_connect_start_gain_audio_stop_and_disconnect(monkeypatch):
    async def scenario():
        sio = FakeSio()
        socket_handler.register_socket_events(sio)
        writer = MagicMock(filename="recording.wav")
        monkeypatch.setattr(
            socket_handler, "IncrementalWavWriter", MagicMock(return_value=writer)
        )
        monkeypatch.setattr(
            socket_handler,
            "_asr_transcribe",
            AsyncMock(return_value="esta es una transcripción válida para la clase"),
        )

        await sio.handlers["connect"]("sid", {})
        assert "sid" in socket_handler.active_sessions
        assert sio.emit.await_args_list[0].args[0] == "connected"

        started = await sio.handlers["start_recording"](
            "sid",
            {
                "language": "es",
                "diarization": True,
                "voiceThreshold": 300,
                "silenceThreshold": 100,
            },
        )
        session = socket_handler.active_sessions["sid"]
        assert started["ok"] is True
        assert session["active"] is True
        assert session["language"] == "es"
        assert session["diarization"] is True

        await sio.handlers["set_mic_gain"]("sid", {"gain": 20})
        assert session["mic_gain"] == 5.0
        await sio.handlers["set_mic_gain"]("sid", 0.1)
        assert session["mic_gain"] == 0.5

        session["vad_strategy"].result = SimpleNamespace(
            rms=500.0,
            should_buffer=True,
            phrase_ended=True,
            state=SimpleNamespace(name="SPEECH"),
        )
        await sio.handlers["audio_chunk_pcm"]("sid", b"x" * 32000)
        await asyncio.wait_for(session["asr_queue"].join(), timeout=2)
        assert len(session["transcription_buffer"]) == 1
        assert session["transcription_buffer"][0]["text"].startswith("esta es")

        await sio.handlers["audio_chunk"]("sid", b"x" * 32000)
        await asyncio.wait_for(session["asr_queue"].join(), timeout=2)

        repository = ModuleType("backend.repositories.transcription_repository")
        repository.TranscriptionRepository = MagicMock
        database = ModuleType("src.database.mongo_manager")
        db = MagicMock()
        db.transcriptions.insert_one.return_value = SimpleNamespace(inserted_id="doc-1")
        database.MongoManager = MagicMock(return_value=db)
        analyzer_module = ModuleType("src.agent.transcription_analyzer")
        analyzer_module.TranscriptionAnalyzer = MagicMock
        generator_module = ModuleType("src.agent.document_generator")
        generator_module.DocumentGenerator = MagicMock
        formatter = MagicMock()
        formatter.format.return_value = "# Transcript"
        socket_handler.FormatterFactory.create.return_value = formatter

        monkeypatch.setitem(sys.modules, repository.__name__, repository)
        monkeypatch.setitem(sys.modules, database.__name__, database)
        monkeypatch.setitem(sys.modules, analyzer_module.__name__, analyzer_module)
        monkeypatch.setitem(sys.modules, generator_module.__name__, generator_module)

        tasks_before = set(asyncio.all_tasks())
        await sio.handlers["stop_recording"]("sid")
        spawned = [task for task in asyncio.all_tasks() - tasks_before if task is not asyncio.current_task()]
        if spawned:
            await asyncio.wait_for(asyncio.gather(*spawned), timeout=3)

        assert db.transcriptions.insert_one.called
        assert any(call.args[0] == "processing_complete" for call in sio.emit.await_args_list)
        assert session["stopping"] is False

        await sio.handlers["disconnect"]("sid")
        assert "sid" not in socket_handler.active_sessions

    asyncio.run(scenario())


def test_registered_handlers_cover_inactive_error_and_disconnect_branches(monkeypatch):
    async def scenario():
        sio = FakeSio()
        socket_handler.register_socket_events(sio)

        await sio.handlers["disconnect"]("missing")
        await sio.handlers["set_mic_gain"]("missing", 2)
        await sio.handlers["audio_chunk"]("missing", b"data")
        await sio.handlers["audio_chunk_pcm"]("missing", b"data")
        await sio.handlers["stop_recording"]("missing")
        assert sio.emit.await_args.args[0] == "error"

        await sio.handlers["connect"]("sid", {})
        session = socket_handler.active_sessions["sid"]
        session["stopping"] = True
        await sio.handlers["disconnect"]("sid")
        assert "sid" in socket_handler.active_sessions

        session["active"] = True
        await sio.handlers["audio_chunk_pcm"]("sid", b"tiny")
        monkeypatch.setattr(
            socket_handler._webm_adapter,
            "to_pcm",
            MagicMock(side_effect=RuntimeError("bad webm")),
        )
        await sio.handlers["audio_chunk"]("sid", b"bad")

    asyncio.run(scenario())
