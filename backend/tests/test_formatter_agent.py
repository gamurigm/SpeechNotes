import sys
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock
import pytest
import asyncio

# Ensure mocks for optional dependencies in lightweight CI environment
for mod in [
    "dotenv",
    "openai",
    "pymongo",
    "pymongo.collection",
    "pymongo.database",
    "pymongo.errors",
    "src.database.mongo_manager",
]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

try:
    from backend.services.agents.formatter_agent import FormatterAgent, StepStatus, FormatterProgress, FormatterJob
    HAS_DEPS = True
except Exception:
    HAS_DEPS = False


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_step_status_enum():
    assert StepStatus.PENDING.value == "pending"
    assert StepStatus.COMPLETED.value == "completed"


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_progress_to_dict():
    prog = FormatterProgress(
        job_id="job-123",
        current=1,
        total=5,
        file_name="doc1.md",
        status="formatting",
        output_path="db://doc1"
    )
    d = prog.to_dict()
    assert d["job_id"] == "job-123"
    assert d["status"] == "formatting"
    assert d["current"] == 1
    assert d["total"] == 5


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_create_and_get_job(tmp_path):
    mock_config = MagicMock()
    mock_config.get.return_value = None
    
    with patch("src.database.config_service.ConfigService", return_value=mock_config):
        agent = FormatterAgent(project_root=tmp_path)
        job_id = agent.create_job(["doc1", "doc2"])
        
        job = agent.get_job(job_id)
        assert job is not None
        assert job.files == ["doc1", "doc2"]
        assert job.status == "pending"


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_local_format():
    mock_config = MagicMock()
    mock_config.get.return_value = None

    with patch("src.database.config_service.ConfigService", return_value=mock_config):
        agent = FormatterAgent(project_root=Path("."))
        
        file_data = {
            "clean_content": "Esta es una introduccion a la clase de fisica. **[00:00:00]** Hablamos de la ley de gravedad.\n\n"
                            "En el segundo bloque explicamos la aceleracion y la masa de los objetos."
        }
        
        res = agent._local_format(file_data)
        assert "## Resumen Ejecutivo" in res
        assert "## Puntos Clave" in res
        assert "## Desarrollo Detallado" in res


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_run_job_success_and_error(tmp_path):
    mock_config = MagicMock()
    mock_config.get.return_value = None

    async def collect(agent, job_id):
        return [item async for item in agent.run_job(job_id)]

    with patch("src.database.config_service.ConfigService", return_value=mock_config):
        agent = FormatterAgent(project_root=tmp_path)
        job_id = agent.create_job(["ok", "bad"])
        agent._read_db_step = AsyncMock(side_effect=[
            {"file_name": "ok.md", "metadata": {}, "clean_content": "ok"},
            RuntimeError("read failed"),
        ])
        agent._format_step = AsyncMock(return_value="formatted")
        agent._save_db_step = AsyncMock()
        progress = asyncio.run(collect(agent, job_id))
        assert [item.status for item in progress] == ["reading", "formatting", "saving", "completed", "reading", "error"], progress
        assert agent.jobs[job_id].successful == 1
        assert agent.jobs[job_id].failed == 1
        assert agent.jobs[job_id].status == "completed"
        assert agent.get_job("missing") is None


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_read_db_step_cleans_content_and_retries(tmp_path):
    mock_config = MagicMock()
    mock_config.get.return_value = None
    database = MagicMock()
    database.transcriptions.find_one.return_value = {
        "_id": "doc", "filename": "clase.md", "raw_content": "**[00:00:01]** Hola\n\n\nMundo",
        "date": "2026-01-01", "word_count": 2, "source_type": "live",
    }
    with patch("src.database.config_service.ConfigService", return_value=mock_config), \
         patch("backend.services.agents.formatter_agent.MongoManager", return_value=database):
        agent = FormatterAgent(project_root=tmp_path)
        result = asyncio.run(agent._read_db_step("doc", max_retries=0))
        assert result["clean_content"] == "Hola\n\nMundo"
        assert result["metadata"]["tipo"] == "live"


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_read_db_rejects_missing_and_local_format_fallback(tmp_path):
    mock_config = MagicMock()
    mock_config.get.return_value = None
    database = MagicMock()
    database.transcriptions.find_one.return_value = None
    with patch("src.database.config_service.ConfigService", return_value=mock_config), \
         patch("backend.services.agents.formatter_agent.MongoManager", return_value=database):
        agent = FormatterAgent(project_root=tmp_path)
        with pytest.raises(FileNotFoundError):
            asyncio.run(agent._read_db_step("missing", max_retries=0))
        result = asyncio.run(agent._format_step({"file_name": "x", "clean_content": "texto", "metadata": {}}))
        assert "## Conclusiones" in result


@pytest.mark.skipif(not HAS_DEPS, reason="Dependencies missing in test environment")
def test_formatter_agent_save_db_all_branches(tmp_path):
    mock_config = MagicMock()
    mock_config.get.return_value = None
    database = MagicMock()
    result = MagicMock(modified_count=1)
    database.transcriptions.update_one.return_value = result
    with patch("src.database.config_service.ConfigService", return_value=mock_config), \
         patch("backend.services.agents.formatter_agent.MongoManager", return_value=database):
        agent = FormatterAgent(project_root=tmp_path)
        asyncio.run(agent._save_db_step("doc", "formatted", max_retries=0))
        database.transcriptions.update_one.assert_called_once()

        database.transcriptions.update_one.reset_mock()
        database.transcriptions.update_one.return_value = MagicMock(modified_count=0)
        database.transcriptions.find_one.return_value = {"_id": "doc"}
        asyncio.run(agent._save_db_step("doc", "same", max_retries=0))
        database.transcriptions.find_one.assert_called_once()

        database.transcriptions.find_one.return_value = None
        asyncio.run(agent._save_db_step("new", "new content", max_retries=0))
        database.transcriptions.insert_one.assert_called_once()
