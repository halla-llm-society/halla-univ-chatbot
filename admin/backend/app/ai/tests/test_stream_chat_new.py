import requests
import json
from typing import List, Dict, Optional

from app.ai.llm import get_llm_manager


# 언어 선택 매핑
language_map = {
    "1": ("KOR", "한국어"),
    "2": ("ENG", "영어"),
    "3": ("VI", "베트남어"),
    "4": ("JPN", "일본어"),
    "5": ("CHN", "중국어"),
}


def select_language() -> str:
    print("언어를 선택하세요:")
    for k, v in language_map.items():
        print(f"{k}. {v[1]}")
    while True:
        choice = input("번호 입력: ").strip()
        if choice in language_map:
            return language_map[choice][0]
        print("잘못된 입력입니다. 다시 선택하세요.")


def select_preset() -> Optional[str]:
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


def print_history(history: List[Dict[str, str]]) -> None:
    """현재까지의 대화 히스토리를 출력합니다."""
    print("\n" + "=" * 80)
    print("🧾 현재 누적 대화 히스토리")
    print("=" * 80)
    for idx, item in enumerate(history, 1):
        role_display = "사용자" if item["role"] == "user" else "챗봇"
        print(f"[{idx}] {role_display}: {item['content']}")
    print("=" * 80 + "\n")


def main():
    """
    프론트엔드가 전체 대화 히스토리를 관리하는 시나리오를 테스트합니다.
    - user_input: 현재 사용자 질문 (지침 추가용)
    - message_history: 지금까지의 user/assistant 목록
    """
    url = "http://127.0.0.1:8000/api/chat"
    language = select_language()
    print(f"선택된 언어: {language}")

    history: List[Dict[str, str]] = []
    last_metadata: Optional[Dict] = None

    print("\n" + "=" * 80)
    print("🧪 프론트 주도 히스토리 테스트")
    print("=" * 80)
    print(" - exit: 종료")
    print(" - /lang: 언어 변경")
    print(" - /preset: 프리셋 변경")
    print(" - /history: 현재 히스토리 확인")
    print(" - /metadata: 마지막 메타데이터 확인")
    print("=" * 80 + "\n")

    while True:
        prompt = "\n질문 입력 (종료: exit, 언어변경: /lang, 프리셋: /preset, 히스토리: /history, 메타데이터: /metadata): "
        user_message = input(prompt).strip()

        if user_message.lower() == "exit":
            print("테스트 종료.")
            break
        if user_message.lower() in ("/lang", "/언어"):
            language = select_language()
            print(f"언어가 변경되었습니다: {language}")
            continue
        if user_message.lower() in ("/preset", "/프리셋"):
            select_preset()
            continue
        if user_message.lower() in ("/history", "/h"):
            if history:
                print_history(history)
            else:
                print("\n🪹 아직 저장된 대화가 없습니다.")
            continue
        if user_message.lower() in ("/metadata", "/meta"):
            if last_metadata:
                print("\n" + "=" * 80)
                print("📊 마지막 메타데이터")
                print("=" * 80)
                print(json.dumps(last_metadata, ensure_ascii=False, indent=2))
                print("=" * 80)
            else:
                print("\n🪹 아직 메타데이터가 없습니다. 먼저 질문을 입력하세요.")
            continue

        payload = {
            "user_input": user_message,
            "message_history": history,
            "language": language,
        }

        try:
            with requests.post(url, json=payload, stream=True) as resp:
                print("\n응답:")
                print("-" * 60)

                assistant_response = []
                last_metadata = None

                for line in resp.iter_lines(decode_unicode=True):
                    if not line or not line.strip():
                        continue

                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError:
                        print(line)
                        continue

                    event_type = event.get("type")

                    if event_type == "delta":
                        delta = event.get("content", "")
                        assistant_response.append(delta)
                        print(delta, end="", flush=True)
                    elif event_type == "completed":
                        text = event.get("text", "")
                        if text:
                            assistant_response = [text]
                            print(text)
                    elif event_type == "metadata":
                        last_metadata = event.get("data")
                  
                    elif event_type == "done":
                        print("\n[스트리밍 완료]")
                    elif event_type == "error":
                        print(f"\n❌ 오류: {event.get('message')}")
                    else:
                        print(f"\n[알 수 없는 이벤트] {event_type}: {event}")

                assistant_text = "".join(assistant_response).strip()

                # 프론트엔드 시나리오와 동일하게 사용자/어시스턴트 메시지를 히스토리에 추가
                history.append({"role": "user", "content": user_message})
                if assistant_text:
                    history.append({"role": "assistant", "content": assistant_text})
                    print("\n[히스토리 업데이트 완료]")
                else:
                    print("\n⚠️ 어시스턴트 응답이 비어 있습니다. 히스토리에 추가하지 않습니다.")

        except requests.RequestException as exc:
            print(f"\n❌ 요청 실패: {exc}")


if __name__ == "__main__":
    main()
