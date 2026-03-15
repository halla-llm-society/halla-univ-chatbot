"""
8192 토큰 초과 문서를 청크로 분할하는 스크립트

분할 전략:
1. 별표/부칙 경계에서 의미 단위로 분리
2. 각 청크가 7500토큰 이하가 되도록 조정
3. 원본 문서는 유지하고 새 청크 문서 추가
4. 청크 문서에는 parent_id로 원본 참조

사용법:
    # 테스트 (dry-run)
    python app/ai/data/chunk_large_docs.py --test

    # 실제 실행
    python app/ai/data/chunk_large_docs.py
"""

import os
import re
import time
import argparse
from typing import List, Dict, Tuple, Any
from dotenv import load_dotenv
from pymongo import MongoClient
from bson import ObjectId
import certifi
import tiktoken

# 환경변수 로드
load_dotenv("app/apikey.env")

MONGODB_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "halla-chatbot-stg")
COLLECTION_NAME = "regulation_chunks"

# MongoDB 클라이언트
mongo_client = MongoClient(
    MONGODB_URI,
    tls=True,
    tlsCAFile=certifi.where(),
    serverSelectionTimeoutMS=30000,
)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# tiktoken 인코더
enc = tiktoken.get_encoding('cl100k_base')

# 청크 최대 토큰 수 (8192 제한 대비 여유)
MAX_CHUNK_TOKENS = 7500


def count_tokens(text: str) -> int:
    """텍스트의 토큰 수 계산"""
    return len(enc.encode(text))


def find_split_points(text: str) -> List[Tuple[int, str]]:
    """
    텍스트에서 분리 포인트 찾기 (별표 단위만)

    전략:
    - 별표 단위로만 분리 (의미 있는 큰 단위)
    - 부칙은 분리하지 않음 (너무 잘게 쪼개짐)

    Returns:
        List of (position, marker_type) tuples
    """
    patterns = [
        (r'<별표\s*(\d+)>', 'table'),
        (r'\[별표\s*(\d+)\]', 'table'),
        # 줄 시작 부분의 "별표 N" 형태만 (본문 중간에 언급된 건 제외)
        (r'(?:^|\n)\s*(별표\s*\d+)', 'table'),
    ]

    matches = []
    for pattern, marker_type in patterns:
        for match in re.finditer(pattern, text):
            matches.append((match.start(), marker_type, match.group()))

    # 위치순 정렬
    matches.sort(key=lambda x: x[0])

    # 중복 제거 (같은 위치 근처 50자 이내)
    filtered = []
    last_pos = -100
    for pos, mtype, mtext in matches:
        if pos - last_pos > 50:  # 50자 이상 떨어진 경우만
            filtered.append((pos, mtype, mtext))
            last_pos = pos

    return filtered


def split_by_semantic_units(text: str, metadata: Dict) -> List[Dict]:
    """
    의미 단위로 텍스트 분할

    전략:
    1. 별표/부칙 경계에서 1차 분할
    2. 각 조각이 MAX_CHUNK_TOKENS 초과시 강제 분할
    """
    total_tokens = count_tokens(text)

    if total_tokens <= MAX_CHUNK_TOKENS:
        # 분할 필요 없음
        return [{
            'text': text,
            'metadata': metadata,
            'chunk_info': {'index': 0, 'total': 1, 'type': 'full'}
        }]

    # 분리 포인트 찾기
    split_points = find_split_points(text)

    if not split_points:
        # 분리 포인트 없으면 강제 분할
        return split_by_token_limit(text, metadata)

    # 분리 포인트에서 분할
    chunks = []
    positions = [0] + [p[0] for p in split_points] + [len(text)]

    for i in range(len(positions) - 1):
        start = positions[i]
        end = positions[i + 1]
        chunk_text = text[start:end].strip()

        if not chunk_text:
            continue

        chunk_tokens = count_tokens(chunk_text)

        if chunk_tokens <= MAX_CHUNK_TOKENS:
            # 청크 타입 결정
            if i < len(split_points):
                chunk_type = split_points[i][1] if i > 0 else 'main'
            else:
                chunk_type = 'tail'

            chunks.append({
                'text': chunk_text,
                'metadata': metadata.copy(),
                'chunk_info': {'type': chunk_type}
            })
        else:
            # 아직 큰 경우 추가 분할
            sub_chunks = split_by_token_limit(chunk_text, metadata)
            chunks.extend(sub_chunks)

    # 인덱스 부여
    for i, chunk in enumerate(chunks):
        chunk['chunk_info']['index'] = i
        chunk['chunk_info']['total'] = len(chunks)

    return chunks


