import json
import requests
from pprint import pprint
import re
import time
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass

# LLM Manager import
try:
    from app.ai.llm import get_provider
except ImportError:
    # 상대 경로로 시도
    from ..llm import get_provider

# 순환 참조 방지: config 대신 직접 생성
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/
_DOTENV_PATH = _BASE_DIR / "apikey.env"
load_dotenv(_DOTENV_PATH)

@dataclass(frozen=True)
class Model: 
    basic: str = "gpt-3.5-turbo-1106"
    advanced: str = "gpt-4.1"
    o3_mini: str = "o3-mini"
    o1: str = "o1"

model = Model()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key, max_retries=1)

def makeup_response(message, finish_reason="ERROR"):
    '''api 응답형식으로 반환해서
       개발자가 임의로 생성한 메세지를
       기존 출력 함수로 출력하는 용도인 함수'''
    return {
        "choices": [
            {
                "finish_reason": finish_reason,
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": message
                }                   
            }
        ],
        "usage": {"total_tokens": 0},
    }
    
tools = [
        
            {
            "type": "function",
            "name": "search_internet",
            "description": "Searches the internet based on user input and retrieves relevant information",
            "parameters": {
                "type": "object",
                "required": [
                "user_input"
                ],
                "properties": {
                "user_input": {
                    "type": "string",
                    "description": "User's search query input(conversation context will be automatically added)"
                }
                },
                "additionalProperties": False
            }
            },
            {
            "type": "function",
            "name": "get_halla_cafeteria_menu",
            "description": "원주 한라대학교 학생식당의 메뉴를 궁금해 하면 이 함수를 호출하세요. 주간 식단 페이지에서 특정 날짜/끼니의 메뉴를 추출합니다.",
            "parameters": {
                "type": "object",
                "required": ["date"],
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "조회할 날짜. 형식 YYYY-MM-DD 또는 YYYY.MM.DD. '오늘', '내일' 허용. 기본값은 '오늘'입니다.",
                    },
                    "meal": {
                        "type": "string",
                        "enum": ["조식", "중식", "석식"],
                        "description": "조회할 끼니. 지정하지 않으면 전체 끼니를 보여줍니다.",
                    }
                },
                "additionalProperties": False
            }
            },
      
       
      
    ]

# --- 공지 카테고리 LLM 분류기 ---
async def _classify_notice_category_llm(user_input: str, context_info: str | None = None, token_counter=None) -> str | None:
    """사용자 입력이 어떤 공지사항 카테고리인지 LLM으로 분류하여 카테고리 문자열을 반환.
    반환 가능 값: "학사공지", "비교과공지", "장학공지", "일반공지", "해당없음". 인식 실패 시 None.
    """
    try:
        allowed = ["학사공지", "비교과공지", "장학공지", "일반공지", "해당없음"]
        prompt = (
            "다음 사용자의 요청이 한라대학교 '공지' 중 어떤 카테고리에 해당하는지 하나만 선택해 답하세요.\n"
            "카테고리: 학사공지 | 비교과공지 | 장학공지 | 일반공지 | 해당없음\n"
            "규칙:\n"
            "- 정확히 위의 단어 중 하나만 출력하세요. 다른 말, 설명, 따옴표 없이.\n"
            f"사용자 입력: {user_input}\n"
            f"대화 문맥: {context_info or '(없음)'}\n\n"
            "정답:"
        )

        # LLM Manager를 통해 Provider 선택 (교체 가능)
        provider = get_provider("category")
        messages = [{
            "role": "user",
            "content": [{"type": "input_text", "text": prompt}],
        }]
        raw, usage = await provider.simple_completion(messages)
        raw = raw.strip()

        # ✅ API usage 기반 토큰 계산
        if token_counter and usage:
            token_counter.update_from_api_usage(
                usage=usage,
                role="category",
                model=provider.get_model_name(),
                category="function"
            )
        
        print("공지 카테고리 분류기 원문:", raw)
        # 정규화 및 선택
        text_norm = raw.replace(" ", "").replace("\n", "")
        for a in allowed:
            if a in text_norm:
                return a
        return None
    except Exception as e:
        print(f"[_classify_notice_category_llm] Error: {e}")
        return None

