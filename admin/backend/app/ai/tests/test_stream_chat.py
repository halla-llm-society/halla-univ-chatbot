import requests
import json
from app.ai.llm import get_llm_manager

# 언어 선택 매핑
language_map = {
    "1": ("KOR", "한국어"),
    "2": ("ENG", "영어"),
    "3": ("VI", "베트남어"),
    "4": ("JPN", "일본어"),
    "5": ("CHN", "중국어"),
}

def select_language():
    print("언어를 선택하세요:")
    for k, v in language_map.items():
        print(f"{k}. {v[1]}")
    while True:
        choice = input("번호 입력: ").strip()
        if choice in language_map:
            return language_map[choice][0]
        print("잘못된 입력입니다. 다시 선택하세요.")


def select_preset():
    """프리셋 선택 메뉴"""
    try:
        llm_manager = get_llm_manager()
        presets = llm_manager.preset_manager.list_presets()
        current_preset = llm_manager.get_active_preset()
        
        print("\n" + "=" * 80)
        print("📊 프리셋 선택")
        print("=" * 80)
        print(f"현재 프리셋: {current_preset}\n")
        
        for idx, preset in enumerate(presets, 1):
            marker = "✅" if preset["name"] == current_preset else "  "
            print(f"{marker} {idx}. {preset['name']}")
            print(f"     설명: {preset['description']}")
            print()
        
        while True:
            choice = input("프리셋 번호 입력 (취소: 0): ").strip()
            if choice == "0":
                return None
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(presets):
                    selected = presets[idx]["name"]
                    if llm_manager.switch_preset(selected):
                        print(f"\n✅ 프리셋이 '{selected}'로 변경되었습니다!")
                        return selected
                    else:
                        print(f"\n❌ 프리셋 변경 실패")
                        return None
                else:
                    print("잘못된 번호입니다. 다시 입력하세요.")
            except ValueError:
                print("숫자를 입력하세요.")
    
    except Exception as e:
        print(f"❌ 프리셋 선택 오류: {e}")
        return None

