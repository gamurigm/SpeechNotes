import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure mocks for optional imports
for mod in ["dotenv", "openai", "pymongo", "pymongo.collection", "pymongo.database", "pymongo.errors"]:
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from backend.services.agents.formatter_agent import FormatterAgent, StepStatus, FormatterProgress, FormatterJob


def test_step_status_enum():
    assert StepStatus.PENDING.value == "pending"
    assert StepStatus.COMPLETED.value == "completed"


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