# --- 규칙 기반 사이트 선호 라우팅 ---
async def _prefer_halla_site_query(user_input: str, context_info: str | None = None, token_counter=None) -> str | None:
    """특정 요구사항일 때 한라대 특정 페이지를 우선 탐색하도록 검색어를 구성.
    매칭되면 URL과 site 필터를 포함한 쿼리를 반환, 없으면 None.
    """
    base = (context_info or "")
    text = f"{user_input}\n{base}".lower()

    # 메뉴/학식 라우팅
    menu_keywords = ["학식", "식단", "메뉴", "점심", "저녁", "오늘 메뉴"]
    if any(k in text for k in menu_keywords):
        url = "https://www.halla.ac.kr/kr/211/subview.do"
        return f"site:halla.ac.kr {url} {user_input}"

    # 공지 라우팅: LLM 분류 기반 → 실패 시 키워드 기반 폴백
    category = await _classify_notice_category_llm(user_input, context_info, token_counter)
    category_to_url = {
        "학사공지": "https://www.halla.ac.kr/kr/242/subview.do",
        "비교과공지": "https://www.halla.ac.kr/kr/243/subview.do",
        "장학공지": "https://www.halla.ac.kr/kr/244/subview.do",
        "일반공지": "https://www.halla.ac.kr/kr/241/subview.do",
    }
    if category and category != "해당없음":
        url = category_to_url.get(category)
        if url:
            return f"site:halla.ac.kr {url} {user_input}"

    # 폴백: 단순 키워드 매칭
    if "학사공지" in text:
        url = "https://www.halla.ac.kr/kr/242/subview.do"
        return f"{user_input} site:halla.ac.kr {url} "
    if "비교과" in text or "비교과공지" in text:
        url = "https://www.halla.ac.kr/kr/243/subview.do"
        return f"{user_input} site:halla.ac.kr {url}"
    if "장학" in text:
        url = "https://www.halla.ac.kr/kr/244/subview.do"
        return f"{user_input} site:halla.ac.kr {url} "
    if "일반공지" in text or "공지" in text:
        url = "https://www.halla.ac.kr/kr/241/subview.do"
        return f"{user_input} site:halla.ac.kr {url}"

    # 미매칭 시 라우팅 없음
    return None

