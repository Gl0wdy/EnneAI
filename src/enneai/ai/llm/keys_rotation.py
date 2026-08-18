class KeyRotator:
    def __init__(self, keys):
        self.keys = list(keys or []) # сюда пуллим ключи с монги (или просто массива)
        self.index = 0

    def _next(self): # инкапсулированный метод для ротатора
        if not self.keys:
            raise ValueError("No API keys available")
        key = self.keys[self.index % len(self.keys)]
        self.index = (self.index + 1) % len(self.keys)
        return key

    async def rotate(self, fn, *args, **kwargs): # в этот метод передается функция использующая ключи
        last_error = None
        for _ in range(len(self.keys)):
            key = self._next()
            try:
                return await fn(*args, api_key=key, **kwargs)
            except Exception as exc:
                last_error = exc
        if last_error:
            raise last_error
        raise ValueError("No API keys available")