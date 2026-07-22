from unittest.mock import MagicMock

import backend.tracing as tracing


def test_init_tracing_handles_missing_logfire_or_token(monkeypatch, capsys):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: {
        "LOGFIRE_TOKEN": "token",
        "LOGFIRE_PROJECT_NAME": "project",
        "OTEL_SERVICE_NAME": "service",
    }.get(key, default)
    monkeypatch.setattr("src.database.config_service.ConfigService", MagicMock(return_value=config))
    monkeypatch.setattr(tracing, "logfire", None)
    tracing.init_tracing()
    assert "not installed" in capsys.readouterr().out

    monkeypatch.setattr(tracing, "logfire", MagicMock())
    config.get.side_effect = lambda key, default=None: None if key == "LOGFIRE_TOKEN" else default
    tracing.init_tracing()
    assert "token not found" in capsys.readouterr().out


def test_init_tracing_configures_all_integrations(monkeypatch):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: "token" if key == "LOGFIRE_TOKEN" else default
    logfire = MagicMock()
    monkeypatch.setattr("src.database.config_service.ConfigService", MagicMock(return_value=config))
    monkeypatch.setattr(tracing, "logfire", logfire)

    tracing.init_tracing("qa-service")

    logfire.configure.assert_called_once_with(
        token="token", service_name="qa-service", send_to_logfire=True
    )
    logfire.instrument_requests.assert_called_once_with()
    logfire.instrument_httpx.assert_called_once_with()
    logfire.instrument_pymongo.assert_called_once_with()
    logfire.instrument_pydantic_ai.assert_called_once_with()


def test_init_tracing_contains_instrumentation_error(monkeypatch, capsys):
    config = MagicMock()
    config.get.side_effect = lambda key, default=None: "token" if key == "LOGFIRE_TOKEN" else default
    logfire = MagicMock()
    logfire.instrument_requests.side_effect = RuntimeError("unsupported")
    monkeypatch.setattr("src.database.config_service.ConfigService", MagicMock(return_value=config))
    monkeypatch.setattr(tracing, "logfire", logfire)

    tracing.init_tracing()

    assert "Error during Logfire instrumentation" in capsys.readouterr().out


def test_instrument_fastapi_handles_all_states(monkeypatch, capsys):
    monkeypatch.setattr(tracing, "logfire", None)
    assert tracing.instrument_fastapi("app") is None

    logfire = MagicMock()
    monkeypatch.setattr(tracing, "logfire", logfire)
    tracing.instrument_fastapi("app")
    logfire.instrument_fastapi.assert_called_once_with("app")

    logfire.instrument_fastapi.side_effect = RuntimeError("unsupported")
    tracing.instrument_fastapi("app")
    assert "Failed to instrument FastAPI" in capsys.readouterr().out
