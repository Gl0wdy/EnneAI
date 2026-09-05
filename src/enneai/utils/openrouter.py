import asyncio

import aiohttp

async def check_openrouter_key(api_key: str) -> bool:
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        timeout = aiohttp.ClientTimeout(
            total=5,
            connect=5,
            sock_connect=5,
            sock_read=5,
        )
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers=headers) as response:
                return response.status == 200
    except (aiohttp.ClientError, asyncio.TimeoutError):
        return False