def split_by_token_limit(text: str, metadata: Dict) -> List[Dict]:
    """
    토큰 제한으로 강제 분할 (줄바꿈 기준)
    """
    lines = text.split('\n')
    chunks = []
    current_chunk = []
    current_tokens = 0

    for line in lines:
        line_tokens = count_tokens(line)

        if current_tokens + line_tokens > MAX_CHUNK_TOKENS:
            if current_chunk:
                chunk_text = '\n'.join(current_chunk)
                chunks.append({
                    'text': chunk_text,
                    'metadata': metadata.copy(),
                    'chunk_info': {'type': 'split'}
                })
            current_chunk = [line]
            current_tokens = line_tokens
        else:
            current_chunk.append(line)
            current_tokens += line_tokens

    # 마지막 청크
    if current_chunk:
        chunk_text = '\n'.join(current_chunk)
        chunks.append({
            'text': chunk_text,
            'metadata': metadata.copy(),
            'chunk_info': {'type': 'split'}
        })

    # 인덱스 부여
    for i, chunk in enumerate(chunks):
        chunk['chunk_info']['index'] = i
        chunk['chunk_info']['total'] = len(chunks)

    return chunks


def process_large_documents(dry_run: bool = True):
    """
    8192 토큰 초과 문서 처리
    """
    print("=" * 60)
    print("대용량 문서 청킹 스크립트")
    print("=" * 60)

    if dry_run:
        print("[모드] DRY-RUN (실제 DB 변경 없음)")
    else:
        print("[모드] 실제 실행")

    # embedding 없고 토큰 초과인 문서 조회
    docs = list(collection.find(
        {'embedding': {'$exists': False}},
        {'_id': 1, 'text': 1, 'metadata': 1}
    ))

    large_docs = []
    for doc in docs:
        text = doc.get('text', '')
        tokens = count_tokens(text)
        if tokens > 8192:
            large_docs.append((tokens, doc))

    large_docs.sort(reverse=True)

    print(f"\n[정보] 8192 토큰 초과 문서: {len(large_docs)}개")

    if not large_docs:
        print("처리할 문서가 없습니다.")
        return

    total_chunks_created = 0

    for i, (tokens, doc) in enumerate(large_docs, 1):
        doc_id = doc['_id']
        text = doc.get('text', '')
        metadata = doc.get('metadata', {})

        source_file = metadata.get('source_file', 'N/A')[:40]
        law_id = metadata.get('law_article_id', 'N/A')

        print(f"\n[{i}/{len(large_docs)}] {source_file}")
        print(f"  원본: {tokens:,} 토큰, law_article_id: {law_id}")

        # 청크 분할
        chunks = split_by_semantic_units(text, metadata)

        print(f"  → {len(chunks)}개 청크로 분할")

        for j, chunk in enumerate(chunks):
            chunk_tokens = count_tokens(chunk['text'])
            chunk_type = chunk['chunk_info'].get('type', 'unknown')
            print(f"     청크 {j+1}: {chunk_tokens:,} 토큰 ({chunk_type})")

            if not dry_run:
                # 새 문서 생성
                new_doc = {
                    'text': chunk['text'],
                    'metadata': {
                        **chunk['metadata'],
                        'parent_id': str(doc_id),
                        'chunk_index': chunk['chunk_info']['index'],
                        'chunk_total': chunk['chunk_info']['total'],
                        'chunk_type': chunk_type,
                    }
                }
                collection.insert_one(new_doc)
                total_chunks_created += 1

        if not dry_run:
            # 원본 문서에 chunked 표시
            collection.update_one(
                {'_id': doc_id},
                {'$set': {'chunked': True, 'chunk_count': len(chunks)}}
            )

    print("\n" + "=" * 60)
    if dry_run:
        print("[완료] DRY-RUN 완료 - 실제 변경 없음")
        print("       실제 실행: python app/ai/data/chunk_large_docs.py")
    else:
        print(f"[완료] {total_chunks_created}개 청크 문서 생성됨")

        # 통계 출력
        total_docs = collection.count_documents({})
        with_embedding = collection.count_documents({'embedding': {'$exists': True}})
        without_embedding = collection.count_documents({
            'embedding': {'$exists': False},
            'chunked': {'$exists': False}
        })
        chunked = collection.count_documents({'chunked': True})

        print(f"\n[현황]")
        print(f"  전체 문서: {total_docs}개")
        print(f"  embedding 있음: {with_embedding}개")
        print(f"  embedding 없음 (청크 대기): {without_embedding}개")
        print(f"  청킹된 원본: {chunked}개")


def main():
    parser = argparse.ArgumentParser(description="대용량 문서 청킹")
    parser.add_argument("--test", action="store_true", help="테스트 모드 (dry-run)")
    args = parser.parse_args()

    process_large_documents(dry_run=args.test)


if __name__ == "__main__":
    main()
