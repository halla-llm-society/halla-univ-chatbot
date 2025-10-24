"""gpt-4.1-nano 모델의 strict JSON schema 지원 테스트"""
import os
from pathlib import Path
from dotenv import load_dotenv

# apikey.env 로드
load_dotenv(Path(__file__).parent / "apikey.env")

from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 테스트 질문
question = "졸업조건알려줘"

# 프롬프트
system_prompt = """당신은 학사 규정 질문 판정 에이전트입니다.
사용자 질문이 학교 규정(졸업, 학점, 휴학, 복학 등)과 관련되었는지 판단하세요.
반드시 JSON 형식으로 응답하세요: {"is_regulation": true/false, "reason": "판단 이유"}"""

prompt = [
    {"role": "system", "content": system_prompt},
    {"role": "user", "content": question},
]

schema = {
    "type": "object",
    "properties": {
        "is_regulation": {"type": "boolean"},
        "reason": {"type": "string"},
    },
    "required": ["is_regulation", "reason"],
    "additionalProperties": False,
}

print("=" * 80)
print("🧪 gpt-4.1-nano 모델의 strict JSON schema 지원 테스트")
print("=" * 80)
print(f"\n📝 테스트 질문: {question}")

# 테스트 1: strict=True (기본값)
print("\n" + "=" * 80)
print("테스트 1: strict=True (엄격한 스키마 강제)")
print("=" * 80)
try:
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "rag_gate_schema",
                "schema": schema,
                "strict": True  # 엄격한 스키마 강제
            }
        },
        temperature=1.0,
    )
    
    output = response.output_text.strip()
    print(f"\n✅ 응답 성공:")
    print(f"  출력: {output}")
    
    # JSON 파싱 테스트
    import json
    parsed = json.loads(output)
    print(f"\n✅ JSON 파싱 성공:")
    print(f"  is_regulation: {parsed.get('is_regulation')}")
    print(f"  reason: {parsed.get('reason')}")
    
except Exception as e:
    print(f"\n❌ 실패: {e}")
    print(f"  에러 타입: {type(e).__name__}")

# 테스트 2: strict=False
print("\n" + "=" * 80)
print("테스트 2: strict=False (유연한 스키마)")
print("=" * 80)
try:
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        text={
            "format": {
                "type": "json_schema",
                "name": "rag_gate_schema",
                "schema": schema,
                "strict": False  # 유연한 스키마
            }
        },
        temperature=1.0,
    )
    
    output = response.output_text.strip()
    print(f"\n✅ 응답 성공:")
    print(f"  출력: {output}")
    
    # JSON 파싱 테스트
    import json
    parsed = json.loads(output)
    print(f"\n✅ JSON 파싱 성공:")
    print(f"  is_regulation: {parsed.get('is_regulation')}")
    print(f"  reason: {parsed.get('reason')}")
    
except Exception as e:
    print(f"\n❌ 실패: {e}")
    print(f"  에러 타입: {type(e).__name__}")

# 테스트 3: 일반 텍스트 모드 (비교용)
print("\n" + "=" * 80)
print("테스트 3: 일반 텍스트 모드 (비교용)")
print("=" * 80)
try:
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        text={"format": {"type": "text"}},
        temperature=1.0,
    )
    
    output = response.output_text.strip()
    print(f"\n✅ 응답 성공:")
    print(f"  출력: {output[:200]}...")
    
except Exception as e:
    print(f"\n❌ 실패: {e}")

print("\n" + "=" * 80)
print("테스트 완료")
print("=" * 80)


