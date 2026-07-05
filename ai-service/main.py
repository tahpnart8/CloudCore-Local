"""
CloudCore AI — Product Embedding & Recommendation Service
──────────────────────────────────────────────────────────
Endpoints:
  GET  /health     → Health check (K8s liveness probe)
  POST /embed      → Tạo embedding vector từ text bất kỳ
  POST /catalog    → Thêm sản phẩm vào kho (Streaming Consumer gọi)
  POST /recommend  → Gợi ý sản phẩm tương tự (cosine similarity)
"""
from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np
from sentence_transformers import SentenceTransformer
import os

app = FastAPI(
    title="CloudCore AI Service",
    description="Product embedding & recommendation"
)

MODEL_NAME = os.getenv("MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2")
model = SentenceTransformer(MODEL_NAME)

# Kho sản phẩm in-memory: {product_id: {"name": ..., "vector": ...}}
product_catalog = {}

class TextInput(BaseModel):
    text: str

class EmbeddingOutput(BaseModel):
    embedding: list[float]
    model: str
    dimensions: int

class ProductInput(BaseModel):
    product_id: str
    name: str

class RecommendInput(BaseModel):
    text: str
    top_k: int = 3

@app.get("/health")
def health():
    return {"status": "healthy", "model": MODEL_NAME,
            "catalog_size": len(product_catalog)}

@app.post("/embed", response_model=EmbeddingOutput)
def embed(input: TextInput):
    """Tạo embedding vector từ text bất kỳ."""
    vector = model.encode(input.text).tolist()
    return EmbeddingOutput(
        embedding=vector, model=MODEL_NAME, dimensions=len(vector))

@app.post("/catalog")
def add_to_catalog(product: ProductInput):
    """Thêm sản phẩm — Consumer từ streaming pipeline sẽ gọi endpoint này."""
    vector = model.encode(product.name)
    product_catalog[product.product_id] = {
        "name": product.name, "vector": vector}
    return {"status": "added", "product_id": product.product_id,
            "catalog_size": len(product_catalog)}

@app.post("/recommend")
def recommend(input: RecommendInput):
    """Gợi ý sản phẩm tương tự bằng cosine similarity."""
    if not product_catalog:
        return {"recommendations": [], "message": "Catalog is empty"}
    query_vec = model.encode(input.text)
    results = []
    for pid, data in product_catalog.items():
        cos_sim = float(np.dot(query_vec, data["vector"]) / (
            np.linalg.norm(query_vec) * np.linalg.norm(data["vector"])))
        results.append({"product_id": pid, "name": data["name"],
                        "similarity": round(cos_sim * 100, 1)})
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return {"query": input.text, "recommendations": results[:input.top_k]}
