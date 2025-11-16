"""RAG 전체 흐름 테스트 (Gate → Retriever → MongoDB)"""
import os
import sys

# 환경 설정
sys.path.insert(0, "/Users/kimdaegi/Desktop/backend")
os.chdir("/Users/kimdaegi/Desktop/backend/app")
os.environ["RAG_DEBUG"] = "1"

from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "apikey.env")

def debug_print(msg):
    print(f"[DEBUG] {msg}")

# LLM 프리셋 전환
from app.ai.llm import get_llm_manager
manager = get_llm_manager()
manager.preset_manager.switch_preset("gpt4_nano_only")
print(f"✅ 현재 프리셋: {manager.preset_manager.get_active_preset()}")
gate_info = manager.get_provider("gate")
print(f"✅ Gate 모델: {gate_info.model_name}\n")

# RAG Service 생성
from app.ai.rag.service import RagService
rag_service = RagService(debug_fn=debug_print)

# 테스트 질문
question = "졸업조건알려줘"

print("=" * 80)
print(f"📝 테스트 질문: {question}")
print("=" * 80)

# RAG 검색 실행
print("\n🔍 RAG 검색 시작...\n")
result = rag_service.retrieve_context(question)

# 결과 출력
print("\n" + "=" * 80)
print("📊 RAG 검색 결과:")
print("=" * 80)
print(f"  is_regulation: {result.is_regulation}")
print(f"  gate_reason: {result.gate_reason}")
print(f"  context_source: {result.context_source}")
print(f"  document_count: {result.document_count}")
print(f"  preview_count: {result.preview_count}")
print(f"  hits 수: {len(result.hits)}")
print(f"  chunk_ids 수: {len(result.chunk_ids)}")
print(f"  merged_documents_text: {result.merged_documents_text is not None}")

if result.merged_documents_text:
    print(f"\n✅ RAG 활성화 가능 - 문서 길이: {len(result.merged_documents_text)}자")
    print(f"\n📄 문서 샘플 (처음 500자):")
    print(result.merged_documents_text[:500] + "...")
else:
    print(f"\n❌ RAG 비활성화 - merged_documents_text가 None")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)

