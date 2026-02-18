import asyncio
import aiohttp

class ApiKey:
    def __init__(self, api_keys: str):
        self.main = None
        self.api_keys = api_keys.split(',')
        self.status = {k: None for k in self.api_keys}

    async def _check_key(self, api_key: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(
                 "https://gen.pollinations.ai/account/balance",
                 headers={
                     "Authorization": f"Bearer {api_key}"
                 }
            ) as response:
                json = await response.json()
                self.status[api_key] = float(json['balance'])
                print(self.status[api_key])
            
    async def update_status(self):
        tasks = (
            self._check_key(k) for k in self.api_keys
        )
        await asyncio.gather(*tasks)
        self.main = max(self.status, key=lambda x: self.status[x])