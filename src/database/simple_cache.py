from typing import Any


class SimpleCache:
    def __init__(self):
        self._data: dict[str, Any] = {}

    async def get(self, key: str) -> str | None:
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self._data[key] = value

    async def incr(self, key: str) -> int:
        self._data[key] = str(int(self._data.get(key, "0")) + 1)
        return int(self._data[key])

    async def expire(self, key: str, seconds: int):
        pass

    async def pipeline(self):
        return SimpleCachePipe(self._data)

    async def ping(self):
        return True


class SimpleCachePipe:
    def __init__(self, data: dict):
        self._data = data
        self._ops = []

    def incr(self, key: str):
        self._ops.append(("incr", key))
        return self

    def expire(self, key: str, seconds: int):
        self._ops.append(("expire", key, seconds))
        return self

    async def execute(self):
        for op in self._ops:
            if op[0] == "incr":
                self._data[op[1]] = str(int(self._data.get(op[1], "0")) + 1)
