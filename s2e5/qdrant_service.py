import os
import uuid

from qdrant_client import QdrantClient
from qdrant_client.http.models import PointStruct

# Initialize Qdrant client
qdrant_client = QdrantClient(url=os.getenv('QDRANT_URL'), api_key=os.getenv('QDRANT_API_KEY'))


# qdrant_client.create_collection(vectors_config=VectorParams(size=3072, distance='Cosine'), collection_name="ai_devs3")

def index_image(embedding, image_data):
    # Create point with embedding vector
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            'type': 'image',
            "name": image_data['name'],
            "desc": image_data['desc'],
            "context": image_data['context'],
        }
    )
    qdrant_client.upsert(collection_name="ai_devs3", points=[point])


def index_audio(embedding, audio_data):
    # Create point with embedding vector
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            'type': 'audio',
            "name": audio_data['name'],
            "transcript": audio_data['transcript'],
            "context": audio_data['context'],
        }
    )
    qdrant_client.upsert(collection_name="ai_devs3", points=[point])


def index_chunk(embedding, chunk_text):
    # Create point with embedding vector
    point = PointStruct(
        id=str(uuid.uuid4()),
        vector=embedding,
        payload={
            'type': 'text',
            'content': chunk_text
        }
    )
    qdrant_client.upsert(collection_name="ai_devs3", points=[point])


def search(embedding, limit=10):
    # Search for closest vectors
    search_result = qdrant_client.search(
        collection_name="ai_devs3",
        query_vector=embedding,
        limit=limit
    )

    results = []
    for result in search_result:
        # Add score and payload to results
        results.append({
            'score': result.score,
            'payload': result.payload
        })

    return results
