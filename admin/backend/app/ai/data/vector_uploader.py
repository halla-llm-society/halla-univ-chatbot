import os
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError, NetworkTimeout, PyMongoError
from bson import ObjectId
import certifi
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI
import tiktoken
import time
import logging
from typing import List, Dict
import argparse
import uuid  # ID 생성용
#from sentence_transformers import SentenceTransformer  # 추가: Ko-BGE용

# apikey.env를 명시적으로 로드 (기본 .env가 아닐 수 있음)
load_dotenv("apikey.env")
MONGODB_URI = os.getenv("MONGODB_URI")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# MongoDB 연결 (Atlas TLS 인증서 검증을 위해 certifi 사용)
if not MONGODB_URI:
    raise RuntimeError("환경변수 MONGODB_URI가 설정되지 않았습니다.")

def create_mongo_client():
    return MongoClient(
        MONGODB_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=20000,
        socketTimeoutMS=20000,
    )


client = create_mongo_client()
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

# 로거 설정
logger = logging.getLogger("vector_upload")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

# tiktoken 인코딩 (토큰 기반 분할에 사용)
enc = tiktoken.get_encoding('cl100k_base')
MAX_TOKENS_PER_CHUNK = 2000  # 업로드 전에 이보다 큰 덩어리는 분할
OVERLAP_TOKENS = 50

# OpenAI 임베딩 클라이언트
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def get_embedding(text: str) -> List[float]:
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"  # 비용/성능 균형 좋은 모델
    )
    return response.data[0].embedding


def split_text_into_token_chunks(text: str, max_tokens: int = MAX_TOKENS_PER_CHUNK, overlap: int = OVERLAP_TOKENS):
    """토큰 단위로 안전하게 텍스트를 분할해 문자열 조각 리스트를 반환합니다."""
    try:
        toks = enc.encode(text)
    except Exception:
        # 인코딩에 실패하면 간단히 문자 기반으로 대체 분할
        approx = max(1000, max_tokens * 3)
        return [text[i:i+approx] for i in range(0, len(text), approx)]

    chunks = []
    n = len(toks)
    start = 0
    while start < n:
        end = min(start + max_tokens, n)
        chunk_text = enc.decode(toks[start:end])
        chunks.append(chunk_text)
        if end >= n:
            break
        start = end - overlap
    return chunks


def safe_embed_and_upsert(text: str, metadata: Dict, namespace: str, batch_list: List[Dict], batch_size: int = 100):
    """텍스트를 안전히 분할해 임베딩하고 batch_list에 추가; batch가 차면 upsert 수행."""
    chunks = split_text_into_token_chunks(text)
    parts_embedded = 0
    embed_time_total = 0.0
    for idx, part in enumerate(chunks):
        start = time.monotonic()
        try:
            emb = get_embedding(part)
            elapsed = time.monotonic() - start
            embed_time_total += elapsed
            parts_embedded += 1
            logger.debug(f"embedded mongo_id={metadata.get('mongo_id')} sub={idx} tokens~{len(enc.encode(part))} time={elapsed:.3f}s")
        except Exception as e:
            elapsed = time.monotonic() - start
            logger.warning(f"get_embedding failed for mongo_id={metadata.get('mongo_id')} sub={idx} time={elapsed:.3f}s error={e}")
            continue

        vec_id = str(uuid.uuid4())
        md = dict(metadata or {})
        md["sub_index"] = idx
        md["text_preview"] = part[:200]
        batch_list.append({"id": vec_id, "values": emb, "metadata": md})

        if len(batch_list) >= batch_size:
            upsert_start = time.monotonic()
            index.upsert(vectors=batch_list, namespace=namespace or "default")
            upsert_elapsed = time.monotonic() - upsert_start
            logger.info(f"Upserted batch of {len(batch_list)} vectors to namespace={namespace} in {upsert_elapsed:.3f}s")
            batch_list.clear()

    logger.info(f"safe_embed_and_upsert finished mongo_id={metadata.get('mongo_id')} parts={parts_embedded} embed_time_total={embed_time_total:.3f}s")
    return batch_list

