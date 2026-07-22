import asyncio
import importlib
import sys
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

from fastapi import WebSocketDisconnect

_module_name = "services.audio.audio_processor"
_saved_module = sys.modules.get(_module_name)
_fake_module = ModuleType(_module_name)
_fake_module.AudioProcessor = MagicMock
sys.modules[_module_name] = _fake_module
websocket_router = importlib.import_module("backend.routers.websocket_router")
if _saved_module is None:
    sys.modules.pop(_module_name, None)
else:
    sys.modules[_module_name] = _saved_module


def _processor(monkeypatch):
    processor = MagicMock()
    processor.transcribe_chunk = AsyncMock()
    processor.finalize = AsyncMock()
    processor.cleanup = AsyncMock()
    monkeypatch.setattr(
        websocket_router, "AudioProcessor", MagicMock(return_value=processor)
    )
    return processor


def test_websocket_processes_audio_and_stop_message(monkeypatch):
    processor = _processor(monkeypatch)
    processor.transcribe_chunk.return_value = {"text": "hello", "timestamp": 1.5}
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.receive = AsyncMock(
        side_effect=[{"bytes": b"audio"}, {"text": '{"type":"stop"}'}]
    )
    websocket.send_json = AsyncMock()

    asyncio.run(websocket_router.websocket_transcribe(websocket))

    websocket.accept.assert_awaited_once_with()
    processor.transcribe_chunk.assert_awaited_once_with(b"audio")
    processor.finalize.assert_awaited_once_with()
    assert websocket.send_json.await_args_list[0].args[0] == {
        "type": "transcription",
        "text": "hello",
        "timestamp": 1.5,
    }
    assert websocket.send_json.await_args_list[1].args[0]["type"] == "complete"
    processor.cleanup.assert_awaited_once_with()


def test_websocket_ignores_empty_transcription_then_handles_disconnect(monkeypatch):
    processor = _processor(monkeypatch)
    processor.transcribe_chunk.return_value = None
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.receive = AsyncMock(side_effect=[{"bytes": b"audio"}, WebSocketDisconnect()])
    websocket.send_json = AsyncMock()

    asyncio.run(websocket_router.websocket_transcribe(websocket))

    websocket.send_json.assert_not_awaited()
    processor.cleanup.assert_awaited_once_with()


def test_websocket_reports_processing_error(monkeypatch):
    processor = _processor(monkeypatch)
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.receive = AsyncMock(side_effect=ValueError("bad payload"))
    websocket.send_json = AsyncMock()

    asyncio.run(websocket_router.websocket_transcribe(websocket))

    websocket.send_json.assert_awaited_once_with(
        {"type": "error", "message": "bad payload"}
    )
    processor.cleanup.assert_awaited_once_with()


def test_websocket_contains_error_while_reporting_error(monkeypatch):
    processor = _processor(monkeypatch)
    websocket = MagicMock()
    websocket.accept = AsyncMock()
    websocket.receive = AsyncMock(side_effect=ValueError("bad payload"))
    websocket.send_json = AsyncMock(side_effect=RuntimeError("socket closed"))
    monkeypatch.setattr("traceback.print_exc", MagicMock())

    asyncio.run(websocket_router.websocket_transcribe(websocket))

    processor.cleanup.assert_awaited_once_with()
