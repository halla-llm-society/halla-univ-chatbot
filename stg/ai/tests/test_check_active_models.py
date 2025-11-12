"""
현재 활성화된 LLM 프리셋과 각 역할별 모델 설정을 확인하는 테스트
"""
import sys
from pathlib import Path

# app 모듈을 import하기 위한 경로 설정
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.ai.llm import get_llm_manager


def main():
    print("=" * 80)
    print("🔍 현재 LLM 설정 확인")
    print("=" * 80)

    llm_manager = get_llm_manager()
    
    # 1. 활성 프리셋 확인
    active_preset = llm_manager.get_active_preset()
    print(f"\n📌 활성 프리셋: {active_preset}")
    
    # 2. 프리셋 정보 가져오기
    preset_config = llm_manager.preset_manager.config.get("presets", {}).get(active_preset)
    if preset_config:
        print(f"   설명: {preset_config.get('description', 'N/A')}")
    
    # 3. 각 역할별 모델 설정 출력
    print("\n📊 역할별 모델 설정:")
    print("-" * 80)
    
    # 가변 역할 (프리셋으로 변경 가능)
    variable_roles = ["category", "search_rewrite", "condense", "gate", "function_analyze"]
    print("\n🔄 가변 역할 (프리셋으로 변경 가능):")
    role_descriptions = llm_manager.preset_manager.config.get("role_descriptions", {})
    for role in variable_roles:
        config = llm_manager.preset_manager.get_role_config(role)
        provider = config.get("provider", "N/A")
        model = config.get("model", "N/A")
        description = role_descriptions.get(role, "")
        print(f"  • {role:20} → {provider:10} / {model:20} ({description})")
    
    # 고정 역할 (변경 불가)
    print("\n🔒 고정 역할 (OpenAI 전용):")
    fixed_roles = llm_manager.preset_manager.config.get("fixed_roles", {})
    for role, config in fixed_roles.items():
        provider = config.get("provider", "N/A")
        model = config.get("model", "N/A")
        reason = config.get("reason", "")
        description = role_descriptions.get(role, "")
        print(f"  • {role:20} → {provider:10} / {model:20}")
        print(f"    이유: {reason}")
        if description:
            print(f"    설명: {description}")
    
    # 4. 사용 가능한 모든 프리셋 목록
    print("\n\n📋 사용 가능한 프리셋 목록:")
    print("-" * 80)
    presets = llm_manager.preset_manager.list_presets()
    for idx, preset in enumerate(presets, 1):
        marker = "✅" if preset["name"] == active_preset else "  "
        print(f"{marker} {idx}. {preset['name']}")
        print(f"     {preset['description']}")
    
    print("\n" + "=" * 80)
    print("💡 프리셋 변경: llm_config.yaml의 'active_preset' 값을 변경하고 서버를 재시작하세요.")
    print("=" * 80)


if __name__ == "__main__":
    main()
