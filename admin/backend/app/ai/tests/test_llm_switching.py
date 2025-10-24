"""
LLM API 교체 시스템 테스트 스크립트

프리셋 전환, Provider 선택, 비용 계산 등 핵심 기능을 테스트합니다.
"""

import sys
from pathlib import Path

# app 디렉토리를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.ai.llm import get_llm_manager, get_provider
from app.ai.utils.cost_calculator import CostCalculator


def test_preset_list():
    """프리셋 목록 조회 테스트"""
    print("\n[Test 1] 프리셋 목록 조회")
    print("=" * 60)
    
    llm_manager = get_llm_manager()
    presets = llm_manager.preset_manager.list_presets()
    
    print(f"총 {len(presets)}개의 프리셋:")
    for preset in presets:
        active_mark = "✓" if preset["is_active"] else " "
        print(f"  [{active_mark}] {preset['preset_name']}: {preset['name']}")
        print(f"      {preset['description']}")
    
    print(f"\n현재 활성 프리셋: {llm_manager.get_active_preset()}")


def test_preset_switch():
    """프리셋 전환 테스트"""
    print("\n[Test 2] 프리셋 전환")
    print("=" * 60)
    
    llm_manager = get_llm_manager()
    
    # balanced → budget 전환
    print("balanced → budget 전환 시도...")
    success = llm_manager.switch_preset("budget")
    print(f"전환 결과: {'성공' if success else '실패'}")
    print(f"현재 활성 프리셋: {llm_manager.get_active_preset()}")
    
    # budget → balanced 복원
    print("\nbudget → balanced 복원 시도...")
    success = llm_manager.switch_preset("balanced")
    print(f"전환 결과: {'성공' if success else '실패'}")
    print(f"현재 활성 프리셋: {llm_manager.get_active_preset()}")


def test_provider_selection():
    """Provider 선택 테스트"""
    print("\n[Test 3] Provider 선택")
    print("=" * 60)
    
    llm_manager = get_llm_manager()
    
    # 모든 역할에 대해 Provider 정보 출력
    roles_info = llm_manager.get_all_roles_info()
    
    print("역할별 LLM Provider:")
    for role, info in roles_info.items():
        fixed_mark = "🔒" if info.get("is_fixed") else "🔄"
        print(f"  {fixed_mark} {role:<20} → {info['provider']:<10} / {info['model']}")


def test_simple_completion():
    """단순 텍스트 생성 테스트 (OpenAI만)"""
    print("\n[Test 4] 단순 텍스트 생성 (category 역할)")
    print("=" * 60)
    
    try:
        provider = get_provider("category")
        print(f"사용 중인 Provider: {provider.get_provider_name()}")
        print(f"사용 중인 모델: {provider.get_model_name()}")
        
        # 간단한 테스트 메시지
        messages = [{
            "role": "user",
            "content": [{"type": "input_text", "text": "학사공지"}]
        }]
        
        print("\n요청: '학사공지'")
        result = provider.simple_completion(messages)
        print(f"응답: {result}")
        
    except Exception as e:
        print(f"오류 발생: {e}")
        print("(API 키가 설정되지 않았거나 네트워크 오류일 수 있습니다)")


def test_cost_calculation():
    """비용 계산 테스트"""
    print("\n[Test 5] 비용 계산")
    print("=" * 60)
    
    calculator = CostCalculator()
    
    # 단일 모델 비용 계산
    print("단일 모델 비용 계산:")
    token_usage = {"input_tokens": 1000, "output_tokens": 500}
    
    models_to_test = ["gpt-5-nano", "gemini-2.0-flash", "o3-mini"]
    for model in models_to_test:
        cost = calculator.calculate(token_usage, model)
        print(f"  {model:<20} → ${cost['total_cost_usd']:.6f} ({cost['provider']})")
    
    # 배치 비용 계산
    print("\n배치 비용 계산:")
    usage_list = [
        {"model": "gpt-5-nano", "input_tokens": 100, "output_tokens": 50},
        {"model": "gemini-2.0-flash", "input_tokens": 200, "output_tokens": 100},
        {"model": "o3-mini", "input_tokens": 500, "output_tokens": 200},
    ]
    
    result = calculator.calculate_batch(usage_list)
    print(f"  총 비용: ${result['total_cost_usd']:.6f}")
    print("\n  Provider별 비용:")
    for provider, costs in result['by_provider'].items():
        print(f"    {provider:<10} → ${costs['total_cost']:.6f}")


def test_preset_info():
    """프리셋 상세 정보 조회 테스트"""
    print("\n[Test 6] 프리셋 상세 정보")
    print("=" * 60)
    
    llm_manager = get_llm_manager()
    
    preset_name = "balanced"
    preset_info = llm_manager.preset_manager.get_preset_info(preset_name)
    
    if preset_info:
        print(f"프리셋: {preset_info.name}")
        print(f"설명: {preset_info.description}")
        print("\n역할별 모델 설정:")
        for role, config in preset_info.roles.items():
            print(f"  {role:<20} → {config['provider']:<10} / {config['model']}")
    else:
        print(f"프리셋 '{preset_name}'을 찾을 수 없습니다.")


def main():
    """전체 테스트 실행"""
    print("\n" + "=" * 60)
    print("LLM API 교체 시스템 테스트")
    print("=" * 60)
    
    try:
        # 기본 기능 테스트
        test_preset_list()
        test_preset_switch()
        test_provider_selection()
        test_preset_info()
        test_cost_calculation()
        
        # API 호출 테스트 (선택적)
        print("\n\n" + "=" * 60)
        print("실제 API 호출 테스트 (선택적)")
        print("=" * 60)
        user_input = input("\n실제 API를 호출하시겠습니까? (y/N): ")
        
        if user_input.lower() == 'y':
            test_simple_completion()
        else:
            print("API 호출 테스트를 건너뜁니다.")
        
        print("\n\n" + "=" * 60)
        print("✅ 모든 테스트 완료!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