def main():
    # FastAPI 라우터는 prefix="/api"로 등록되어 있으며, 현재 서버 엔드포인트는 /api/chat 입니다.
    url = "http://127.0.0.1:8000/api/chat"
    language = select_language()
    print(f"선택된 언어: {language}")
    
    # 테스트 안내 메시지 출력
    print("\n" + "=" * 80)
    print("📋 메타데이터 테스트 가이드")
    print("=" * 80)
    print("\n각 질문 유형에 따라 다른 메타데이터가 출력됩니다:\n")
    
    print("1️⃣  RAG 메타데이터 (RagMetadata)")
    print("   질문 예시: '휴학 신청 방법 알려줘', '규정 3-1-1 보여줘'")
    print("   출력 내용: gate_reason, hits_count, document_count, condensed_context")
    print("   💡 '/rag' 명령어로 검색된 원문 확인 가능\n")
    
    print("2️⃣  함수 호출 메타데이터 (FunctionCallMetadata)")
    print("   질문 예시:")
    print("     - 학식: '오늘 점심 메뉴 뭐야?', '내일 저녁 메뉴는?'")
    print("     - 웹검색: '최근 AI 뉴스 알려줘', '날씨 어때?'")
    print("   출력 내용: name, arguments, reasoning (함수 선택 이유), is_fallback\n")
    
    print("3️⃣  도구 선택 추론 (ToolReasoningMetadata)")
    print("   함수 호출 시 LLM이 '왜 이 함수를 선택했는지' 설명")
    print("   출력 내용: reasoning, selected_tools\n")
    
    print("4️⃣  토큰 사용량 메타데이터 (TokenUsageMetadata)")
    print("   모든 질문에 출력됨")
    print("   출력 내용: total_tokens, total_cost_usd, role_breakdown (역할별 분석)\n")
    
    print("5️⃣  웹 검색 상태")
    print("   웹 검색 함수 호출 시 상태 표시 (ok / empty-or-error / not-run)\n")
    
    print("6️⃣  일반 대화 (메타데이터 최소)")
    print("   질문 예시: '안녕?', '고마워'")
    print("   출력 내용: 토큰 사용량만 출력 (함수/RAG 없음)")
    
    print("\n" + "=" * 80)
    print("💡 명령어:")
    print("  - exit: 종료")
    print("  - /lang: 언어 변경")
    print("  - /preset: 프리셋 변경 (balanced, budget, premium 등)")
    print("  - /rag: 마지막 RAG 검색 원문 보기")
    print("=" * 80 + "\n")
    
    # 마지막 RAG 메타데이터 저장
    last_rag_metadata = None

    while True:
        # RAG 원문 안내 표시
        prompt = "\n질문 입력 (종료: exit, 언어변경: /lang, 프리셋: /preset"
        if last_rag_metadata:
            prompt += ", RAG 원문: /rag"
        prompt += "): "
        
        msg = input(prompt).strip()
        
        if msg.lower() == "exit":
            print("테스트 종료.")
            break
        if msg.lower() in ["/lang", "/언어"]:
            language = select_language()
            print(f"언어가 변경되었습니다: {language}")
            continue
        
        # 프리셋 변경 명령어
        if msg.lower() in ["/preset", "/프리셋"]:
            select_preset()
            continue
        
        # RAG 원문 보기 명령어
        if msg.lower() == "/rag":
            if not last_rag_metadata:
                print("⚠️ 아직 RAG 검색 결과가 없습니다. 먼저 질문을 입력하세요.")
                continue
            
            print("\n" + "=" * 80)
            print("📄 RAG 검색 원문 (마지막 질문)")
            print("=" * 80)
            print(f"규정 여부: {'예' if last_rag_metadata.get('is_regulation', False) else '아니오'}")
            print(f"검색 소스: {last_rag_metadata.get('context_source', 'N/A')}")
            print(f"검색 문서 수: {last_rag_metadata.get('hits_count', 0)}개")
            print(f"MongoDB 문서: {last_rag_metadata.get('document_count', 0)}개")
            print(f"프리뷰 문서: {last_rag_metadata.get('preview_count', 0)}개")
            
            # 출처 문서 정보 표시
            source_docs = last_rag_metadata.get("source_documents", [])
            if source_docs:
                # 유효한 문서만 필터링 (모든 필드가 비어있지 않은 문서)
                valid_docs = [
                    doc for doc in source_docs 
                    if doc.get("title") or doc.get("law_article_id") or doc.get("source_file")
                ]
                
                if valid_docs:
                    print("\n--- 📚 검색된 문서 출처 정보 ---")
                    for idx, doc in enumerate(valid_docs, 1):
                        print(f"\n[문서 {idx}]")
                        if doc.get("title"):
                            print(f"  제목: {doc['title']}")
                        if doc.get("law_article_id"):
                            print(f"  조항 ID: {doc['law_article_id']}")
                        if doc.get("source_file"):
                            print(f"  원본 파일: {doc['source_file']}")
                else:
                    print("\n⚠️ 출처 문서 메타데이터가 비어있습니다.")
            else:
                print("\n⚠️ 출처 문서 정보가 없습니다.")
            
            # 요약된 컨텍스트 우선 표시 (LLM이 <반영> 태그로 가공한 버전)
            if last_rag_metadata.get("condensed_context"):
                print("\n--- 📝 요약된 원문 (<반영> 태그 포함) ---")
                print(last_rag_metadata["condensed_context"])
            elif last_rag_metadata.get("raw_context"):
                print("\n--- 📄 원본 RAG 컨텍스트 (MongoDB) ---")
                print(last_rag_metadata["raw_context"])
            else:
                print("\n⚠️ 컨텍스트 정보가 없습니다.")
            
            print("=" * 80)
            continue

        payload = {"message": msg, "language": language}
        try:
            with requests.post(url, json=payload, stream=True) as resp:
                print("\n응답:")
                print("-" * 60)
                
                # JSON Lines 형식 파싱
                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line)
                        msg_type = data.get("type")
                        
                        if msg_type == "delta":
                            # 텍스트 델타 출력 (줄바꿈 없이)
                            print(data.get("content", ""), end="", flush=True)
                        
                        elif msg_type == "metadata":
                            # 메타데이터 출력 (줄바꿈 후)
                            print("\n\n" + "=" * 80)
                            print("📊 메타데이터 파싱 디버그")
                            print("=" * 80)
                            metadata = data.get("data", {})
                            
                            # 1. RAG 메타데이터
                            if "rag" in metadata and metadata["rag"]:
                                rag = metadata["rag"]
                                last_rag_metadata = rag  # RAG 메타데이터 저장
                                print("\n[1] 🔍 RAG 메타데이터 (RagMetadata.to_dict())")
                                print(f"  ✅ is_regulation: {rag.get('is_regulation', False)}")
                                print(f"  ✅ gate_reason: {rag.get('gate_reason', 'N/A')}")
                                print(f"  ✅ context_source: {rag.get('context_source', 'N/A')}")
                                print(f"  ✅ hits_count: {rag.get('hits_count', 0)}")
                                print(f"  ✅ document_count: {rag.get('document_count', 0)}")
                                print(f"  ✅ preview_count: {rag.get('preview_count', 0)}")
                                if rag.get("has_condensed_context"):
                                    print(f"  ✅ condensed_context: {rag.get('condensed_context_length', 0)}자")
                                if rag.get("source_documents"):
                                    print(f"  ✅ source_documents: {len(rag['source_documents'])}개")
                                print(f"  💡 '/rag' 입력 시 원문 확인 가능")
                            else:
                                # RAG 검색이 없었다면 초기화
                                last_rag_metadata = None
                                print("\n[1] 🔍 RAG 메타데이터: None (규정 질문 아님)")
                            
                            # 2. 함수 호출 메타데이터
                            if "functions" in metadata and metadata["functions"]:
                                funcs = metadata["functions"]
                                print(f"\n[2] ⚙️  함수 호출 메타데이터 (FunctionCallMetadata.to_dict())")
                                print(f"  ✅ functions_count: {len(funcs)}")
                                for idx, func in enumerate(funcs, 1):
                                    print(f"\n  [함수 {idx}]")
                                    print(f"    ✅ name: {func.get('name', 'Unknown')}")
                                    print(f"    ✅ arguments: {func.get('arguments', {})}")
                                    print(f"    ✅ output_length: {func.get('output_length', 0)}자")
                                    print(f"    ✅ call_id: {func.get('call_id', 'N/A')}")
                                    print(f"    ✅ is_fallback: {func.get('is_fallback', False)}")
                                    if func.get('reasoning'):
                                        print(f"    ✅ reasoning: {func['reasoning']}")
                                    else:
                                        print(f"    ⚠️  reasoning: None")
                            else:
                                print(f"\n[2] ⚙️  함수 호출 메타데이터: 없음")
                            
                            # 3. 도구 선택 추론 메타데이터
                            if "tool_reasoning" in metadata and metadata["tool_reasoning"]:
                                tool_reasoning = metadata["tool_reasoning"]
                                print(f"\n[3] 🧠 도구 선택 추론 (ToolReasoningMetadata.to_dict())")
                                print(f"  ✅ reasoning: {tool_reasoning.get('reasoning', 'N/A')}")
                                print(f"  ✅ selected_tools: {tool_reasoning.get('selected_tools', [])}")
                            else:
                                print(f"\n[3] 🧠 도구 선택 추론: None (함수 호출 없음)")
                            
                            # 4. 토큰 사용량 메타데이터
                            if "token_usage" in metadata and metadata["token_usage"]:
                                tokens = metadata["token_usage"]
                                print(f"\n[4] 💰 토큰 사용량 메타데이터 (TokenUsageMetadata.to_dict())")
                                print(f"  ✅ input_tokens: {tokens.get('input_tokens', 0):,}")
                                print(f"  ✅ output_tokens: {tokens.get('output_tokens', 0):,}")
                                print(f"  ✅ function_tokens: {tokens.get('function_tokens', 0):,}")
                                print(f"  ✅ rag_tokens: {tokens.get('rag_tokens', 0):,}")
                                print(f"  ✅ total_tokens: {tokens.get('total_tokens', 0):,}")
                                print(f"  ✅ input_cost_usd: ${tokens.get('input_cost_usd', 0):.6f}")
                                print(f"  ✅ output_cost_usd: ${tokens.get('output_cost_usd', 0):.6f}")
                                print(f"  ✅ total_cost_usd: ${tokens.get('total_cost_usd', 0):.6f}")
                                print(f"  ✅ model: {tokens.get('model', 'N/A')}")
                                
                                # 프리셋 정보 출력 (중요!)
                                if tokens.get('preset'):
                                    print(f"  ✅ preset: {tokens['preset']} (현재 활성 프리셋)")
                                else:
                                    print(f"  ⚠️  preset: None")
                                
                                # 역할별 토큰 분석
                                if tokens.get('role_breakdown'):
                                    print(f"\n  📊 역할별 토큰 분석:")
                                    for role, counts in tokens['role_breakdown'].items():
                                        total = counts.get('input', 0) + counts.get('output', 0)
                                        print(f"    - {role}: {total:,} (입력: {counts.get('input', 0):,}, 출력: {counts.get('output', 0):,})")
                            else:
                                print(f"\n[4] 💰 토큰 사용량 메타데이터: None")
                            
                            # 5. 웹 검색 상태
                            if "web_search_status" in metadata:
                                status = metadata["web_search_status"]
                                print(f"\n[5] 🌐 웹 검색 상태: {status}")
                            else:
                                print(f"\n[5] 🌐 웹 검색 상태: None")
                            
                            print("\n" + "=" * 80)
                            print("✅ 모든 메타데이터 파싱 완료 (to_dict() 자동 변환)")
                            print("=" * 80)
                        
                        elif msg_type == "done":
                            # 완료 신호
                            print("\n\n✅ 응답 완료")
                    
                    except json.JSONDecodeError as e:
                        print(f"\n⚠️ JSON 파싱 오류: {e}")
                        print(f"   원본: {line[:100]}...")
                
                print("-" * 60)
        except Exception as e:
            print(f"❌ 요청 실패: {e}")

if __name__ == "__main__":
    main()