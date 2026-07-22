"""Unit tests for formatter router branches without Mongo/FFmpeg services."""
import asyncio
import sys
from datetime import datetime
from types import ModuleType, SimpleNamespace
from unittest.mock import MagicMock

import pytest

formatter_mod = ModuleType("services.agents.formatter_agent")
formatter_mod.FormatterAgent = MagicMock
services_mod = sys.modules.setdefault("services", ModuleType("services"))
services_mod.__path__ = []
agents_mod = sys.modules.setdefault("services.agents", ModuleType("services.agents"))
agents_mod.__path__ = []
sys.modules.setdefault("services.agents.formatter_agent", formatter_mod)
mongo_mod = ModuleType("src.database.mongo_manager")
mongo_mod.MongoManager = MagicMock
sys.modules.setdefault("src.database.mongo_manager", mongo_mod)

import backend.routers.formatter as module


def test_list_files_and_start_job(monkeypatch):
    db = MagicMock()
    docs = [{"_id": 1, "filename": "a.wav", "raw_content": "x", "date": "today", "word_count": 3, "source_type": "audio"}]
    db.transcriptions.find.return_value.sort.return_value.limit.return_value = docs
    monkeypatch.setattr(module, "MongoManager", lambda: db)
    monkeypatch.setattr(module, "formatter_agent", MagicMock(create_job=lambda ids: "job-1"))
    files = asyncio.run(module.list_available_files(True))
    assert files[0].id == "1" and files[0].tiene_contenido
    response = asyncio.run(module.start_format_job(module.FormatRequest(file_ids=["1"]), True))
    assert response.job_id == "job-1" and response.total_files == 1
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.start_format_job(module.FormatRequest(file_ids=[]), True))
    assert exc.value.status_code == 500


def test_job_status_and_background(monkeypatch):
    progress = SimpleNamespace(to_dict=lambda: {"step": "done"})
    job = SimpleNamespace(job_id="j", status="done", files=["a"], successful=1, failed=0,
                          created_at=datetime(2026, 1, 1), completed_at=None, progress=[progress])
    agent = MagicMock()
    agent.get_job.side_effect = [None, job]
    monkeypatch.setattr(module, "formatter_agent", agent)
    with pytest.raises(module.HTTPException) as exc:
        asyncio.run(module.get_job_status("missing", True))
    assert exc.value.status_code == 404
    result = asyncio.run(module.get_job_status("j", True))
    assert result["successful"] == 1 and result["progress"] == [{"step": "done"}]

    async def stream(_):
        yield progress
    agent.run_job = stream
    asyncio.run(module.run_job_background("j"))
