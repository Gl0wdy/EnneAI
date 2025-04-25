from ai.extractor import Extractor
from ai.vector_db import VectorDb
import asyncio


async def main():
    ex = Extractor()
    chunks = ex.extract_from_folder('/bots/EnneAI/data/books')
    print('1. Chunks extracted')

    db = VectorDb()
    await db.create_collection('naranjo')
    print('2. Collection created')
    await db.insert_data('naranjo', *chunks)
    print('3. Done!')


asyncio.run(main())