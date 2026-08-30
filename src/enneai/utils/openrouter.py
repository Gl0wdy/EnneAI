import aiohttp

async def check_openrouter_key(api_key: str) -> bool:
    url = "https://openrouter.ai/api/v1/auth/key"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
    except (aiohttp.ClientError, TimeoutError):
        return False