"""Core functionality exposed through lazy imports."""

from importlib import import_module

_EXPORTS = {
    "ConfigManager": (".config", "ConfigManager"),
    "RivaConfig": (".config", "RivaConfig"),
    "TranscriptionEnvironmentFactory": (".environment_factory", "TranscriptionEnvironmentFactory"),
    "TranscriptionEnvironmentFactoryProvider": (".environment_factory", "TranscriptionEnvironmentFactoryProvider"),
    "RivaLiveFactory": (".environment_factory", "RivaLiveFactory"),
    "LocalBatchFactory": (".environment_factory", "LocalBatchFactory"),
    "EnvironmentType": (".environment_factory", "EnvironmentType"),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    """Avoid initializing optional audio factories for unrelated imports."""
    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name, __name__), attribute)
    globals()[name] = value
    return value
