"""
MongoDB Vector Search를 위한 embedding 필드 추가 스크립트

사용법:
    # 테스트 (10개 문서만)
    python app/ai/data/add_embeddings.py --test

    # 전체 실행
    python app/ai/data/add_embeddings.py

    # 특정 개수만 실행
    python app/ai/data/add_embeddings.py --limit 100
"""

import os
import sys
import time
import argparse
from typing import List
from dotenv import load_dotenv
from pymongo import MongoClient
from openai import OpenAI
import certifi

# 환경변수 로드
load_dotenv("app/apikey.env")

MONGODB_URI = os.getenv("MONGODB_URI")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DB_NAME = os.getenv("MONGO_DB_NAME", "halla-chatbot-stg")
COLLECTION_NAME = "regulation_chunks"

# OpenAI 클라이언트
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# MongoDB 클라이언트
mongo_client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]


def get_embedding(text: str) -> List[float]:
    """OpenAI text-embedding-3-small 모델로 임베딩 생성"""
    response = openai_client.embeddings.create(
        input=text,
        model="text-embedding-3-small"
    )
    return response.data[0].embedding


def add_embeddings(limit: int = None, test_mode: bool = False, batch_size: int = 50):
    """모든 문서에 embedding 필드 추가 (배치 처리 방식)

    커서 타임아웃 방지를 위해 배치 단위로 _id만 조회 후 개별 처리
    """

    if test_mode:
        limit = 10
        print("=" * 50)
        print("테스트 모드: 10개 문서만 처리")
        print("=" * 50)

    # embedding이 없는 문서만 조회
    query = {"embedding": {"$exists": False}}

    total_without_embedding = collection.count_documents(query)
    print(f"\n[정보] embedding 없는 문서: {total_without_embedding}개")

    if total_without_embedding == 0:
        print("모든 문서에 이미 embedding이 있습니다.")
        return

    # 처리할 총 개수 결정
    total_to_process = min(limit, total_without_embedding) if limit else total_without_embedding
    print(f"[정보] 처리할 문서 수: {total_to_process}개")
    print(f"[정보] 배치 크기: {batch_size}개")

    processed = 0
    errors = 0
    start_time = time.time()

    print("\n[시작] Embedding 추가 작업 시작...")
    print("-" * 50)

    # 배치 처리: 커서 타임아웃 방지
    while processed + errors < total_to_process:
        # 매 배치마다 새로운 쿼리로 _id만 조회 (빠름)
        remaining = total_to_process - (processed + errors)
        current_batch_size = min(batch_size, remaining)

        # _id만 조회하여 빠르게 가져옴
        doc_ids = list(collection.find(
            {"embedding": {"$exists": False}},
            {"_id": 1}
        ).limit(current_batch_size))

        if not doc_ids:
            print("  [정보] 더 이상 처리할 문서 없음")
            break

        for doc_ref in doc_ids:
            doc_id = doc_ref["_id"]

            # 개별 문서 조회
            doc = collection.find_one({"_id": doc_id})
            if not doc:
                continue

            text = doc.get("text", "")

            if not text:
                print(f"  ⚠️ 빈 텍스트: {doc_id}")
                errors += 1
                continue

            try:
                # 임베딩 생성
                embedding = get_embedding(text)

                # MongoDB에 업데이트
                collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"embedding": embedding}}
                )

                processed += 1

                # 진행 상황 출력 (50개마다)
                if processed % 50 == 0:
                    elapsed = time.time() - start_time
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining_docs = total_to_process - processed - errors
                    eta = remaining_docs / rate if rate > 0 else 0
                    print(f"  ✓ {processed}/{total_to_process}개 완료 ({rate:.1f} docs/s, 예상 남은 시간: {eta/60:.1f}분)")

            except Exception as e:
                print(f"  ❌ 오류 ({doc_id}): {e}")
                errors += 1
                continue

        # 배치 완료 후 잠시 대기 (Rate limit 방지)
        time.sleep(0.5)

    elapsed = time.time() - start_time

    print("-" * 50)
    print(f"\n[완료] Embedding 추가 작업 완료!")
    print(f"  - 처리: {processed}개")
    print(f"  - 오류: {errors}개")
    print(f"  - 소요 시간: {elapsed:.1f}초 ({elapsed/60:.1f}분)")
    if processed > 0:
        print(f"  - 평균 속도: {processed/elapsed:.2f} docs/s")

    # 최종 확인
    with_embedding = collection.count_documents({"embedding": {"$exists": True}})
    without_embedding = collection.count_documents({"embedding": {"$exists": False}})
    print(f"\n[현황]")
    print(f"  - embedding 있음: {with_embedding}개")
    print(f"  - embedding 없음: {without_embedding}개")


def verify_embeddings():
    """embedding 필드 검증"""
    print("\n[검증] Embedding 필드 검증...")

    # 샘플 문서 확인
    sample = collection.find_one({"embedding": {"$exists": True}})
    if sample:
        embedding = sample.get("embedding", [])
        print(f"  - 샘플 문서 ID: {sample['_id']}")
        print(f"  - embedding 차원: {len(embedding)}")
        print(f"  - embedding 타입: {type(embedding)}")
        print(f"  - 첫 5개 값: {embedding[:5]}")

        if len(embedding) == 1536:
            print("  ✅ 차원 검증 통과 (1536)")
        else:
            print(f"  ❌ 차원 불일치! 예상: 1536, 실제: {len(embedding)}")
    else:
        print("  ❌ embedding 있는 문서를 찾을 수 없습니다.")


def main():
    parser = argparse.ArgumentParser(description="MongoDB 문서에 embedding 필드 추가")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (10개 문서만)")
    parser.add_argument("--limit", type=int, help="처리할 문서 수 제한")
    parser.add_argument("--verify", action="store_true", help="embedding 검증만 실행")
    args = parser.parse_args()

    print("=" * 50)
    print("MongoDB Vector Search - Embedding 추가 스크립트")
    print("=" * 50)
    print(f"DB: {DB_NAME}")
    print(f"Collection: {COLLECTION_NAME}")

    if args.verify:
        verify_embeddings()
        return

    add_embeddings(limit=args.limit, test_mode=args.test)
    verify_embeddings()


if __name__ == "__main__":
    main()
