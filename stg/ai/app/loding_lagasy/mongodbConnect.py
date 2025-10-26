from pymongo import MongoClient
from typing import List, Dict
import os
from dotenv import load_dotenv
import certifi

# .env에서 MONGODB_URI 불러오기
load_dotenv('apikey.env')
MONGODB_URI = os.getenv("MONGODB_URI")
if not MONGODB_URI:
    raise ValueError("MONGODB_URI 환경 변수가 설정되지 않았습니다.")
COLLECTION_NAME = "regulation_chunks"
DB_NAME = "halla_academic_db"

# Mongo 연결
# 일부 환경에서 시스템 CA 경로가 누락될 수 있어 보조적으로 SSL_CERT_FILE을 지정
os.environ.setdefault("SSL_CERT_FILE", certifi.where())

client = MongoClient(
    MONGODB_URI,
    tls=True,                         # TLS 명시
    tlsCAFile=certifi.where(),        # 신뢰 CA 번들
    serverSelectionTimeoutMS=30000,
    connectTimeoutMS=20000,
    socketTimeoutMS=20000,
)

# 초기 연결 확인(실패 시 앱 크래시 방지하고 친절한 진단만 출력)
MONGO_AVAILABLE = True
try:
    client.admin.command("ping")
except Exception as e:
    MONGO_AVAILABLE = False
    print("[Mongo TLS] 핑 실패로 연결 점검이 필요합니다.")
    print(f" - 에러: {e}")
    print(f" - URI 스킴: {('mongodb+srv' if MONGODB_URI.startswith('mongodb+srv') else 'mongodb')} (SRV 권장)")
    print(f" - CA 경로(사용 중): {certifi.where()}")
    print(" - Atlas Network Access IP 허용, VPC/방화벽, 로컬 프록시/보안SW를 확인하세요.")

db = client[DB_NAME]
collection = db[COLLECTION_NAME]


def insert_chunks_to_mongo(chunks: List[Dict]):
    try:
        if not MONGO_AVAILABLE:
            print("[Mongo] 현재 연결이 불안정합니다(ping 실패). 저장 시도는 계속합니다.")
        cluster = client 

        db = cluster[DB_NAME]
        collection = db[COLLECTION_NAME]

        filenames = set(chunk['metadata']['source_file'] for chunk in chunks)
        for fname in filenames:
            delete_result = collection.delete_many({"metadata.source_file": fname})
            print(f" {fname} 삭제: {delete_result.deleted_count}개")

        result = collection.insert_many(chunks)
        print(f"저장 완료: {len(result.inserted_ids)}개")
    except Exception as e:
        print(f" Mongo 에러: {str(e)} URI/네트워크/TLS 설정을 확인하세요")