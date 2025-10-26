"""
토큰 사용량 및 비용 추적 테스트 스크립트

ChatbotStream의 stream_chat() 메서드를 호출하여
토큰 계산 및 비용 추적이 올바르게 작동하는지 검증합니다.
"""

import asyncio
import json
from app.ai.chatbot.stream import ChatbotStream
from app.ai.chatbot.config import model


async def test_token_tracking():
    """토큰 추적 기능 통합 테스트"""
    
    # ChatbotStream 인스턴스 생성
    system_role = "당신은 제주대학교 규정 안내 챗봇입니다."
    instruction = "제주대학교 규정에 대한 질문에 답변하고, 필요시 웹검색이나 학식 정보를 제공합니다."
    
    chatbot = ChatbotStream(
        model=model.advanced,
        system_role=system_role,
        instruction=instruction
    )
    
    print("=" * 80)
    print("토큰 사용량 및 비용 추적 테스트")
    print("=" * 80)
    
    # 테스트 케이스 1: 간단한 질문 (RAG 없음, 함수 없음)
    print("\n[테스트 1] 간단한 질문")
    print("-" * 80)
    test_message_1 = "안녕하세요. 오늘 날씨가 어때요?"
    
    print(f"사용자: {test_message_1}")
    print("\n챗봇 응답:")
    
    response_text_1 = ""
    metadata_1 = None
    
    async for line in chatbot.stream_chat(test_message_1, language="KOR"):
        try:
            event = json.loads(line)
            
            if event["type"] == "delta":
                print(event["content"], end="", flush=True)
                response_text_1 += event["content"]
            
            elif event["type"] == "metadata":
                metadata_1 = event["data"]
            
            elif event["type"] == "done":
                print("\n")
                break
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
    
    # 메타데이터 출력
    if metadata_1:
        print("\n[메타데이터]")
        print(f"  RAG 사용: {metadata_1.get('rag') is not None}")
        print(f"  함수 호출 수: {metadata_1.get('functions_count', 0)}")
        print(f"  웹검색 상태: {metadata_1.get('web_search_status', 'N/A')}")
        
        token_usage = metadata_1.get("token_usage")
        if token_usage:
            print("\n[토큰 사용량]")
            print(f"  입력 토큰: {token_usage['input_tokens']:,}")
            print(f"  출력 토큰: {token_usage['output_tokens']:,}")
            print(f"  함수 토큰: {token_usage['function_tokens']:,}")
            print(f"  RAG 토큰: {token_usage['rag_tokens']:,}")
            print(f"  총 토큰: {token_usage['total_tokens']:,}")
            
            print("\n[비용 (USD)]")
            print(f"  입력 비용: ${token_usage['input_cost_usd']:.6f}")
            print(f"  출력 비용: ${token_usage['output_cost_usd']:.6f}")
            print(f"  총 비용: ${token_usage['total_cost_usd']:.6f}")
            print(f"  모델: {token_usage['model']}")
    
    # 테스트 케이스 2: 규정 질문 (RAG 포함)
    print("\n" + "=" * 80)
    print("[테스트 2] 규정 질문 (RAG 검색 포함)")
    print("-" * 80)
    test_message_2 = "교원 임용 자격 요건이 어떻게 되나요?"
    
    print(f"사용자: {test_message_2}")
    print("\n챗봇 응답:")
    
    response_text_2 = ""
    metadata_2 = None
    
    async for line in chatbot.stream_chat(test_message_2, language="KOR"):
        try:
            event = json.loads(line)
            
            if event["type"] == "delta":
                print(event["content"], end="", flush=True)
                response_text_2 += event["content"]
            
            elif event["type"] == "metadata":
                metadata_2 = event["data"]
            
            elif event["type"] == "done":
                print("\n")
                break
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
    
    # 메타데이터 출력
    if metadata_2:
        print("\n[메타데이터]")
        
        rag = metadata_2.get("rag")
        if rag:
            print(f"  규정 여부: {rag['is_regulation']}")
            print(f"  판단 이유: {rag['gate_reason']}")
            print(f"  컨텍스트 소스: {rag['context_source']}")
            print(f"  검색 히트: {rag['hits_count']}개")
            print(f"  문서 수: {rag['document_count']}개")
        
        print(f"  함수 호출 수: {metadata_2.get('functions_count', 0)}")
        print(f"  웹검색 상태: {metadata_2.get('web_search_status', 'N/A')}")
        
        token_usage = metadata_2.get("token_usage")
        if token_usage:
            print("\n[토큰 사용량]")
            print(f"  입력 토큰: {token_usage['input_tokens']:,}")
            print(f"  출력 토큰: {token_usage['output_tokens']:,}")
            print(f"  함수 토큰: {token_usage['function_tokens']:,}")
            print(f"  RAG 토큰: {token_usage['rag_tokens']:,} ⭐")
            print(f"  총 토큰: {token_usage['total_tokens']:,}")
            
            print("\n[비용 (USD)]")
            print(f"  입력 비용: ${token_usage['input_cost_usd']:.6f}")
            print(f"  출력 비용: ${token_usage['output_cost_usd']:.6f}")
            print(f"  총 비용: ${token_usage['total_cost_usd']:.6f}")
            print(f"  모델: {token_usage['model']}")
    
    # 테스트 케이스 3: 함수 호출 (학식 정보)
    print("\n" + "=" * 80)
    print("[테스트 3] 함수 호출 (학식 정보)")
    print("-" * 80)
    test_message_3 = "오늘 학식 메뉴가 뭐야?"
    
    print(f"사용자: {test_message_3}")
    print("\n챗봇 응답:")
    
    response_text_3 = ""
    metadata_3 = None
    
    async for line in chatbot.stream_chat(test_message_3, language="KOR"):
        try:
            event = json.loads(line)
            
            if event["type"] == "delta":
                print(event["content"], end="", flush=True)
                response_text_3 += event["content"]
            
            elif event["type"] == "metadata":
                metadata_3 = event["data"]
            
            elif event["type"] == "done":
                print("\n")
                break
                
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
    
    # 메타데이터 출력
    if metadata_3:
        print("\n[메타데이터]")
        print(f"  RAG 사용: {metadata_3.get('rag') is not None}")
        
        functions = metadata_3.get("functions", [])
        print(f"  함수 호출 수: {len(functions)}")
        for func in functions:
            print(f"    - {func['name']} (fallback: {func['is_fallback']})")
        
        print(f"  웹검색 상태: {metadata_3.get('web_search_status', 'N/A')}")
        
        token_usage = metadata_3.get("token_usage")
        if token_usage:
            print("\n[토큰 사용량]")
            print(f"  입력 토큰: {token_usage['input_tokens']:,}")
            print(f"  출력 토큰: {token_usage['output_tokens']:,}")
            print(f"  함수 토큰: {token_usage['function_tokens']:,} ⭐")
            print(f"  RAG 토큰: {token_usage['rag_tokens']:,}")
            print(f"  총 토큰: {token_usage['total_tokens']:,}")
            
            print("\n[비용 (USD)]")
            print(f"  입력 비용: ${token_usage['input_cost_usd']:.6f}")
            print(f"  출력 비용: ${token_usage['output_cost_usd']:.6f}")
            print(f"  총 비용: ${token_usage['total_cost_usd']:.6f}")
            print(f"  모델: {token_usage['model']}")
    
    print("\n" + "=" * 80)
    print("테스트 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_token_tracking())