async def search_internet(user_input: str, chat_context=None, token_counter=None) -> str:
    start_ts = time.time()
    print(f"[WEB][START] query='{user_input}' chat_ctx={'Y' if chat_context else 'N'}")
    try:
        if chat_context:
            print("[WEB] context available -> trimming recent messages")
            recent_messages = chat_context[-4:]
            context_info = "\n".join([
                f"{m.get('role','unknown')}: {m.get('content','')}" for m in recent_messages if m.get('role') != 'system'
            ])
        else:
            recent_messages = []
            context_info = ""

        preferred = await _prefer_halla_site_query(user_input, context_info if context_info else None, token_counter)
        
        # LLM 에이전트로 검색어 재작성 (context_info 포함)
        rewrite_prompt = (
            f"{user_input}\n\n[대화 문맥]: {context_info} 를 참고해 (이전 문맥과 연결된 후속 질문이면 연관된 핵심 키워드 포함) "
            "간결한 검색어 조합을 새로 만들어라. 가능하면 site:halla.ac.kr 또는 관련 공식 URL 포함."
        )
        
        # preferred가 있으면 추가 정보로 활용
        if preferred:
            rewrite_prompt += f"\n\n[추천 사이트]: {preferred}"
        
        provider = get_provider("search_rewrite")
        messages = [{"role": "user", "content": [{"type": "input_text", "text": rewrite_prompt}]}]
        search_text, usage = await provider.simple_completion(messages)
        search_text = search_text.strip()

        # ✅ API usage 기반 토큰 계산
        if token_counter and usage:
            token_counter.update_from_api_usage(
                usage=usage,
                role="search_rewrite",
                model=provider.get_model_name(),
                category="function"
            )
        print(f"[WEB] final_search_text='{search_text}'")

        context_input = [{
            "role": "user",
            "content": [{"type": "input_text", "text": search_text}]
        }]

        call_ts = time.time()
        response = client.responses.create(
            model=model.advanced,
            input=context_input,
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[{
                "type": "web_search_preview",
                "user_location": {"type": "approximate", "country": "KR"},
                "search_context_size": "medium"
            }],
            tool_choice={"type": "web_search_preview"},
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        print(f"[WEB] openai.responses.create elapsed={time.time()-call_ts:.2f}s total={time.time()-start_ts:.2f}s")

        # ✅ API usage 추적 (web_search 역할)
        if token_counter:
            if hasattr(response, 'usage') and response.usage:
                # API usage 정보 추출
                input_tok = getattr(response.usage, "input_tokens", 0)
                output_tok = getattr(response.usage, "output_tokens", 0)

                # reasoning_tokens 추출 (필요시)
                reasoning_tok = 0
                if hasattr(response.usage, 'output_tokens_details') and response.usage.output_tokens_details:
                    reasoning_tok = getattr(response.usage.output_tokens_details, 'reasoning_tokens', 0)

                # total_tokens 계산
                total_tok = getattr(response.usage, "total_tokens", input_tok + output_tok)

                usage_data = {
                    "input_tokens": input_tok,
                    "output_tokens": output_tok,
                    "reasoning_tokens": reasoning_tok,
                    "total_tokens": total_tok,
                }

                token_counter.update_from_api_usage(
                    usage=usage_data,
                    role="web_search",
                    model=model.advanced,  # gpt-4.1
                    category="function",
                    replace=False
                )
                print(f"[TokenTrack][web_search] ✅ API usage tracked: input={input_tok}, output={output_tok}, reasoning={reasoning_tok}")
            else:
                print(f"[TokenTrack][web_search] ⚠️ No API usage available")

        did_call = any(getattr(item, "type", None) == "web_search_call" for item in getattr(response, "output", []))
        print(f"[WEB] search_call_performed={did_call}")

        message = next((item for item in response.output if getattr(item, "type", None) == "message"), None)
        if not message:
            return "❌ GPT 응답 메시지를 찾을 수 없습니다."
        content_block = next((block for block in message.content if getattr(block, "type", None) == "output_text"), None)
        if not content_block:
            return "❌ GPT 응답 내 output_text 항목을 찾을 수 없습니다."
        output_text = getattr(content_block, "text", "").strip()
        annotations = getattr(content_block, "annotations", [])
        citations = []
        for a in annotations:
            if getattr(a, "type", None) == "url_citation":
                title = getattr(a, "title", "출처")
                url = getattr(a, "url", "")
                if url:
                    citations.append(f"[{title}]({url})")
        result = output_text
        if citations:
            result += "\n\n📎 출처:\n" + "\n".join(citations)
        print(f"[WEB][END] success total_elapsed={time.time()-start_ts:.2f}s")
        return result + "\n[WEB_METADATA]elapsed={:.2f}s did_call={}".format(time.time()-start_ts, did_call)
    except Exception as e:
        print(f"[WEB][ERROR] {e} total_elapsed={time.time()-start_ts:.2f}s")
        return f"🚨 웹검색 오류: {str(e)}"


def _parse_date_input(date_text: Optional[str]) -> datetime.date:
    today = datetime.now().date()
    if not date_text:
        return today
    s = str(date_text).strip()
    # 상대 날짜 지원
    if s in ("오늘", "today"):
        return today
    if s in ("내일", "tomorrow"):
        return today + timedelta(days=1)
    if s in ("어제", "yesterday"):
        return today - timedelta(days=1)
    if s in ("모레", "day after tomorrow"):
        return today + timedelta(days=2)
    # Normalize separators and parse flexibly (YYYY.M.D or YYYY.MM.DD)
    s_norm = s.replace("/", ".").replace("-", ".")
    parts = s_norm.split(".")
    if len(parts) == 3 and all(p.isdigit() for p in parts):
        y, m, d = map(int, parts)
        return datetime(year=y, month=m, day=d).date()
    # 한국어 표기: 9월 7일 (연도 생략 시 올해)
    m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", s)
    if m:
        y = today.year
        month = int(m.group(1))
        day = int(m.group(2))
        return datetime(year=y, month=month, day=day).date()
    raise ValueError("날짜 형식은 YYYY-MM-DD / YYYY.M.D / '오늘/내일/어제'를 사용하세요.")


def get_halla_cafeteria_menu(date: Optional[str] = None, meal: Optional[str] = None) -> str:
    """원주 한라대 학생식당 주간 식단 페이지를 파싱하여 특정 날짜/끼니 메뉴를 반환.
    제한: 서버가 주차 변경을 JS/폼으로 처리하면 과거/미래 주 선택은 어려울 수 있음. 이 경우 현재 주만 반환.
    """
    t0 = time.time()
    print(f"[CAF][START] date={date} meal={meal}")
    try:
        target_date = _parse_date_input(date)
    except Exception as e:
        print(f"[CAF][ERROR] date-parse {e}")
        return f"❌ 날짜 해석 실패: {e}"

    url = "https://www.halla.ac.kr/kr/211/subview.do"
    try:
        net_t = time.time()
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        print(f"[CAF] fetch ok elapsed={time.time()-net_t:.2f}s status={resp.status_code}")
    except Exception as e:
        print(f"[CAF][ERROR] fetch {e}")
        return f"❌ 페이지 요청 실패: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")

    # 주간 범위 텍스트 찾기 (예: 2025.08.25 ~ 2025.08.31)
    text = soup.get_text("\n", strip=True)
    m = re.search(r"(\d{4}\.\d{2}\.\d{2})\s*~\s*(\d{4}\.\d{2}\.\d{2})", text)
    week_start = week_end = None
    if m:
        try:
            week_start = datetime.strptime(m.group(1), "%Y.%m.%d").date()
            week_end = datetime.strptime(m.group(2), "%Y.%m.%d").date()
        except Exception:
            pass

    # 현재 주 확인 및 대상 날짜가 해당 주에 포함되는지 체크
    if week_start and week_end and not (week_start <= target_date <= week_end):
        # 다른 주일 경우, 서버가 파라미터 없이 현재 주만 제공하면 한계 안내
        info = f"현재 페이지는 {week_start}~{week_end} 주간 식단입니다."
        return info + " 원하는 날짜는 다른 주입니다. 페이지가 주차 파라미터를 제공하지 않아 현재 주만 조회 가능합니다: " + url

    # 테이블 탐색: 요일 헤더와 끼니 라벨이 있는 표를 찾아 파싱
    tables = soup.find_all("table")

    days = ["월", "화", "수", "목", "금", "토", "일"]
    weekday_idx = target_date.weekday()  # 0=월
    target_day_label = days[weekday_idx]

    def clean(txt: str) -> str:
        return re.sub(r"\s+", " ", txt).strip()

    def pick_table_and_parse() -> dict:
        # 반환: {"조식": str|None, "중식": str|None, "석식": str|None}
        result = {"조식": None, "중식": None, "석식": None}
        for tbl in tables:
            rows = tbl.find_all("tr")
            if not rows:
                continue
            # 1) 요일 열 인덱스 매핑 찾기 (헤더 1~2행을 살펴봄)
            day_col_index = None
            header_candidates = rows[:2] if len(rows) >= 2 else rows[:1]
            for hdr in header_candidates:
                cells = hdr.find_all(["th", "td"])
                for i, c in enumerate(cells):
                    txt = clean(c.get_text())
                    if target_day_label in txt or (txt.endswith("요일") and target_day_label in txt):
                        day_col_index = i
                        break
                if day_col_index is not None:
                    break

            # 일부 표는 첫 열이 '구분', 이후 월~일이므로 day_col_index를 못 찾으면 월~일 패턴으로 추정
            if day_col_index is None:
                # 헤더 행에서 월~일이 연속으로 나타나는지 확인
                for hdr in header_candidates:
                    cells = [clean(c.get_text()) for c in hdr.find_all(["th", "td"])]
                    if any(d in "".join(cells) for d in days):
                        # 기본적으로 첫 열이 라벨, 이후 월=1, 화=2 ...로 가정
                        day_col_index = 1 + weekday_idx
                        break

            if day_col_index is None:
                continue

            # 2) 끼니 라벨 행을 찾아 해당 요일 열의 셀을 추출
            for tr in rows:
                cells = tr.find_all(["th", "td"])
                if not cells:
                    continue
                label = clean(cells[0].get_text()) if cells else ""
                # 끼니명은 변형될 수 있어 부분 일치 허용 (예: 중식(11:30~13:30))
                for meal_label in list(result.keys()):
                    if meal_label in label:
                        # 요일 열이 범위 안에 있는지 확인
                        if len(cells) > day_col_index:
                            result[meal_label] = clean(cells[day_col_index].get_text())
            # 하나라도 수집되었으면 이 테이블을 채택
            if any(v for v in result.values()):
                return result
        return result

    parse_t = time.time()
    found = pick_table_and_parse()
    print(f"[CAF] primary-parse elapsed={time.time()-parse_t:.2f}s result={found}")

    # 폴백: 표 파싱 실패 시 페이지 텍스트에서 라인 기반 추론(부정확할 수 있음)
    if all(v is None for v in found.values()):
        lines = [l for l in text.split("\n") if l]
        # 매우 단순 추정: '중식 | ...' 같은 라인이 있으면 그 다음 토큰들을 사용
        for key in list(found.keys()):
            for ln in lines:
                if key in ln and "|" in ln:
                    # 파이프 구분으로 분해 후 요일 인덱스 사용
                    parts = [clean(p) for p in ln.split("|")]
                    # parts 예: [라벨, 조식, 월, 화, 수, ...] 형태일 수 있음 → 월이 parts에서 어디에 있는지 동적으로 탐색
                    try:
                        # 월~일 중 target_day_label의 첫 등장 위치를 찾음
                        day_pos = None
                        for i, token in enumerate(parts):
                            if token.startswith(target_day_label):
                                day_pos = i
                                break
                        if day_pos is None:
                            # 기본 오프셋 가정: [라벨, 끼니, 월, 화, 수, ...]
                            base = 2
                            day_pos = base + weekday_idx
                        if len(parts) > day_pos:
                            found[key] = parts[day_pos]
                    except Exception:
                        pass
                        break

    # 결과 구성
    day_label = target_day_label
    header = f"한라대 학생식당 식단 ({target_date} {day_label})"

    if meal in ("조식", "중식", "석식"):
        val = found.get(meal)
        if not val:
            out = header + f"\n[{meal}] 정보 없음\n추가 사항: 원문: {url}"
            print(f"[CAF][END] elapsed={time.time()-t0:.2f}s meal-miss")
            return out
        out = header + f"\n[{meal}] {val}\n추가 사항: 원문: {url}"
        print(f"[CAF][END] elapsed={time.time()-t0:.2f}s meal-hit")
        return out

    # 3끼 모두 반환
    lines_out = []
    for k in ["조식", "중식", "석식"]:
        v = found.get(k)
        lines_out.append(f"[{k}] {v if v else '정보 없음'}")
    out = header + "\n" + "\n".join(lines_out) + f"\n추가 사항: 원문: {url}"
    print(f"[CAF][END] elapsed={time.time()-t0:.2f}s all-meals")
    return out

