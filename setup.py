from ai.extractor import Extractor
from ai.vector_db import VectorDb
from ai.utils import get_classifier_data
import asyncio


async def main():
    ex = Extractor()
    db = VectorDb()
    
    for catalog in ('socionics', 'ennea', 'psychosophy'):
        chunks = ex.extract_from_folder(f'/root/bots/EnneAI/data/books/{catalog}')
        print('1. Chunks extracted')

        await db.client.delete_collection(catalog)
        await db.create_collection(catalog)
        print(f'2. Collection {catalog} created')
        await db.insert_data(catalog, *chunks)
        print('3. Done!')

    await db.client.delete_collection('texts')
    await db.create_collection('texts')

    train_json = get_classifier_data()
    total_train = []
    for key, val in train_json.items():
        print(key)
        for i in val['data']:
            total_train.append((i, key))

    await db.insert_clasiffy_data('texts', total_train)
    while True:
        query = input('Your input: ')
        res = await db.classify_search(query, 'texts')
        print(f'> This is {res}')


asyncio.run(main())
