from ai.extractor import Extractor
from ai.vector_db import VectorDb
from config import BASE_PATH

import asyncio


async def main():
    ex = Extractor()
    db = VectorDb()
    
    for catalog in ('socionics', 'ennea', 'psychosophy', 'jung', 'ichazo'):
        chunks = ex.extract_from_folder(BASE_PATH / f'data/{catalog}/dynamic')
        print('1. Chunks extracted')

        await db.client.delete_collection(catalog)
        await db.create_collection(catalog)
        print(f'2. Collection {catalog} created')
        await db.insert_data(catalog, *chunks)
        print('3. Done!')


asyncio.run(main())
