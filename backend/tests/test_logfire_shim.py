"""Contract tests for the intentionally disabled local Logfire shim."""

import backend.logfire as shim


def test_instrument_supports_both_decorator_forms():
    def sample():
        return "ok"

    assert shim.instrument(sample) is sample
    assert shim.instrument("operation")(sample) is sample
    assert shim.instrument()(sample)() == "ok"


def test_noop_telemetry_functions_accept_realistic_arguments():
    functions = [
        shim.info,
        shim.error,
        shim.warn,
        shim.configure,
        shim.instrument_requests,
        shim.instrument_httpx,
        shim.instrument_pymongo,
        shim.instrument_pydantic_ai,
        shim.instrument_fastapi,
    ]
    for function in functions:
        assert function("event", enabled=True) is None


def test_dummy_span_behaves_as_non_suppressing_context_manager():
    context = shim.span("operation", request_id="qa")
    with context as entered:
        assert entered is context
        assert entered.child.attribute is context
        assert entered("argument") is context
    assert context.__exit__(ValueError, ValueError("boom"), None) is None


def test_logfire_compatibility_object_returns_callable_noops():
    client = shim.Logfire(token="ignored")
    assert client.span("operation").__enter__() is not None
    assert client.instrument("operation").__enter__() is not None
    assert client.any_other_method("value", key="value") is None
    assert isinstance(shim.LogfireSpan(), shim.LogfireSpan)
