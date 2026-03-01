import logging
import aiohttp
from config import ADV_TOKEN

# Call this method wherever you want to show an ad,
# for example your bot just made its job and
# it's a great time to show an ad to a user

log = logging.getLogger('adverts')

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

                log.error('Gramads: %s' % str(await response.json()))