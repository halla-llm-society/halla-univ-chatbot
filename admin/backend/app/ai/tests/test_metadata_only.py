"""함수 선택 추론 메타데이터 직접 테스트

임포트 체인 문제를 피하기 위해 메타데이터 클래스만 직접 테스트
"""

import sys
from pathlib import Path

# 직접 경로 추가
sys.path.insert(0, str(Path(__file__).parent))

# metadata.py만 직접 실행
import importlib.util
spec = importlib.util.spec_from_file_location(
    "metadata", 
    Path(__file__).parent / "ai" / "chatbot" / "metadata.py"
)
metadata_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(metadata_module)

FunctionCallMetadata = metadata_module.FunctionCallMetadata
ToolReasoningMetadata = metadata_module.ToolReasoningMetadata


def test_function_call_metadata_with_reasoning():
    """FunctionCallMetadata에 reasoning 필드 추가 테스트"""
    
    print("=" * 80)
    print("테스트 1: FunctionCallMetadata - reasoning 포함")
    print("=" * 80)
    
    metadata = FunctionCallMetadata(
        name="search_internet",
        arguments={"user_input": "최근 AI 뉴스"},
        output="검색 결과...",
        call_id="call_123",
        is_fallback=False,
        reasoning="사용자가 최신 AI 뉴스를 요청했으므로 search_internet 함수가 필요합니다."
    )
    
    result = metadata.to_dict()
    
    print(f"✅ 함수 이름: {result['name']}")
    print(f"✅ Fallback: {result['is_fallback']}")
    print(f"✅ 추론: {result.get('reasoning', '(없음)')}")
    
    assert "reasoning" in result, "reasoning 필드가 누락됨"
    assert result["reasoning"] == "사용자가 최신 AI 뉴스를 요청했으므로 search_internet 함수가 필요합니다."
    
    print("\n✅ 테스트 1 통과: reasoning 필드가 정상적으로 포함됨")
    
    print("\n" + "=" * 80)
    print("테스트 2: FunctionCallMetadata - reasoning 없음 (Fallback)")
    print("=" * 80)
    
    metadata2 = FunctionCallMetadata(
        name="get_halla_cafeteria_menu",
        arguments={"date": "오늘"},
        output="메뉴...",
        call_id="call_auto",
        is_fallback=True,
        reasoning=None
    )
    
    result2 = metadata2.to_dict()
    
    print(f"✅ 함수 이름: {result2['name']}")
    print(f"✅ Fallback: {result2['is_fallback']}")
    print(f"✅ 추론: {result2.get('reasoning', '(없음)')}")
    
    # reasoning이 None이면 to_dict()에 포함되지 않음
    assert "reasoning" not in result2, "reasoning이 None인데 포함됨"
    
    print("\n✅ 테스트 2 통과: reasoning이 None이면 to_dict()에 포함되지 않음")
    
    print("\n" + "=" * 80)
    print("테스트 3: ToolReasoningMetadata")
    print("=" * 80)
    
    tool_reasoning = ToolReasoningMetadata(
        reasoning="사용자가 학식 메뉴를 요청했으므로 get_halla_cafeteria_menu 함수를 선택합니다.",
        selected_tools=["get_halla_cafeteria_menu"]
    )
    
    result3 = tool_reasoning.to_dict()
    
    print(f"✅ 추론: {result3['reasoning']}")
    print(f"✅ 선택된 도구: {result3['selected_tools']}")
    
    assert "reasoning" in result3
    assert "selected_tools" in result3
    assert len(result3["selected_tools"]) == 1
    
    print("\n✅ 테스트 3 통과: ToolReasoningMetadata 정상 작동")
    
    print("\n" + "=" * 80)
    print("테스트 4: FunctionCallMetadata JSON 직렬화")
    print("=" * 80)
    
    import json
    
    metadata3 = FunctionCallMetadata(
        name="get_halla_cafeteria_menu",
        arguments={"date": "오늘", "meal": "중식"},
        output="오늘 중식 메뉴: 김치찌개, 된장찌개...",
        call_id="call_456",
        is_fallback=False,
        reasoning="사용자가 학식 메뉴를 요청했으므로 get_halla_cafeteria_menu 함수를 선택합니다."
    )
    
    json_str = json.dumps(metadata3.to_dict(), ensure_ascii=False, indent=2)
    print(json_str)
    
    parsed = json.loads(json_str)
    assert parsed["reasoning"] == "사용자가 학식 메뉴를 요청했으므로 get_halla_cafeteria_menu 함수를 선택합니다."
    
    print("\n✅ 테스트 4 통과: JSON 직렬화/역직렬화 정상 작동")
    
    print("\n" + "=" * 80)
    print("모든 테스트 통과! 🎉")
    print("=" * 80)
    print("\n📋 요약:")
    print("  1. FunctionCallMetadata에 reasoning 필드 추가 완료")
    print("  2. reasoning이 있으면 to_dict()에 포함")
    print("  3. reasoning이 None이면 to_dict()에서 제외")
    print("  4. ToolReasoningMetadata 정상 작동")
    print("  5. JSON 직렬화/역직렬화 정상")


if __name__ == "__main__":
    test_function_call_metadata_with_reasoning()
