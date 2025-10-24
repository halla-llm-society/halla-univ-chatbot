"""함수 선택 추론(reasoning) 기능 테스트

RAG의 gate_reason과 동일한 패턴으로 함수 호출 시 추론 생성 확인
"""

import asyncio
from app.ai.chatbot.stream import ChatbotStream
from app.ai.chatbot import character


async def test_function_reasoning():
    """함수 선택 추론 생성 테스트"""
    
    print("=" * 80)
    print("테스트: 함수 선택 추론 생성")
    print("=" * 80)
    
    # ChatbotStream 초기화
    chatbot = ChatbotStream(
        model="gpt-4.1",
        system_role=character.system_role,
        instruction=character.instruction,
        debug=True
    )
    
    # 테스트 케이스 1: 학식 메뉴 조회
    print("\n[테스트 1] 학식 메뉴 조회")
    print("-" * 80)
    message1 = "오늘 점심 메뉴 뭐야?"
    
    async for event_json in chatbot.stream_chat(message1):
        import json
        try:
            event = json.loads(event_json)
            
            # 메타데이터만 출력 (tool_reasoning 확인)
            if event.get("type") == "metadata":
                metadata = event.get("data", {})
                
                # tool_reasoning 확인
                tool_reasoning = metadata.get("tool_reasoning")
                if tool_reasoning:
                    print("\n✅ 함수 선택 추론 생성됨:")
                    print(f"  - 추론: {tool_reasoning.get('reasoning')}")
                    print(f"  - 선택된 도구: {tool_reasoning.get('selected_tools')}")
                else:
                    print("\n❌ tool_reasoning이 None입니다.")
                
                # 함수 호출 메타데이터 확인
                functions = metadata.get("functions", [])
                print(f"\n📊 함수 호출 개수: {len(functions)}")
                for func in functions:
                    print(f"  - 함수: {func.get('name')}")
                    print(f"    인자: {func.get('arguments')}")
                    print(f"    Fallback: {func.get('is_fallback')}")
                    print(f"    추론: {func.get('reasoning', '(없음)')}")
                
        except json.JSONDecodeError:
            pass
    
    # 테스트 케이스 2: 웹 검색
    print("\n" + "=" * 80)
    print("[테스트 2] 웹 검색")
    print("-" * 80)
    message2 = "최근 AI 뉴스 알려줘"
    
    async for event_json in chatbot.stream_chat(message2):
        import json
        try:
            event = json.loads(event_json)
            
            if event.get("type") == "metadata":
                metadata = event.get("data", {})
                
                tool_reasoning = metadata.get("tool_reasoning")
                if tool_reasoning:
                    print("\n✅ 함수 선택 추론 생성됨:")
                    print(f"  - 추론: {tool_reasoning.get('reasoning')}")
                    print(f"  - 선택된 도구: {tool_reasoning.get('selected_tools')}")
                else:
                    print("\n❌ tool_reasoning이 None입니다.")
                
                functions = metadata.get("functions", [])
                print(f"\n📊 함수 호출 개수: {len(functions)}")
                for func in functions:
                    print(f"  - 함수: {func.get('name')}")
                    print(f"    추론: {func.get('reasoning', '(없음)')}")
        except json.JSONDecodeError:
            pass
    
    # 테스트 케이스 3: 함수 불필요한 일반 대화
    print("\n" + "=" * 80)
    print("[테스트 3] 일반 대화 (함수 불필요)")
    print("-" * 80)
    message3 = "안녕?"
    
    async for event_json in chatbot.stream_chat(message3):
        import json
        try:
            event = json.loads(event_json)
            
            if event.get("type") == "metadata":
                metadata = event.get("data", {})
                
                tool_reasoning = metadata.get("tool_reasoning")
                if tool_reasoning:
                    print("\n⚠️  tool_reasoning이 있습니다:")
                    print(f"  - 추론: {tool_reasoning.get('reasoning')}")
                    print(f"  - 선택된 도구: {tool_reasoning.get('selected_tools')}")
                else:
                    print("\n✅ tool_reasoning이 None입니다 (함수 호출 없음)")
                
                functions = metadata.get("functions", [])
                print(f"\n📊 함수 호출 개수: {len(functions)}")
        except json.JSONDecodeError:
            pass
    
    print("\n" + "=" * 80)
    print("테스트 완료")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_function_reasoning())
