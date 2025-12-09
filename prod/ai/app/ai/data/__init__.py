"""
데이터 처리 모듈

문서 로딩, MongoDB 연결, 벡터 DB 업로드 등을 담당합니다.
"""

from .mongodb_client import collection, MONGO_AVAILABLE

__all__ = ["collection", "MONGO_AVAILABLE"]
