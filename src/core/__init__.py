"""Core functionality exposed through lazy imports."""

from importlib import import_module
_ENVIRONMENT_FACTORY_MODULE = ".environment_factory"

_EXPORTS = {
    "ConfigManager": (".config", "ConfigManager"),
    "RivaConfig": (".config", "RivaConfig"),
    "TranscriptionEnvironmentFactory": (_ENVIRONMENT_FACTORY_MODULE, "TranscriptionEnvironmentFactory"),
    "TranscriptionEnvironmentFactoryProvider": (_ENVIRONMENT_FACTORY_MODULE, "TranscriptionEnvironmentFactoryProvider"),
    "RivaLiveFactory": (_ENVIRONMENT_FACTORY_MODULE, "RivaLiveFactory"),
    "LocalBatchFactory": (_ENVIRONMENT_FACTORY_MODULE, "LocalBatchFactory"),
    "EnvironmentType": (_ENVIRONMENT_FACTORY_MODULE, "EnvironmentType"),
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
