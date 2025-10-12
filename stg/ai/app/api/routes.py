import asyncio
import os
from openai import OpenAI
from fastapi import APIRouter, HTTPException 
from pydantic import BaseModel
from dotenv import load_dotenv  
from fastapi.responses import StreamingResponse
from ..chatbotDirectory import chatbot
from ..chatbotDirectory.functioncalling import tools, FunctionCalling
from ..chatbotDirectory.functioncalling import model
from ..chatbotDirectory.chatbot import ChatbotStream
import json


# UserRequest 클래스에 language 필드 추가
class UserRequest(BaseModel):
    message: str
    language: str = "KOR"  # 기본값은 한국어로 설정

func_calling = FunctionCalling(
    model=model.basic,
    available_functions={
        # 필요시 다른 함수도 여기에 추가
    }
)
router = APIRouter()

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

# 예시: 전역 또는 엔드포인트 내부에서 인스턴스 생성
chatbot = ChatbotStream(
    model=model.advanced,
    system_role="""당신은 학교 생활, 학과 정보, 행사 등 사용자가 궁금한 점이 있으면 아는 범위 안에서 대답합니다. 단 절대 거짓내용을 말하지 않습니다. 아는 범위에서 말하고 부족한 부분은 인정하세요.
    당신은 실시간으로 검색하는 기능이있습니다.
    당신은 한라대 공지사항을 탐색할 수 있습니다.
    당신은 한라대 학식메뉴를 탐색할 수 있습니다.
    당신은 한라대 학사일정을 탐색할 수 있습니다.""",
    instruction="당신은 사용자의 질문에 답변하는 역할을 합니다.",
    user="한라대 대학생",
    assistant="memmo"
)

# 채팅
class Message(BaseModel):
    message: str
    
