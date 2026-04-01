"""JSON serialization utilities with optional orjson support."""

from typing import Any

try:
    import orjson
    from orjson import JSONDecodeError

    def loads(data: str | bytes) -> Any:
        return orjson.loads(data)

    def dumps(obj: Any) -> str:
        return orjson.dumps(obj).decode()

    _USE_ORJSON = True
except ImportError:
    import json
    from json import JSONDecodeError

    def loads(data: str | bytes) -> Any:
        return json.loads(data)

    def dumps(obj: Any) -> str:
        return json.dumps(obj)

    _USE_ORJSON = False


def is_using_orjson() -> bool:
    return _USE_ORJSON