class FunctionCalling:
    def __init__(self, model, available_functions=None, token_counter=None):
        self.model = model
        self.token_counter = token_counter
        default_functions = {
            "search_internet": search_internet,
            "get_halla_cafeteria_menu": get_halla_cafeteria_menu,
        }

        if available_functions:
            default_functions.update(available_functions)

        self.available_functions = default_functions
       
    async def analyze(self, user_message, tools):
        """사용자 메시지를 분석하여 필요한 함수와 판단 근거를 반환

        Returns:
            dict: {
                "reasoning": str (판단 근거),
                "output": list (함수 호출 목록, 기존 response.output 형식)
            }
        """
        if not user_message or user_message.strip() == "":
            return {
                "reasoning": "입력이 비어있어 함수를 선택할 수 없습니다.",
                "output": []
            }
        
        # 1단계: LLM으로 함수 선택 이유 생성 (structured output)
        reasoning = None
        try:
            from app.ai.chatbot import character
            from app.ai.llm import get_provider
            
            prompt = [
                {"role": "system", "content": character.decide_function},
                {"role": "user", "content": user_message},
            ]
            
            schema = {
                "type": "object",
                "properties": {
                    "reasoning": {"type": "string"},
                    "selected_tools": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                },
                "required": ["reasoning", "selected_tools"],
                "additionalProperties": False,
            }
            
            provider = get_provider("function_analyze")
            raw, usage = await provider.structured_completion(prompt, schema)
            raw = raw.strip()

            # ✅ API usage 기반 토큰 계산
            if self.token_counter and usage:
                self.token_counter.update_from_api_usage(
                    usage=usage,
                    role="function_analyze",
                    model=provider.get_model_name(),
                    category="function"
                )
            
            if raw:
                payload = json.loads(raw)
                reasoning = payload.get("reasoning", "").strip() or None
                selected_tools = payload.get("selected_tools", [])
        except Exception as e:
            reasoning = f"추론 생성 실패 ({e})"
            selected_tools = []  # exception 발생 시 기본값 설정

        # 2단계: 기존 함수 호출 분석 (OpenAI API)

        structured_input = [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_message}
                ],
            }
        ]
        try:
            response = client.responses.create(
                model=model.o3_mini,
                input=structured_input,
                tools=tools,
                tool_choice="auto",
            )

            if self.token_counter and hasattr(response, 'usage') and response.usage:
                usage_data = {
                    "input_tokens": getattr(response.usage, "input_tokens", 0),
                    "output_tokens": getattr(response.usage, "output_tokens", 0),
                    "total_tokens": getattr(response.usage, "total_tokens", 0),
                    "reasoning_tokens": getattr(response.usage.output_tokens_details, 'reasoning_tokens', 0) if hasattr(response.usage, 'output_tokens_details') else 0,
                }
                self.token_counter.update_from_api_usage(
                    usage=usage_data,
                    role="function_calling",
                    model=model.o3_mini,
                    category="function",
                    replace=False
                )

            return {
                "reasoning": reasoning,
                "selected_tools": selected_tools,  # reasoning에서 선택된 도구 목록 추가
                "output": response.output
            }
        except Exception as e:
            return {
                "reasoning": reasoning,
                "selected_tools": selected_tools,
                "output": []
            }
    

    def run(self, analyzed,context):
        ''' analyzed_dict: 함수 호출 정보, context: 현재 문맥'''
        context.append(analyzed)
        for tool_call in analyzed:
            if tool_call.get("type") != "function_call":
                continue
            function=tool_call["function"]
            func_name=function["name"]
            #실제 함수와 연결
            func_to_call = self.available_functions[func_name]

            try:

                func_args=json.loads(function["arguments"])#딕셔너리로 변환-> 문자열이 json형태입-> 이걸 딕셔너리로 변환
                
                if func_name == "search_internet":
                    # context는 이미 run 메서드의 매개변수로 받고 있음
                    func_response = func_to_call(chat_context=context[:], **func_args)
                else:
                    func_response=func_to_call(**func_args)
                context.append({
                    "tool_call_id": tool_call["id"],
                    "role": "tool",
                    "name": func_name, 
                    "content": str(func_response),
                    "parallel_tool_calls": True
                })#실행 결과를 문맥에 추가
  

            except Exception as e:
                print("Error occurred(run):",e)
                return makeup_response("[run 오류입니다]")

        # 함수 실행 후 최종 응답 생성
        response = client.responses.create(model=self.model, input=context)

        # ✅ API usage 추적 (function_calling 역할 - 재호출)
        if self.token_counter and hasattr(response, 'usage') and response.usage:
            usage_data = {
                "input_tokens": getattr(response.usage, "input_tokens", 0),
                "output_tokens": getattr(response.usage, "output_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
                "reasoning_tokens": getattr(response.usage.output_tokens_details, 'reasoning_tokens', 0) if hasattr(response.usage, 'output_tokens_details') else 0,
            }
            self.token_counter.update_from_api_usage(
                usage=usage_data,  # ✅ 수정: usage_info → usage
                role="function_calling",
                model=self.model,  # ✅ 추가: 필수 파라미터
                category="function",
                replace=False
            )

        return response.model_dump()
    
   
    def call_function(self, analyzed_dict):        
        func_name = analyzed_dict["function_call"]["name"]
        func_to_call = self.available_functions[func_name]                
        try:            
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
            func_response = func_to_call(**func_args)
            return str(func_response)
        except Exception as e:
            print("Error occurred(call_function):",e)
            return makeup_response("[call_function 오류입니다]")
    