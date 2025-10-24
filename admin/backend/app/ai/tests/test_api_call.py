"""
실제 LLM API 호출 테스트

API 키가 설정되어 있어야 실행 가능합니다.
"""

import sys
from pathlib import Path

# app 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.llm import get_provider


def test_openai_api():
    """OpenAI API 호출 테스트"""
    print("\n[Test] OpenAI API 호출")
    print("=" * 60)
    
    try:
        # category 역할의 Provider (현재 설정: gemini-1.5-flash)
        provider = get_provider("category")
        print(f"Provider: {provider.get_provider_name()}")
        print(f"Model: {provider.get_model_name()}")
        
        # 간단한 테스트 메시지
        messages = [{
            "role": "user",
            "content": [{"type": "input_text", "text": "안녕하세요"}]
        }]
        
        print("\n요청: '안녕하세요'")
        print("API 호출 중...")
        
        result = provider.simple_completion(messages)
        print(f"✅ 응답: {result}")
        
        return True
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("\n가능한 원인:")
        print("1. API 키가 설정되지 않음 (apikey.env 파일 확인)")
        print("2. google-generativeai 패키지가 설치되지 않음")
        print("3. 네트워크 오류")
        return False


def main():
    print("\n" + "=" * 60)
    print("실제 LLM API 호출 테스트")
    print("=" * 60)
    print("\n⚠️  이 테스트는 실제 API를 호출하며 비용이 발생할 수 있습니다.")
    print("⚠️  API 키가 apikey.env에 설정되어 있어야 합니다.")
    print("\n")
    
    test_openai_api()


if __name__ == "__main__":
    main()

