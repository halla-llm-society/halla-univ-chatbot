"""함수 선택 추론 메타데이터 단위 테스트

FunctionCallMetadata의 reasoning 필드 테스트
"""

from app.ai.chatbot.metadata import FunctionCallMetadata, ToolReasoningMetadata


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
    print("모든 테스트 통과! 🎉")
    print("=" * 80)


if __name__ == "__main__":
    test_function_call_metadata_with_reasoning()
