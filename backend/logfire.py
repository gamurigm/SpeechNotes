"""
Dummy logfire module to prevent crashes since the real logfire
was removed to stop the 401 spam. This shadows the missing package
so all existing `import logfire` and `@logfire.instrument` calls work.
"""

def instrument(*args, **kwargs):
    def decorator(func):
        return func
    # If used without parens: @logfire.instrument
    if len(args) == 1 and callable(args[0]):
        return args[0]
    # If used with parens: @logfire.instrument("name")
    return decorator

def info(*args, **kwargs):
    """Intentionally discard informational telemetry in the local shim."""
    return None


def error(*args, **kwargs):
    """Intentionally discard error telemetry in the local shim."""
    return None


def warn(*args, **kwargs):
    """Intentionally discard warning telemetry in the local shim."""
    return None


def configure(*args, **kwargs):
    """Accept Logfire configuration while telemetry is intentionally disabled."""
    return None


def instrument_requests(*args, **kwargs):
    """Leave Requests uninstrumented while telemetry is disabled."""
    return None


def instrument_httpx(*args, **kwargs):
    """Leave HTTPX uninstrumented while telemetry is disabled."""
    return None


def instrument_pymongo(*args, **kwargs):
    """Leave PyMongo uninstrumented while telemetry is disabled."""
    return None


def instrument_pydantic_ai(*args, **kwargs):
    """Leave Pydantic AI uninstrumented while telemetry is disabled."""
    return None


def instrument_fastapi(*args, **kwargs):
    """Leave FastAPI uninstrumented while telemetry is disabled."""
    return None


class DummyContextManager:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Never suppress exceptions raised inside the dummy span."""
        return None
    def __getattr__(self, name): return self
    def __call__(self, *args, **kwargs): return self

def span(*args, **kwargs): return DummyContextManager()

class LogfireSpan:
    """Dummy class to satisfy pydantic_ai internal imports."""
    # The compatibility type deliberately carries no state or behavior.

class Logfire:
    """Dummy Logfire object to silence pydantic-graph."""
    def __init__(self, *args, **kwargs):
        """Accept the real client's constructor arguments without side effects."""
        return None
    def __getattr__(self, name):
        # Return a callable that does nothing, or a DummyContextManager for spans
        if name in ('span', 'instrument'):
            return span
        return lambda *args, **kwargs: None