def upload_chunks_to_pinecone(category: str = None, batch_size: int = 100, dry_run: bool = False):
    """Mongo에서 청크를 읽어 안전 분할 후 Pinecone에 업로드합니다.
    네트워크 오류 발생 시 사용자에게 재시도 여부를 물어보고, 'y'이면 재접속 후 마지막 처리된 _id 이후로 재개합니다.
    """
    query = {"metadata.category": category} if category else {}

    # allow reassigning module-level client/db/collection on reconnect
    global client, db, collection

    batch = []
    total = 0
    total_parts = 0
    total_embed_time = 0.0
    total_upsert_time = 0.0
    errors = 0

    start_all = time.monotonic()
    last_id = None

    # cursor may be recreated after reconnect; use a while loop to allow resume
    while True:
        try:
            # create cursor, optionally resuming after last_id
            if last_id is not None:
                resume_query = dict(query)
                resume_query.update({"_id": {"$gt": ObjectId(last_id)}})
                cursor = collection.find(resume_query).sort([("_id", 1)])
            else:
                cursor = collection.find(query).sort([("_id", 1)])

            for doc in cursor:
                total += 1
                text = doc.get("text", "")
                metadata = dict(doc.get("metadata", {}))
                metadata["mongo_id"] = str(doc.get("_id"))

                try:
                    batch_before = len(batch)
                    batch = safe_embed_and_upsert(text, metadata, namespace=category or "default", batch_list=batch, batch_size=batch_size)
                    parts_added = len(batch) - batch_before if len(batch) >= batch_before else 0
                    total_parts += parts_added
                except Exception as e:
                    errors += 1
                    logger.exception(f"Error processing mongo_id={metadata.get('mongo_id')}: {e}")

                # remember last processed id for resume
                last_id = metadata.get("mongo_id")

                if total % 50 == 0:
                    logger.info(f"Processed {total} documents so far...")

                # If dry_run, log periodically
                if dry_run and total % 200 == 0:
                    logger.info(f"[DRY_RUN] processed {total} docs, current pending batch size {len(batch)}")

            # finished iteration without errors -> exit loop
            break

        except (ServerSelectionTimeoutError, NetworkTimeout, PyMongoError) as e:
            # Network or server selection error: prompt user to retry or abort
            logger.error(f"MongoDB connection error: {e}")
            answer = None
            while answer not in ("y", "n"):
                try:
                    answer = input("네트워크 오류 발생. 다시 시도하시겠습니까? (y/n): ").strip().lower()
                except KeyboardInterrupt:
                    answer = "n"
                    print()
                if answer not in ("y", "n"):
                    print("y 또는 n을 입력하세요.")

            if answer == "n":
                logger.info("User chose not to retry. Aborting upload.")
                break

            # attempt to recreate client and continue loop
            logger.info("Attempting to reconnect to MongoDB...")
            try:
                client = create_mongo_client()
                db = client["halla_academic_db"]
                collection = db["regulation_chunks"]
                logger.info("Reconnected to MongoDB, resuming...")
                # continue while loop to recreate cursor (with last_id resume)
                continue
            except Exception as re:
                logger.exception(f"Reconnection attempt failed: {re}")
                # prompt again in next loop iteration
                continue

    # 남아있는 배치 flush (실제 업서트는 dry_run False일 때만 수행)
    if batch:
        if dry_run:
            logger.info(f"[DRY_RUN] final pending vectors: {len(batch)} (not upserting)")
        else:
            upsert_start = time.monotonic()
            index.upsert(vectors=batch, namespace=category or "default")
            upsert_elapsed = time.monotonic() - upsert_start
            total_upsert_time += upsert_elapsed
            logger.info(f"Final upserted {len(batch)} vectors to namespace={category} in {upsert_elapsed:.3f}s")

    elapsed_all = time.monotonic() - start_all
    logger.info(f"upload_chunks_to_pinecone completed category={category} processed_documents={total} total_parts_estimate={total_parts} errors={errors} elapsed={elapsed_all:.3f}s")

    # 남아있는 배치 flush (실제 업서트는 dry_run False일 때만 수행)
    if batch:
        if dry_run:
            logger.info(f"[DRY_RUN] final pending vectors: {len(batch)} (not upserting)")
        else:
            upsert_start = time.monotonic()
            index.upsert(vectors=batch, namespace=category or "default")
            upsert_elapsed = time.monotonic() - upsert_start
            total_upsert_time += upsert_elapsed
            logger.info(f"Final upserted {len(batch)} vectors to namespace={category} in {upsert_elapsed:.3f}s")

    elapsed_all = time.monotonic() - start_all
    logger.info(f"upload_chunks_to_pinecone completed category={category} processed_documents={total} total_parts_estimate={total_parts} errors={errors} elapsed={elapsed_all:.3f}s")


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

