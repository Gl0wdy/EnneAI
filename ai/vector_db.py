from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer
from utils.logger import logger
from collections import defaultdict
from config import QDRANT_URL
import asyncio
import uuid


class VectorDb:
    def __init__(self):
        self.client = AsyncQdrantClient(QDRANT_URL)
        self.model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
        self.vector_dim = self.model.get_sentence_embedding_dimension()

    def _encode(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()

    async def _encode_async(self, text: str) -> list[float]:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._encode, text)

    async def create_collection(self, name: str = 'collection'):
        try:
            exists = await self.client.collection_exists(name)
            if not exists:
                await self.client.create_collection(
                    collection_name=name,
                    vectors_config=VectorParams(
                        size=self.vector_dim,
                        distance=Distance.COSINE
                    )
                )
        except Exception as err:
            logger.error('Error creating collection', exc_info=err)

    async def insert_data(self, collection_name: str = 'collection', *args):
        try:
            points = []
            for text in args:
                vector = await self._encode_async(text)
                points.append(PointStruct(
                    id=str(uuid.uuid4()), 
                    vector=vector,
                    payload={"text": text}
                ))
            await self.client.upsert(
                collection_name=collection_name,
                points=points
            )
        except Exception as err:
            logger.error('Error inserting data', exc_info=err)

    async def search(self, query: str, collection_name: str = 'collection') -> list[str] | None:
        try:
            hits = await self.client.query_points(
                collection_name=collection_name,
                query=await self._encode_async(query),
                limit=6,
                with_payload=True,
                score_threshold=0.5 
            )
            return [hit.payload['text'] for hit in hits.points]
        except Exception as err:
            logger.error('Error in search', exc_info=err)
            return None

    async def classify_search(self, query: str, collection_name: str = 'texts') -> str | None:
        try:
            query_vector = await self._encode_async(query)
            hits = await self.client.query_points( 
                collection_name=collection_name,
                query=query_vector,
                limit=10,
                with_payload=True
            )
            label_scores = defaultdict(float)
            for hit in hits.points:
                label_scores[hit.payload['label']] += hit.score

            if not label_scores:
                return None

            return max(label_scores.items(), key=lambda x: x[1])[0]
        except Exception as err:
            logger.error('Error in classify_search', exc_info=err)
            return None

    async def insert_classify_data(self, collection_name: str, data: list[tuple]):
        try:
            points = []
            for text, label in data:
                vector = await self._encode_async(text)
                points.append(PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={"label": label, "text": text}
                ))
            await self.client.upsert(collection_name=collection_name, points=points)
        except Exception as err:
            logger.error('Error inserting classify data', exc_info=err)

    async def get_collections(self):
        try:
            return await self.client.get_collections()
        except Exception as err:
            logger.error('Error getting collections', exc_info=err)
            return None

    async def delete_collections(self):
        try:
            collections = await self.client.get_collections()
            for collection in collections.collections:
                await self.client.delete_collection(collection.name)
        except Exception as err:
            logger.error('Error deleting collections', exc_info=err)