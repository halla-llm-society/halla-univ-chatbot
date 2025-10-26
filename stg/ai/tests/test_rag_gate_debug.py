"""RAG Gate 디버그 테스트"""
import os
import sys

# 프로젝트 경로 설정
sys.path.insert(0, "/Users/kimdaegi/Desktop/backend")
os.chdir("/Users/kimdaegi/Desktop/backend/app")

# 환경 변수 설정
os.environ["RAG_DEBUG"] = "1"

from app.ai.rag.gate import RegulationGate
from app.ai.llm import get_llm_manager

# LLM 프리셋 확인
manager = get_llm_manager()
print(f"✅ 현재 활성 프리셋: {manager.preset_manager.active_preset}")
print(f"✅ Gate 모델: {manager.preset_manager.get_role('gate')}")

# RAG Gate 인스턴스 생성
def debug_print(msg):
    print(f"[DEBUG] {msg}")

gate = RegulationGate(debug_fn=debug_print)

# 테스트 질문
test_question = "졸업조건알려줘"

print(f"\n📝 테스트 질문: {test_question}")
print("=" * 80)

try:
    decision = gate.decide(test_question)
    print(f"\n✅ RAG Gate 결과:")
    print(f"  - is_regulation: {decision.is_regulation}")
    print(f"  - reason: {decision.reason}")
except Exception as e:
    print(f"\n❌ RAG Gate 실패: {e}")
    import traceback
    traceback.print_exc()


