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

def info(*args, **kwargs): pass
def error(*args, **kwargs): pass
def warn(*args, **kwargs): pass
def configure(*args, **kwargs): pass
def instrument_requests(*args, **kwargs): pass
def instrument_httpx(*args, **kwargs): pass
def instrument_pymongo(*args, **kwargs): pass
def instrument_pydantic_ai(*args, **kwargs): pass
def instrument_fastapi(*args, **kwargs): pass
class DummyContextManager:
    def __enter__(self): return self
    def __exit__(self, exc_type, exc_val, exc_tb): pass
    def __getattr__(self, name): return self
    def __call__(self, *args, **kwargs): return self

def span(*args, **kwargs): return DummyContextManager()

class LogfireSpan:
    """Dummy class to satisfy pydantic_ai internal imports."""
    pass

class Logfire:
    """Dummy Logfire object to silence pydantic-graph."""
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name):
        # Return a callable that does nothing, or a DummyContextManager for spans
        if name in ('span', 'instrument'):
            return span
        return lambda *args, **kwargs: None
