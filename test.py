import asyncio
from ai.vector_db import VectorDb
from ai.extractor import Extractor

async def main():
    db = VectorDb()
    ex = Extractor()

    await db.create_collection('naranjo')
    chunks = ex.extract_from_folder(r'D:\PYTHON\ADVANCED\EnneAI\data\books')
    print('extracted')
    await db.insert_data('naranjo', *chunks)

asyncio.run(main())