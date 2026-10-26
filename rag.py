from qdrant_client import QdrantClient
from qdrant_client.http import models
import requests

qdrant_client = QdrantClient(path="./qdrant_storage")
COLLECTION_NAME = "customer_records"

def init_vector_db():
    collections = [c.name for c in qdrant_client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        qdrant_client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE)
        )

def get_embedding(text: str) -> list:
    response = requests.post(
        "http://localhost:11434/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": text}
    )
    if response.status_code == 200:
        return response.json().get("embedding")
    raise Exception("Embedding generation failed.")

def index_invoice_record(customer_id: int, invoice_id: int, invoice_number: str, date: str, amount: float, currency: str, status: str):
    init_vector_db()
    text_content = f"Invoice Number: {invoice_number}, Date: {date}, Amount: {amount} {currency}, Status: {status}, Customer ID: {customer_id}"
    vector = get_embedding(text_content)
    
    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=[
            models.PointStruct(
                id=invoice_id,
                vector=vector,
                payload={
                    "customer_id": customer_id,
                    "invoice_id": invoice_id,
                    "invoice_number": invoice_number,
                    "content": text_content
                }
            )
        ]
    )

def search_customer_records(customer_id: int, query_text: str, limit: int = 3):
    init_vector_db()
    try:
        query_vector = get_embedding(query_text)
        # MANDATORY CUSTOMER FILTER: Prevent cross-customer data leakage
        search_result = qdrant_client.search(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="customer_id",
                        match=models.MatchValue(value=customer_id)
                    )
                ]
            ),
            limit=limit
        )
        return [{"invoice_id": hit.payload["invoice_id"], "invoice_number": hit.payload["invoice_number"], "content": hit.payload["content"]} for hit in search_result]
    except Exception as e:
        print(f"Retrieval error: {e}")
        return []