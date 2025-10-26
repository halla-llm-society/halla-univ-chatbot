import os
from dotenv import load_dotenv
from pymongo import MongoClient
import certifi
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
from typing import List, Dict
import argparse
import uuid  # ID 생성용
#from sentence_transformers import SentenceTransformer  # 추가: Ko-BGE용

# apikey.env를 명시적으로 로드 (기본 .env가 아닐 수 있음)
load_dotenv(".env")
MONGODB_URI = os.getenv("MONGODB_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MongoDB 연결 (Atlas TLS 인증서 검증을 위해 certifi 사용)
if not MONGODB_URI:
    raise RuntimeError("환경변수 MONGODB_URI가 설정되지 않았습니다.")

client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000,
    socketTimeoutMS=20000,
)
db = client["halla_academic_db"]
collection = db["regulation_chunks"]

# Pinecone 연결
pc = Pinecone(api_key=PINECONE_API_KEY)
index_name = "halla-academic-index"  # 인덱스 이름 (카테고리별 namespace 사용)

# 인덱스 생성 (이미 있으면 스킵)
if index_name not in pc.list_indexes().names():
    pc.create_index(
        name=index_name,
        dimension=1536,  # OpenAI 임베딩 차원  
        metric="cosine",
        spec=ServerlessSpec(cloud="aws", region="us-east-1")  # 당신의 리전으로 변경
    )
index = pc.Index(index_name)

# OpenAI 임베딩 클라이언트
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # 비용/성능 균형 좋은 모델
    )
    return response.data[0].embedding

def upload_chunks_to_pinecone(category: str = None, batch_size: int = 100):
    query = {"metadata.category": category} if category else {}
    chunks = list(collection.find(query))

    vectors = []
    for chunk in chunks:
        embedding = get_embedding(chunk["text"])
        vec_id = str(uuid.uuid4())  # Pinecone 벡터 식별자(별개)
        metadata = dict(chunk.get("metadata", {}))  # 안전 복사
        metadata["mongo_id"] = str(chunk["_id"])    # 핵심: Mongo _id 저장
        metadata["text_preview"] = chunk.get("text", "")[:100]

        vectors.append({"id": vec_id, "values": embedding, "metadata": metadata})
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors, namespace=category or "default")
            vectors.clear()

    if vectors:
        index.upsert(vectors=vectors, namespace=category or "default")
        print("최종 Batch 업로드 완료")


def main():
    parser = argparse.ArgumentParser(description="Upload Mongo chunks to Pinecone with mongo_id metadata")
    parser.add_argument("--category", dest="category", default=None, help="Category(namespace) to upload (e.g., law_articles, appendix_tables). If omitted, upload all.")
    parser.add_argument("--batch-size", dest="batch_size", type=int, default=100, help="Batch size for upserts")
    args = parser.parse_args()

    if args.category:
        upload_chunks_to_pinecone(category=args.category, batch_size=args.batch_size)
    else:
        # 업로드 대상이 명확하면 여기서 목록을 지정하세요
        for cat in ["law_articles", "appendix_tables"]:
            print(f"\n=== Uploading category: {cat} ===")
            upload_chunks_to_pinecone(category=cat, batch_size=args.batch_size)


if __name__ == "__main__":
    main()

