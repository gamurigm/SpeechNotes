import pytest
from unittest.mock import patch, MagicMock
from backend.services.nim.registry import NIMRegistry


def test_nim_registry_singleton():
    reg1 = NIMRegistry.instance()
    reg2 = NIMRegistry.instance()
    assert reg1 is reg2


def test_nim_registry_configs_registered():
    reg = NIMRegistry.instance()
    assert "thinking" in reg._configs
    assert "translator" in reg._configs
    assert "detector" in reg._configs
    assert "asr" in reg._configs
    assert "asr_es" in reg._configs
    assert "bnr" in reg._configs


def test_get_asr_locale_selection():
    reg = NIMRegistry.instance()
    
    with patch.object(reg, "get") as mock_get:
        mock_get.return_value = MagicMock()
        
        reg.get_asr("es-ES")
        mock_get.assert_called_with("asr_es")
        
        reg.get_asr("en-US")
        mock_get.assert_called_with("asr")


def test_get_unknown_config_raises_key_error():
    reg = NIMRegistry.instance()
    with pytest.raises(KeyError):
        reg.get("non_existent_config_123")