@router.post("/chat")
async def stream_chat(user_input: UserRequest):
    # 1) 사용자 메시지를 원본 문맥에 추가
    chatbot.add_user_message_in_context(user_input.message)

    # 2) 언어 지침 추가
    instruction_map = {
        "KOR": "한국어로 정중하고 따뜻하게 답해주세요.",
        "ENG": "Please respond kindly in English.",
        "VI": "Vui lòng trả lời bằng tiếng Việt một cách nhẹ nhàng.",
        "JPN": "日本語で丁寧に温かく答えてください。",
        "CHN": "请用中文亲切地回答。",
        "UZB": "Iltimos, o‘zbek tilida samimiy va hurmat bilan javob bering.",
        "MNG": "Монгол хэлээр эелдэг, дулаахан хариулна уу.",
        "IDN": "Tolong jawab dengan ramah dan hangat dalam bahasa Indonesia."
    }
    instruction = instruction_map.get(user_input.language, instruction_map["KOR"])
    chatbot.context[-1]["content"] += " " + instruction

    # 3) RAG 컨텍스트 준비
    rag_ctx = chatbot.get_rag_context(user_input.message)
    has_rag = bool(rag_ctx and rag_ctx.strip())

    # 4) 함수 호출 분석 및 실행
    analyzed = func_calling.analyze(user_input.message, tools)
    func_msgs: list[dict] = []
    func_outputs: list[str] = []

    for tool_call in analyzed:
        if getattr(tool_call, "type", None) != "function_call":
            continue
        func_name = tool_call.name
        func_args = json.loads(tool_call.arguments)
        call_id = tool_call.call_id

        func_to_call = func_calling.available_functions.get(func_name)
        if not func_to_call:
            print(f"[오류] 등록되지 않은 함수: {func_name}")
            continue

        try:
            # 안전 기본값 보강
            if func_name == "get_halla_cafeteria_menu":
                func_args.setdefault("date", "오늘")
                # meal은 지정하지 않으면 전체 끼니를 반환

            func_response = (
                func_to_call(chat_context=chatbot.context[:], **func_args)
                if func_name == "search_internet"
                else func_to_call(**func_args)
            )

            func_msgs.extend([
                {
                    "type": "function_call",
                    "call_id": call_id,
                    "name": func_name,
                    "arguments": tool_call.arguments,
                },
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": str(func_response),
                },
            ])
            func_outputs.append(str(func_response))
        except Exception as e:
            print(f"[함수 실행 오류] {func_name}: {e}")

    has_funcs = len(func_outputs) > 0

    # 4-1) 학식/식단 질의 보강 호출 (LLM 누락 대비 + 결과 요약 system 주입)
    lowered = user_input.message.lower()
    cafeteria_keywords = any(k in lowered for k in ["학식", "식단", "점심", "저녁", "메뉴", "조식", "석식", "아침", "오늘 메뉴", "밥 뭐"])
    already_called_cafeteria = any(m.get("name") == "get_halla_cafeteria_menu" for m in func_msgs if m.get("type") == "function_call")


    if cafeteria_keywords and not already_called_cafeteria:
        try:
            print("[DEBUG] Cafeteria fallback engaged (missing function call)")
            # 끼니가 명시되면 해당 끼니, 아니면 전체 반환하도록 None 허용
            meal_pref = None
            if any(x in lowered for x in ["조식", "아침"]):
                meal_pref = "조식"
            elif any(x in lowered for x in ["석식", "저녁"]):
                meal_pref = "석식"
            elif "점심" in lowered or "중식" in lowered:
                meal_pref = "중식"
            date_pref = "오늘"
            if "내일" in lowered:
                date_pref = "내일"
            else:
                import re as _re
                m = _re.search(r"(\d{4}[./-]\d{1,2}[./-]\d{1,2})", user_input.message)
                if m:
                    date_pref = m.group(1)
            caf_args = {"date": date_pref, "meal": meal_pref}
            get_cafeteria_fn = func_calling.available_functions.get("get_halla_cafeteria_menu")
            if not get_cafeteria_fn:
                raise RuntimeError("get_halla_cafeteria_menu not registered")
            caf_out = get_cafeteria_fn(**caf_args)
            call_id = "cafeteria_auto"
            func_msgs.extend([
                {"type": "function_call", "call_id": call_id, "name": "get_halla_cafeteria_menu", "arguments": json.dumps(caf_args, ensure_ascii=False)},
                {"type": "function_call_output", "call_id": call_id, "output": str(caf_out)},
            ])
            func_outputs.append(str(caf_out))
            has_funcs = True
            # 간단 요약 블록 (LLM 호출 없이 규칙 기반 축약)
            first_lines = "\n".join([ln for ln in str(caf_out).splitlines()[:8]])
            cafeteria_summary_block = f"<학식요약>요청일자={date_pref}, 식사={meal_pref or '전체'}\n{first_lines}</학식요약>"
        except Exception as e:
            print(f"[보강 호출 실패] get_halla_cafeteria_menu: {e}")

    # 5) 최종 스트리밍에 사용할 컨텍스트 구성
    base_context = chatbot.to_openai_context(chatbot.context[:])
    temp_context = base_context[:]

    # 이후 하나의 system 메시지로 합칠 섹션을 수집
    sections: list[str] = []
    query_guidance = (
        f"이것은 사용자 쿼리입니다: {user_input.message}\n"
        "다음 정보를 사용자가 원하는 대답에 맞게 통합해 전달하세요.\n"
        "- 함수호출 결과: 있으면 반영\n- 기억검색 결과: 있으면 반영 / 함수 호출 존재 자체는 언급 금지"
    )
    sections.append("[사용자쿼리지침]\n" + query_guidance)
    sections.append("[일반지침]\n" + chatbot.instruction)

    if has_rag:
        # 5-1) 기억검색 결과를 그대로 넣지 않고, 먼저 LLM으로 사용자 질문에 맞게 가공/요약
        def _sanitize_text(txt: str) -> str:
            # 제어문자 제거 및 태그 충돌 방지
            if not isinstance(txt, str):
                txt = str(txt)
            # 간단 제어문자 필터링 (LF, TAB 제외)
            txt = ''.join(ch for ch in txt if ch in ('\n', '\t') or (ord(ch) >= 32 and ch != 127))
            # 태그 조기 종료 방지
            txt = txt.replace("</기억검색>", "[/기억검색]")
            # 과도한 길이 클램프 (필요시 조정)
            # 표/주석 단위의 넓은 맥락을 충분히 담기 위해 상한을 확대
            max_len = 30000
            return txt[:max_len]

        sanitized_rag = _sanitize_text(rag_ctx)

        condense_prompt = [
            {
                "role": "system",
                "content": (
                    f"""
당신은 긴 규정/세칙 문서 묶음에서 사용자 질문과 직접 관련된 부분을 "넓은 맥락"으로 추출·표시하는 어시스턴트입니다.
규칙(넓은 맥락 포함):
1) 원문 전체는 <기억검색> 태그 안에 있습니다.
2) 사용자 질문과 직접 관련된 근거는 <반영>...</반영> 태그 안에 담되, 다음을 포함하세요.
   - 표/목록/번호 조항은 해당 항목의 머리글(제목/헤더)과 인접 행·항까지 함께 포함(최소 ±5~10줄 맥락).
   - "주)" 형태의 주석/비고가 붙은 경우 해당 주석 전부 포함.
   - 학점·과목·배분영역·트랙과 같은 숫자/항목은 표의 열 머리말과 같이 포함(헤더+행 세트).
3) 사용자가 특정 번호(예: 1번, 2번)를 언급했지만 모호할 경우, 후보 번호 2~3개를 모두 포함하되 각 블록 앞에 [후보] 표기.
4) 관련 근거가 충분치 않다고 판단되면, 상위 단락(조/항/표 제목) 단위까지 확장하여 최소 15줄 이상을 담고, 지나친 요약을 피하세요.
5) 원문 구조(조/항/호/표 제목)는 유지하고 임의 재작성 금지. 반드시 원문을 거의 그대로 인용하세요.
6) 원문 밖 추론/창작 금지.

사용자 질문: {user_input.message}
<기억검색>{sanitized_rag}</기억검색>
"""
                ),
            }
        ]

        # 디버그: condense_prompt와 rag_ctx 출력
        print("==== [DEBUG] condense_prompt ====")
        for item in condense_prompt:
            print(item)
        print("==== [DEBUG] rag_ctx ====")
        print(rag_ctx)

        try:
            condensed = client.responses.create(
                model=model.advanced,
                input=condense_prompt,
                text={"format": {"type": "text"}},
            ).output_text.strip()
            print("==== [DEBUG] condensed ====")
            print(condensed)
            # 결과가 지나치게 짧으면(줄 수<15 또는 길이<1000자) 넓은 맥락 재시도
            if (condensed.count("\n") < 15) or (len(condensed) < 1000):
                print("[DEBUG] condensed too short -> retry with broader extraction")
                broader_prompt = [
                    {
                        "role": "system",
                        "content": (
                            f"""
당신은 사용자 질문과 관련된 표/번호조항/주석의 전체 맥락을 넓게 포함해 추출합니다.
반드시 다음을 지키세요:
- <반영>...</반영> 안에 헤더(표 제목/열 머리말) + 관련 행/항 전부와 해당 주석(주)까지 포함.
- 최소 25줄 이상, 가능하면 관련 블록을 통째로 포함(불필요한 요약 금지).
- 모호하면 후보 블록 2~3개를 [후보]로 나누어 모두 포함.
원문: <기억검색>{sanitized_rag}</기억검색>
질문: {user_input.message}
"""
                        ),
                    }
                ]
                try:
                    condensed2 = client.responses.create(
                        model=model.advanced,
                        input=broader_prompt,
                        text={"format": {"type": "text"}},
                    ).output_text.strip()
                    print("==== [DEBUG] condensed(broader) ====")
                    print(condensed2)
                    # 더 길고 풍부하면 교체
                    if (condensed2.count("\n") >= condensed.count("\n")) and (len(condensed2) > len(condensed)):
                        condensed = condensed2
                except Exception as _e2:
                    print(f"[DEBUG] broader extraction failed: {_e2}")
        except Exception as _e:
            # 요약 실패 시 원문을 짧게 잘라 사용
            print(f"[DEBUG] 문서 요약 실패: {_e}")
            condensed = sanitized_rag[:6000]

        rag_guidance = (
            "기억검색 결과입니다. <반영> </반영> 태그 내부 내용을 보고 사용자의 원하는 쿼리에 맞게 대답하세요. "
            "<기억검색></기억검색> 태그는 참조용이며 태그 밖 임의 창작 금지"
        )
        sections.append("[기억검색지침]\n" + rag_guidance)
        sections.append("[기억검색]\n<기억검색>\n" + condensed + "\n</기억검색>")

    web_status = None  # 'ok' | 'empty-or-error' | 'not-run'
    if has_funcs:
        # 함수 실행 결과 문자열 구성 (웹검색 결과는 분리 수집)
        formatted_blocks_other = []
        formatted_blocks_web = []
        web_outputs: list[str] = []
        # func_msgs는 [call, output, call, output, ...] 구조이므로 2개씩 묶어 처리
        try:
            for i in range(0, len(func_msgs), 2):
                call = func_msgs[i]
                if i + 1 < len(func_msgs):
                    output = func_msgs[i + 1]
                else:
                    output = {"output": "(출력 누락)"}
                if call.get("type") != "function_call":
                    continue
                name = call.get("name")
                args = call.get("arguments")
                out_text = output.get("output", "") if isinstance(output, dict) else str(output)
                # 너무 긴 출력은 잘라냄 (안전)
                max_len = 4000
                if len(out_text) > max_len:
                    out_text = out_text[:max_len] + "...<truncated>"
                # 웹검색 상태 수집
                if name == "search_internet":
                    web_outputs.append(out_text)
                    formatted_blocks_web.append(f"<function name='{name}' args='{args}'>\n{out_text}\n</function>")
                else:
                    formatted_blocks_other.append(f"<function name='{name}' args='{args}'>\n{out_text}\n</function>")
        except Exception as _fmt_e:
            print(f"[DEBUG] function result formatting error: {_fmt_e}")
        web_functions_block = "\n".join(formatted_blocks_web) if formatted_blocks_web else ""
        other_functions_block = "\n".join(formatted_blocks_other) if formatted_blocks_other else ""

        # 학식 보강 요약 블록이 있다면 포함
        try:
            if 'cafeteria_summary_block' in locals() and cafeteria_summary_block:
                functions_block += f"\n{cafeteria_summary_block}"
        except Exception:
            pass

        # 웹검색 상태 판단
        if not web_outputs:
            web_status = "not-run"
        else:
            # 하나라도 의미 있는 텍스트가 있으면 ok, 모두 오류/비어있음이면 empty-or-error
            def _is_error_or_empty(txt: str) -> bool:
                t = (txt or "").strip()
                if not t:
                    return True
                err_keywords = ["🚨", "❌", "오류", "error", "검색 결과를 찾을 수", "no result", "did_call=False"]
                return any(k.lower() in t.lower() for k in err_keywords)
            all_bad = all(_is_error_or_empty(t) for t in web_outputs)
            web_status = "empty-or-error" if all_bad else "ok"

        # 지침: 웹검색 결과는 따로 표기하고, 우회/문의 안내만 있는 경우 참고만 하도록 명시
        web_guidance = (
            "다음은 인터넷 검색결과입니다. 공식 근거가 아니므로 참고용으로만 사용하세요. "
            "검색이 안되어 우회/문의 안내만 있을 경우, 무시하고 이 내용은'참조만' 하세요. 반드시 기억검색 근거를 우선 반영하세요. 참조란 안내 전화번호 사이트만을 반영하는것을 말합니다 "
        )
        sections.append("[웹검색지침]\n" + web_guidance)
        if web_functions_block:
            sections.append("[인터넷 검색결과]\n<인터넷검색>\n" + web_functions_block + "\n</인터넷검색>")

        func_guidance = (
            "다음은 함수(검색/메뉴 등) 호출 결과입니다. <함수결과> 태그 내부 내용은 참고용이며, 반드시 아래 기억검색(<기억검색>) 근거를 우선 답변에 반영하세요. "
            "'함수 호출'이라는 표현은 사용하지 말고, 거짓 정보 생성 금지."
        )
        sections.append("[함수결과지침]\n" + func_guidance)
        if other_functions_block:
            sections.append("[함수결과]\n<함수결과>\n" + other_functions_block + "\n</함수결과>")
        # 웹검색 상태 표시 (있을 때만)
        if web_status and web_status != "not-run":
            status_kr = {
                "ok": "정상",
                "empty-or-error": "결과없음/오류",
                "not-run": "실행안함",
            }[web_status]
            sections.append("[웹검색상태]\n" + status_kr)

        # 웹검색이 없거나 실패했을 때의 답변 지침 (불필요한 말 금지)
        if web_status in ("empty-or-error", "not-run"):
            if has_rag:
                sections.append(
                    "[웹검색결과없음지침]\n인터넷 검색결과는 참고용입니다. 공식 규정은 아래 기억검색(<기억검색>) 근거를 반드시 우선 확인하세요. 검색이 되지 않거나 문의 안내만 있을 경우, 해당 내용은 참고만 하시고 반드시 아래 규정 근거를 답변에 반영하세요."
                )
            else:
                sections.append(
                    "[웹검색결과없음지침]\n웹검색 결과는 없었습니다. 관련 근거를 찾지 못했음을 한 문장으로 간단히 알리고, 필요한 추가 정보를 한 문장으로 요청하세요."
                )
       

    if has_rag and has_funcs:
        # 웹검색이 비어도(결과없음/오류) 기억검색이 있으면 '정보 없음'이라고 결론내리지 말라는 규칙 추가
        extra = " 웹검색이 결과없음/오류여도 기억검색이 존재하면 '정보 없음'이라고 하지 말고 기억검색 근거로 답할 것."
        if web_status == "empty-or-error":
            extra_note = extra
        else:
            extra_note = ""
        merge_instruction = (
            "위 기억검색 근거(<기억검색>)와 인터넷 검색결과(<인터넷검색>), 기타 함수결과(<함수결과>)를 대조하여 모순 없이 답하세요. "
            "핵심 답 먼저 제시하고, 필요한 근거만 축약 인용. 인터넷 검색결과는 참고용이며, 우회/문의 안내만 있을 경우 '참조만' 하고 -참조란 안내 전화번호 사이트만을 반영하는것을 말합니다   "
            "반드시 기억검색 근거를 우선 반영하세요. 근거가 없으면 그 사실을 명시." + extra_note
        )
        sections.append("[통합지침]\n" + merge_instruction)

    # 단일 system 메시지로 병합 추가
    temp_context.append({
        "role": "system",
        "content": "\n\n".join(sections)
    })

    # 둘 다 없으면 원본 컨텍스트만 사용해 일반 응답
    context_to_stream = temp_context if (has_rag or has_funcs) else base_context

    # 6) 스트리밍 응답 생성 및 최종 문맥 저장
    async def generate_with_tool():
        completed_text = ""
        try:
            stream = client.responses.create(
                model=chatbot.model,
                input=context_to_stream,
                top_p=1,
                stream=True,
                text={"format": {"type": "text"}},
            )

            loading = True
            for event in stream:
                match event.type:
                    # case "response.created":
                    #     loading = True
                    #     yield "⏳ GPT가 응답을 준비 중입니다..."
                    #     await asyncio.sleep(0)
                    case "response.output_text.delta":
                        # if loading:
                        #     yield "\n[� 응답 시작됨 ↓]"
                        #     loading = False
                        yield f"{event.delta}"
                        await asyncio.sleep(0)
                    # case "response.in_progress":
                    #     yield "\n[🌀 응답 생성 중...]\n"
                    case "response.output_item.done":
                        item = event.item
                        if item.type == "message" and item.role == "assistant":
                            for part in item.content:
                                if getattr(part, "type", None) == "output_text":
                                    completed_text = part.text
                    # case "response.completed":
                    #     yield "\n"
                    # case "response.failed":
                    #     yield "❌ 응답 생성 실패"
                    # case "error":
                    #     yield "⚠️ 스트리밍 중 에러 발생!"
                    # case _:
                    #     yield f"\n[📬 기타 이벤트 감지: {event.type}]"
        except Exception as e:
            yield f"\nStream Error: {str(e)}"
        finally:
            if completed_text:
                chatbot.add_response_stream(completed_text)
            print(context_to_stream)

    return StreamingResponse(generate_with_tool(), media_type="text/plain")