class KeyRotator:
    def __init__(self, keys=None):
        self.keys = list(keys or [])
        self.index = 0

    def add_key(self, key: str) -> None:
        if key and key not in self.keys:
            self.keys.append(key)

    def remove_key(self, key: str) -> None:
        if key in self.keys:
            self.keys.remove(key)
            self.index = 0

    def replace_keys(self, keys: list[str]) -> None:
        self.keys = list(keys)
        self.index = 0

    def _next(self):
        if not self.keys:
            raise ValueError("No API keys available")
        key = self.keys[self.index % len(self.keys)]
        self.index = (self.index + 1) % len(self.keys)
        return key

    async def rotate(self, fn, *args, **kwargs):
        if not self.keys:
            raise ValueError("No API keys available")

        last_error = None
        for _ in range(len(self.keys)):
            key = self._next()
            try:
                return await fn(*args, api_key=key, **kwargs)
            except Exception as exc:
                last_error = exc
        raise last_error