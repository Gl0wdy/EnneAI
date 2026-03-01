import aiohttp
from .logger import logger

from config import ADV_TOKEN

async def show_advert(user_id: int):

    async with aiohttp.ClientSession() as session:

        async with session.post(
            'https://api.gramads.net/ad/SendPost',
            headers={
                'Authorization': f'Bearer {ADV_TOKEN}',
                'Content-Type': 'application/json',
            },
            json={'SendToChatId': user_id},
        ) as response:

            if not response.ok:

                logger.error('Gramads: %s' % str(await response.json()))