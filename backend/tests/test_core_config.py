import os

import pytest

from src.core.config import ConfigManager, RivaConfig


@pytest.fixture(autouse=True)
def reset_config_manager():
    ConfigManager.reset_instance()
    yield
    ConfigManager.reset_instance()


def test_riva_config_validates_required_values():
    with pytest.raises(ValueError, match="API_KEY"):
        RivaConfig(api_key="", server="server", function_id="fn")
    with pytest.raises(ValueError, match="RIVA_FUNCTION_ID_WHISPER"):
        RivaConfig(api_key="key", server="server", function_id="")


def test_config_manager_loads_env_and_is_a_singleton(tmp_path, monkeypatch):
    env_file = tmp_path / ".env"
    env_file.write_text(
        "# ignored\nAPI_KEY='test-key'\nRIVA_FUNCTION_ID_WHISPER=fn-1\n"
        'QUOTED="hello world"\nINVALID_LINE\n',
        encoding="utf-8",
    )
    for key in ("API_KEY", "RIVA_FUNCTION_ID_WHISPER", "QUOTED"):
        monkeypatch.delenv(key, raising=False)

    manager = ConfigManager(env_file)
    same_manager = ConfigManager(tmp_path / "unused.env")

    assert same_manager is manager
    assert manager.get("QUOTED") == "hello world"
    assert manager.get("MISSING", "fallback") == "fallback"
    assert manager.get_riva_config() == RivaConfig(
        api_key="test-key",
        server="grpc.nvcf.nvidia.com:443",
        function_id="fn-1",
    )
    assert ConfigManager.get_instance() is manager


def test_config_manager_rejects_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match=".env file not found"):
        ConfigManager(tmp_path / "missing.env")


def test_find_env_file_points_to_project_root():
    assert ConfigManager._find_env_file().name == ".env"
    assert ConfigManager._find_env_file().parent.name == "SpeechNotes"
