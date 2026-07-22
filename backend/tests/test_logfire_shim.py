import importlib.util
import sys
from pathlib import Path


def _load_shim():
    path = Path(__file__).resolve().parents[2] / "backend" / "logfire.py"
    name = "_qa_logfire_shim"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_logfire_shim_noop_functions_and_decorators():
    shim = _load_shim()
    for function in (
        shim.info, shim.error, shim.warn, shim.configure,
        shim.instrument_requests, shim.instrument_httpx,
        shim.instrument_pymongo, shim.instrument_pydantic_ai,
        shim.instrument_fastapi,
    ):
        assert function("value", key="value") is None

    @shim.instrument
    def plain():
        return "ok"

    @shim.instrument("named")
    def named():
        return "named"

    assert plain() == "ok" and named() == "named"


def test_logfire_shim_context_and_proxy_objects():
    shim = _load_shim()
    context = shim.span("test")
    assert context.__enter__() is context
    assert context.__exit__(None, None, None) is None
    assert context.any_method()("value") is context
    assert shim.LogfireSpan() is not None
    assert shim.Logfire().span("x") is context or shim.Logfire().span("x") is not None
