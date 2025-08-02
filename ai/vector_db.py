from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client import AsyncQdrantClient
from sentence_transformers import SentenceTransformer

from utils.logger import logger
from collections import defaultdict


class VectorDb:
    def __init__(self):
        self.client = AsyncQdrantClient("http://localhost:6333")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.vector_dim = self.model.get_sentence_embedding_dimension()
    
    async def create_collection(self, name: str = 'collection', **kwargs):
        exists = await self.client.collection_exists(name)
        if not exists:
            await self.client.create_collection(
                collection_name=name,
                vectors_config=VectorParams(size=self.vector_dim, distance=Distance.COSINE, **kwargs)
            )
    
    async def insert_data(self, collection_name: str = 'collection', *args):
        data = [self.model.encode(i).tolist() for i in args]
        await self.client.upsert(
            collection_name=collection_name,
            points=[
                PointStruct(
                        id=idx,
                        vector=vector,
                        payload={"text": args[idx]}
                )
                for idx, vector in enumerate(data)
            ]
        )

    async def search(self, query: str, collection_name: str = 'collection'):
        try:
            hits = await self.client.query_points(
                collection_name=collection_name,
                query=self.model.encode(query).tolist(),
                limit=6,
                with_payload=True
            )
        except Exception as err:
            logger.error('Error in ai/vector_db.py', exc_info=err)
            return
        return [hit.payload['text'] for hit in hits.points]
    

    async def classify_search(self, query: str, collection_name: str = 'texts'):
        query_vector = self.model.encode(query).tolist()
        hits = await self.client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=5
        )
        label_scores = defaultdict(float)
        for hit in hits:
            label = hit.payload['label']
            score = hit.score
            label_scores[label] += score
        predicted_label = max(label_scores.items(), key=lambda x: x[1])[0]
        return predicted_label

    async def insert_clasiffy_data(self, collection_name: str, data: list[tuple]):
        points = []
        for idx, (text, label) in enumerate(data):
            vector = self.model.encode(text).tolist()
            points.append(PointStruct(id=idx, vector=vector, payload={"label": label, "text": text}))

        await self.client.upsert(collection_name=collection_name, points=points)

    async def get_collections(self):
        collections = await self.client.get_collections()
        return collections

    async def delete_collections(self):
        collections = await self.client.get_collections()
        for collection in collections.collections:
            await self.client.delete_collection(collection.name)