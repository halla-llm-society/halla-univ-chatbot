import json
import requests
import httpx
from pprint import pprint
import re
import time
import logging
from datetime import datetime, timedelta
from typing import Optional
from bs4 import BeautifulSoup
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# LLM Manager import
try:
    from app.ai.llm import get_provider
except ImportError:
    # 상대 경로로 시도
    from ..llm import get_provider

# ShuttleBus Service import
try:
    from app.ai.functions.shuttle_bus_service import ShuttleBusService
except ImportError:
    from .shuttle_bus_service import ShuttleBusService

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

# 함수 정의는 function_prompts.py에서 가져옴
try:
    from app.ai.chatbot.function_prompts import get_function_definitions
    tools = get_function_definitions()
    logger.debug("[ANALYZER][INIT] ✅ Successfully imported function definitions from function_prompts.py")
except ImportError as e:
    # 폴백: 기존 하드코딩 방식
    logger.warning(f"[ANALYZER][INIT] ⚠️ Failed to import function_prompts: {e}")
    logger.debug(f"[ANALYZER][INIT] Using fallback hardcoded function definitions")
    import traceback
    traceback.print_exc()
    tools = [
        
            {
            "type": "function",
            "name": "search_internet",
            "description": """인터넷에서 최신 정보를 검색하는 함수입니다.

            ⚠️ 이 함수를 사용해야 하는 경우:
            - 최신 공지사항, 뉴스, 이벤트 정보
            - 한라대학교 웹사이트의 최신 정보
            - 일반적인 웹 검색이 필요한 경우

            ❌ 이 함수를 사용하지 말아야 하는 경우:
            - 통학버스, 셔틀버스 관련 질문 → get_shuttle_bus_info 사용
            - 학식, 식단 관련 질문 → get_halla_cafeteria_menu 사용
            - 학사규정 관련 질문 → RAG 시스템 사용 (자동 처리)

            통학버스 시간표, 탑승 위치, 예약 방법 등은 반드시 get_shuttle_bus_info 함수를 사용하세요.""",
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
            "description": "원주 한라대학교 학생식당과 교직원식당의 메뉴를 조회합니다. 주간 식단 페이지에서 특정 날짜/끼니의 메뉴를 추출합니다. 학생식당(/kr/211/)과 교직원식당(/kr/212/) 모두 지원합니다.",
            "parameters": {
                "type": "object",
                "required": ["date"],
                "properties": {
                    "date": {
                        "type": "string",
                        "description": """반드시 YYYY-MM-DD 형식으로 계산하여 전달하세요.
                                오늘 날짜를 기준으로 직접 계산:
                                - "오늘" → 오늘 날짜 
                                - "내일" → 오늘+1일
                                - "모레" → 오늘+2일
                                - "글피/그을피" → 오늘+3일
                                - "그글피" → 오늘+4일
                                - "다음주 월요일" → 해당 날짜 계산
                                사용자가 어떤 표현을 쓰든 YYYY-MM-DD로 변환하여 전달.""",
                    },
                    "meal": {
                        "type": "string",
                        "enum": ["조식", "중식", "석식"],
                        "description": "조회할 끼니. 지정하지 않으면 전체 끼니를 보여줍니다.",
                    },
                    "cafeteria_type": {
                        "type": "string",
                        "enum": ["학생", "교직원"],
                        "description": "식당 종류. '학생' 또는 '교직원'. 기본값은 '학생'입니다. 사용자가 '교직원', '교수', '직원' 등의 키워드를 언급하면 '교직원'을 선택하세요.",
                    }
                },
                "additionalProperties": False
             }
            },
            {
            "type": "function",
            "name": "get_halla_academic_calendar",
            "description": "한라대학교 학사일정을 조회합니다. 특정 월의 학사 일정(개강, 종강, 시험, 방학 등)을 제공합니다.",
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {
                    "month": {
                        "type": "string",
                        "description": """조회할 월을 지정합니다.
                            허용 형식:
                            - 상대 월: "이번달", "다음달", "지난달"
                            - 절대 월: "3월", "12월" (올해 기준)
                            - YYYY-MM 형식: "2025-03"
                            - YYYY년 MM월: "2025년 3월"
                            - 숫자: "3", "12" (1~12는 월로 해석)
                            기본값: 현재 월""",
                    }
                },
                "additionalProperties": False
            }
            },
            {
            "type": "function",
            "name": "get_shuttle_bus_info",
            "description": """한라대학교 통학버스(셔틀버스) 정보를 제공하는 전용 함수입니다.

            ⚠️ 이 함수를 반드시 사용해야 하는 경우:
            - '통학버스', '셔틀버스', '스쿨버스' 관련 질문
            - '등교', '하교' 시간 문의
            - '원주역', '만종역', '청솔', '시외버스터미널' 등 원주 시내 출발지
            - '서울', '수원', '여주', '잠실', '강변', '노원' 등 시외 출발지
            - 버스 탑승 위치, 시간표, 노선, 예약 방법, 요금 질문

            ⚠️ 통학버스 관련 질문은 인터넷 검색이 아닌 이 함수만 사용하세요.

            지원 정보:
            - 시내버스: 만종역, 대명원, 시외버스터미널, 무실동, 원주역, 청솔아파트, 한국가스공사, 오성마을, 오페라웨딩홀
            - 시외버스: 서울(잠실,강변,상봉,천호,노원), 수원/여주(라마다호텔,아주대,영통,기흥,여주역)
            - 이용안내: 예약방법, 취소방법, 요금, 적립금""",
            "parameters": {
                "type": "object",
                "required": ["user_query"],
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": "사용자의 통학버스 관련 질문 원문. 예: '수원 하교시간', '원주역 등교 버스', '서울 통학버스 예약'"
                    }
                },
                "additionalProperties": False
            }
            },
            {
            "type": "function",
            "name": "get_department_phone_number",
            "description": """한라대학교 학과(단과대학) 사무실의 전화번호를 조회하는 전용 함수입니다.

            ⚠️ 이 함수를 반드시 사용해야 하는 경우:
            - 특정 학과/학부의 '전화번호', '연락처', '전화', '몇 번' 등을 묻는 질문
            - 학과 행정실/사무실 연락처 문의

            ⚠️ 학과 전화번호 관련 질문은 인터넷 검색이 아닌 이 함수만 사용하세요.""",
            "parameters": {
                "type": "object",
                "required": ["department_query"],
                "properties": {
                    "department_query": {
                        "type": "string",
                        "description": "사용자가 언급한 학과명 또는 질문 원문. 예: '컴퓨터공학과', '경영학과 전화번호'"
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
        
        logger.debug(f"공지 카테고리 분류기 원문: {raw}")
        # 정규화 및 선택
        text_norm = raw.replace(" ", "").replace("\n", "")
        for a in allowed:
            if a in text_norm:
                return a
        logger.debug(f"[_classify_notice_category_llm] ⚠️ No matching category found in response: {text_norm}")
        return None
    except Exception as e:
        logger.warning(f"[_classify_notice_category_llm] ❌ Error: {e}")
        logger.debug(f"[_classify_notice_category_llm] user_input: {user_input}")
        logger.debug(f"[_classify_notice_category_llm] context_info: {context_info}")
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
    logger.debug(f"[WEB][START] query='{user_input}' chat_ctx={'Y' if chat_context else 'N'}")
    try:
        # 대화 문맥 처리: 최근 2개만 사용
        if chat_context:
            logger.debug("[WEB] context available -> trimming recent messages")
            # system 역할 제외한 메시지만 필터링
            non_system_messages = [m for m in chat_context if m.get('role') != 'system']
            
            # 최근 2개만 선택
            recent_messages = non_system_messages[-2:] if len(non_system_messages) >= 2 else non_system_messages
            
            # 대화 문맥 구성
            if len(recent_messages) == 0:
                context_info = "최근 대화가 없습니다"
                logger.debug("[WEB] No recent conversation history")
            elif len(recent_messages) == 1:
                context_info = f"{recent_messages[0].get('role','unknown')}: {recent_messages[0].get('content','')}"
                logger.debug(f"[WEB] Using 1 recent message for context")
            else:  # len(recent_messages) == 2
                context_info = "\n".join([
                    f"{m.get('role','unknown')}: {m.get('content','')}" for m in recent_messages
                ])
                logger.debug(f"[WEB] Using 2 recent messages for context")
        else:
            recent_messages = []
            context_info = "최근 대화가 없습니다"
            logger.debug("[WEB] No chat_context provided")

        preferred = await _prefer_halla_site_query(user_input, context_info if context_info else None, token_counter)
        
        # 현재 날짜 정보 추가
        current_date = datetime.now()
        date_str = current_date.strftime("%Y년 %m월 %d일")
        year_str = current_date.strftime("%Y")
        
        # 공지사항 관련 검색인지 판단
        is_notice_query = any(keyword in user_input.lower() for keyword in ["공지", "notice", "알림", "announcement"])
        
        # LLM 에이전트로 검색어 재작성 (context_info 포함)
        rewrite_prompt = (
            f"[현재 날짜] {date_str} ({year_str}년)\n"
            f"[사용자 요청] {user_input}\n"
            f"[대화 문맥] {context_info or '없음'}\n\n"
            "**중요**: 검색 엔진에 직접 입력할 순수한 검색어만 출력하세요. 설명, 안내문, 추가 설명 절대 금지.\n\n"
            "검색어 작성 규칙:\n"
            "1. site:halla.ac.kr 필수 포함\n"
        )
        
        # 공지사항 검색이면 항상 현재 연도 포함
        if is_notice_query:
            rewrite_prompt += (
                f"2. 반드시 현재 연도({year_str}년) 포함\n"
                "3. 간결하고 핵심적인 검색어로만 구성 (한 줄)\n"
                "4. 출력 예시: 'site:halla.ac.kr 2025년 학사공지'\n"
            )
        else:
            rewrite_prompt += (
                f"2. '최신', '최근' 키워드 발견 시 현재 연도({year_str}년) 포함\n"
                "3. 간결하고 핵심적인 검색어로만 구성 (한 줄)\n"
                "4. 출력 예시: 'site:halla.ac.kr 키워드'\n"
            )
        
        # preferred가 있으면 추가 정보로 활용
        if preferred:
            rewrite_prompt += f"\n[추천 검색어] {preferred}\n위 검색어를 참고하되, 순수 검색어만 출력하세요.\n"
        
        rewrite_prompt += "\n**출력**: 검색어만 한 줄로 작성 (설명 금지)"
        
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
        logger.debug(f"[WEB] final_search_text='{search_text}'")
        logger.debug(f"[WEB][🔍 실제 검색어] '{search_text}'")
        logger.debug(f"[WEB][DEBUG] 이 검색어로 OpenAI web_search_preview API를 호출합니다")

        context_input = [{
            "role": "user",
            "content": [{"type": "input_text", "text": search_text}]
        }]
        
        logger.debug(f"[WEB][DEBUG] Request payload - model: {model.advanced}")
        logger.debug(f"[WEB][DEBUG] Request payload - search_text: '{search_text}'")
        logger.debug(f"[WEB][DEBUG] Request payload - tools: web_search_preview")

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
        logger.debug(f"[WEB] openai.responses.create elapsed={time.time()-call_ts:.2f}s total={time.time()-start_ts:.2f}s")
        logger.debug(f"[WEB][DEBUG] Response object type: {type(response)}")
        logger.debug(f"[WEB][DEBUG] Response has output: {hasattr(response, 'output')}")
        if hasattr(response, 'output'):
            logger.debug(f"[WEB][DEBUG] Output length: {len(response.output) if response.output else 0}")
            logger.debug(f"[WEB][DEBUG] Output types: {[getattr(item, 'type', 'unknown') for item in response.output] if response.output else []}")

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
                logger.debug(f"[TokenTrack][web_search] ✅ API usage tracked: input={input_tok}, output={output_tok}, reasoning={reasoning_tok}")
            else:
                logger.debug(f"[TokenTrack][web_search] ⚠️ No API usage available")

        did_call = any(getattr(item, "type", None) == "web_search_call" for item in getattr(response, "output", []))
        logger.debug(f"[WEB] search_call_performed={did_call}")
        
        # 📊 Output 아이템 상세 디버깅
        if hasattr(response, 'output') and response.output:
            logger.debug(f"[WEB][DEBUG] === Output Items Detail ===")
            for idx, item in enumerate(response.output):
                item_type = getattr(item, 'type', 'unknown')
                logger.debug(f"[WEB][DEBUG] Item[{idx}]: type={item_type}")
                if item_type == "web_search_call":
                    logger.debug(f"[WEB][DEBUG]   - web_search_call detected")
                elif item_type == "message":
                    content_count = len(getattr(item, 'content', [])) if hasattr(item, 'content') else 0
                    logger.debug(f"[WEB][DEBUG]   - message with {content_count} content blocks")

        message = next((item for item in response.output if getattr(item, "type", None) == "message"), None)
        logger.debug(f"[WEB][DEBUG] Message found: {message is not None}")
        if not message:
            logger.debug(f"[WEB][ERROR] ❌ No message in output")
            return "❌ GPT 응답 메시지를 찾을 수 없습니다."
        
        # Content blocks 디버깅
        content_blocks = getattr(message, 'content', [])
        logger.debug(f"[WEB][DEBUG] Content blocks count: {len(content_blocks)}")
        for idx, block in enumerate(content_blocks):
            block_type = getattr(block, 'type', 'unknown')
            logger.debug(f"[WEB][DEBUG] Content[{idx}]: type={block_type}")
        
        content_block = next((block for block in message.content if getattr(block, "type", None) == "output_text"), None)
        logger.debug(f"[WEB][DEBUG] Output_text block found: {content_block is not None}")
        if not content_block:
            logger.debug(f"[WEB][ERROR] ❌ No output_text in content blocks")
            return "❌ GPT 응답 내 output_text 항목을 찾을 수 없습니다."
        
        output_text = getattr(content_block, "text", "").strip()
        logger.debug(f"[WEB][DEBUG] Output text length: {len(output_text)}")
        logger.debug(f"[WEB][DEBUG] Output text preview: {output_text[:200] if output_text else '(empty)'}...")
        
        annotations = getattr(content_block, "annotations", [])
        logger.debug(f"[WEB][DEBUG] Annotations count: {len(annotations)}")
        logger.debug(f"[WEB][DEBUG] Annotations count: {len(annotations)}")
        
        citations = []
        for idx, a in enumerate(annotations):
            ann_type = getattr(a, "type", None)
            logger.debug(f"[WEB][DEBUG] Annotation[{idx}]: type={ann_type}")
            if ann_type == "url_citation":
                title = getattr(a, "title", "출처")
                url = getattr(a, "url", "")
                logger.debug(f"[WEB][DEBUG]   - Citation: title='{title}', url='{url}'")
                if url:
                    citations.append(f"[{title}]({url})")
        
        logger.debug(f"[WEB][DEBUG] Total citations extracted: {len(citations)}")
        
        result = output_text
        if citations:
            result += "\n\n📎 출처:\n" + "\n".join(citations)
            logger.debug(f"[WEB][DEBUG] Citations added to result")
        else:
            logger.debug(f"[WEB][DEBUG] ⚠️ No citations found")
        
        logger.debug(f"[WEB][DEBUG] Final result length: {len(result)}")
        logger.debug(f"[WEB][END] ✅ success total_elapsed={time.time()-start_ts:.2f}s")
        return result + "\n[WEB_METADATA]elapsed={:.2f}s did_call={}".format(time.time()-start_ts, did_call)
    except Exception as e:
        logger.debug(f"[WEB][ERROR] ❌ Exception occurred: {e} total_elapsed={time.time()-start_ts:.2f}s")
        logger.debug(f"[WEB][ERROR] user_input: {user_input}")
        logger.debug(f"[WEB][ERROR] chat_context: {chat_context is not None}")
        import traceback
        traceback.print_exc()
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
    if s in ("글피", "3 days later"):
        return today + timedelta(days=3)
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


async def get_halla_cafeteria_menu(date: Optional[str] = None, meal: Optional[str] = None, cafeteria_type: Optional[str] = None) -> str:
    """원주 한라대 식당(학생식당/교직원식당) 주간 식단 페이지를 파싱하여 특정 날짜/끼니 메뉴를 반환.

    Args:
        date: 조회할 날짜 ("오늘", "내일", "YYYY-MM-DD" 등)
        meal: 조회할 끼니 ("조식", "중식", "석식", None이면 전체)
        cafeteria_type: 식당 종류 ('학생' 또는 '교직원', 기본값: '학생')

    제한: 서버가 주차 변경을 JS/폼으로 처리하면 과거/미래 주 선택은 어려울 수 있음. 이 경우 현재 주만 반환.
    """
    # cafeteria_type 검증 및 기본값 설정
    if cafeteria_type is None or cafeteria_type not in ["학생", "교직원"]:
        cafeteria_type = "학생"
    
    t0 = time.time()
    logger.debug(f"[CAF][START] date={date} meal={meal} cafeteria_type={cafeteria_type}")
    try:
        target_date = _parse_date_input(date)
    except Exception as e:
        logger.debug(f"[CAF][ERROR] ❌ date-parse exception: {e}")
        logger.debug(f"[CAF][ERROR] date input value: {date}")
        import traceback
        traceback.print_exc()
        return f"❌ 날짜 해석 실패: {e}"

    # URL 분기: 교직원식당은 /kr/212/, 학생식당은 /kr/211/
    if cafeteria_type == "교직원":
        url = "https://www.halla.ac.kr/kr/212/subview.do"
    else:
        url = "https://www.halla.ac.kr/kr/211/subview.do"
    try:
        net_t = time.time()

        # User-Agent 헤더 추가 (봇 차단 방지)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=headers, timeout=60.0)
            resp.raise_for_status()
            html_content = resp.text

        # 에러 HTML 감지 (403 Forbidden 등)
        if "403 Forbidden" in html_content or "<title>403" in html_content:
            logger.debug(f"[CAF][ERROR] 403 Forbidden detected in response body")
            return f"❌ 페이지 접근이 차단되었습니다. 잠시 후 다시 시도해주세요."

        logger.debug(f"[CAF] fetch ok elapsed={time.time()-net_t:.2f}s status={resp.status_code}")
    except Exception as e:
        logger.debug(f"[CAF][ERROR] ❌ fetch exception: {e}")
        logger.debug(f"[CAF][ERROR] url: {url}")
        logger.debug(f"[CAF][ERROR] cafeteria_type: {cafeteria_type}")
        import traceback
        traceback.print_exc()
        return f"❌ 페이지 요청 실패: {e}"

    soup = BeautifulSoup(html_content, "html.parser")

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
    logger.debug(f"[CAF] primary-parse elapsed={time.time()-parse_t:.2f}s result={found}")

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
    cafeteria_label = "교직원식당" if cafeteria_type == "교직원" else "학생식당"
    header = f"한라대 {cafeteria_label} 식단 ({target_date} {day_label})"

    if meal in ("조식", "중식", "석식"):
        val = found.get(meal)
        if not val:
            out = header + f"\n[{meal}] 정보 없음\n추가 사항: 원문: {url}"
            logger.debug(f"[CAF][END] elapsed={time.time()-t0:.2f}s meal-miss")
            return out
        out = header + f"\n[{meal}] {val}\n추가 사항: 원문: {url}"
        logger.debug(f"[CAF][END] elapsed={time.time()-t0:.2f}s meal-hit")
        return out

    # 3끼 모두 반환
    lines_out = []
    for k in ["조식", "중식", "석식"]:
        v = found.get(k)
        lines_out.append(f"[{k}] {v if v else '정보 없음'}")
    out = header + "\n" + "\n".join(lines_out) + f"\n추가 사항: 원문: {url}"
    logger.debug(f"[CAF][END] elapsed={time.time()-t0:.2f}s all-meals")
    return out


def _parse_month_input(month_text: Optional[str]) -> tuple:
    """월 입력을 파싱하여 (년, 월) 튜플 반환

    Args:
        month_text: 월 입력 ("이번달", "다음달", "2025-03", "3월" 등)

    Returns:
        (year, month) 튜플
    """
    today = datetime.now().date()

    if not month_text:
        return (today.year, today.month)

    s = str(month_text).strip()

    # 상대 월 지원
    if s in ("이번달", "이번 달", "현재", "this month"):
        return (today.year, today.month)
    if s in ("다음달", "다음 달", "next month"):
        next_month = today.replace(day=1) + timedelta(days=32)
        return (next_month.year, next_month.month)
    if s in ("지난달", "지난 달", "last month"):
        prev_month = today.replace(day=1) - timedelta(days=1)
        return (prev_month.year, prev_month.month)

    # YYYY-MM 형식
    if re.match(r"^\d{4}-\d{1,2}$", s):
        parts = s.split("-")
        return (int(parts[0]), int(parts[1]))

    # YYYY년 MM월 형식
    m = re.search(r"(\d{4})년\s*(\d{1,2})월", s)
    if m:
        return (int(m.group(1)), int(m.group(2)))

    # MM월 형식 (올해)
    m = re.search(r"(\d{1,2})월", s)
    if m:
        return (today.year, int(m.group(1)))

    # 숫자만 (1~12: 월, 그 외: 현재 월)
    if s.isdigit():
        num = int(s)
        if 1 <= num <= 12:
            return (today.year, num)

    # 파싱 실패 시 현재 월
    return (today.year, today.month)


async def get_halla_academic_calendar(month: Optional[str] = None) -> str:
    """한라대학교 학사일정 조회

    Args:
        month: 조회할 월 ("이번달", "다음달", "2025-03", "3월" 등)

    Returns:
        학사일정 정보 문자열
    """
    t0 = time.time()
    logger.debug(f"[CALENDAR][START] month={month}")

    try:
        year, month_num = _parse_month_input(month)
    except Exception as e:
        logger.debug(f"[CALENDAR][ERROR] ❌ month-parse exception: {e}")
        logger.debug(f"[CALENDAR][ERROR] month input value: {month}")
        import traceback
        traceback.print_exc()
        return f"❌ 월 해석 실패: {e}"

    url = "https://www.halla.ac.kr/kr/100/subview.do"

    try:
        net_t = time.time()
        # 특정 년월 조회 시도 (파라미터 전달)
        params = {"year": str(year), "month": str(month_num)}

        # User-Agent 헤더 추가 (봇 차단 방지)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers, timeout=60.0)
            resp.raise_for_status()
            html_content = resp.text

        # 에러 HTML 감지 (403 Forbidden 등)
        if "403 Forbidden" in html_content or "<title>403" in html_content:
            logger.debug(f"[CALENDAR][ERROR] 403 Forbidden detected in response body")
            return f"❌ 페이지 접근이 차단되었습니다. 잠시 후 다시 시도해주세요."

        logger.debug(f"[CALENDAR] fetch ok elapsed={time.time()-net_t:.2f}s status={resp.status_code}")
    except Exception as e:
        logger.debug(f"[CALENDAR][ERROR] ❌ fetch exception: {e}")
        logger.debug(f"[CALENDAR][ERROR] url: {url}")
        logger.debug(f"[CALENDAR][ERROR] params: {params}")
        import traceback
        traceback.print_exc()
        return f"❌ 페이지 요청 실패: {e}"

    soup = BeautifulSoup(html_content, "html.parser")

    schedules = []

    # 방법 1: ul 태그에서 li 항목 찾기
    ul_tags = soup.find_all("ul")
    for ul in ul_tags:
        li_items = ul.find_all("li")
        for li in li_items:
            text = li.get_text("\n", strip=True)
            # "MM.DD" 패턴이 포함된 li만 처리
            if re.search(r"\d{1,2}\.\d{1,2}", text):
                # 줄바꿈을 공백으로 변경하고 정리
                cleaned = " ".join(text.split())
                if len(cleaned) > 5:  # 의미있는 텍스트만
                    schedules.append(cleaned)

    # 방법 2: ul에서 못 찾았으면, 전체 텍스트에서 패턴 매칭
    if not schedules:
        text = soup.get_text("\n", strip=False)
        lines = text.split("\n")

        # "MM.DD" 패턴으로 시작하는 라인 찾기
        schedule_pattern = re.compile(r"(\d{1,2}\.\d{1,2})")

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            match = schedule_pattern.match(line)

            if match:
                # 날짜 라인 발견
                date_str = match.group(1)

                # 다음 라인이 일정 내용일 가능성
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()

                    # 범위 날짜 체크 (예: "11.24 - 11.25")
                    if next_line.startswith("-") and i + 2 < len(lines):
                        # "- 11.25" 형태
                        range_match = re.match(r"-\s*(\d{1,2}\.\d{1,2})", next_line)
                        if range_match:
                            end_date = range_match.group(1)
                            date_str = f"{date_str} - {end_date}"
                            i += 1  # 다음 라인 건너뛰기

                            # 그 다음 라인이 일정 내용
                            if i + 1 < len(lines):
                                next_line = lines[i + 1].strip()

                    # 일정 내용인지 확인 (날짜 패턴이 아니고, 의미있는 텍스트)
                    if next_line and not schedule_pattern.match(next_line) and len(next_line) > 1:
                        schedules.append(f"{date_str}: {next_line}")
                        i += 1  # 다음 라인 건너뛰기

            i += 1

    # 결과 구성
    header = f"한라대 학사일정 ({year}년 {month_num}월)"

    if not schedules:
        out = header + f"\n등록된 일정이 없습니다.\n원문: {url}"
        logger.debug(f"[CALENDAR][END] elapsed={time.time()-t0:.2f}s no-schedule")
        return out

    out = header + "\n" + "\n".join(schedules) + f"\n\n원문: {url}"
    logger.debug(f"[CALENDAR][END] elapsed={time.time()-t0:.2f}s schedules={len(schedules)}")
    return out


# 통학버스 서비스 싱글톤 인스턴스
_shuttle_bus_service = None

def _get_shuttle_bus_service():
    """ShuttleBusService 싱글톤 인스턴스 반환"""
    global _shuttle_bus_service
    if _shuttle_bus_service is None:
        _shuttle_bus_service = ShuttleBusService()
    return _shuttle_bus_service


async def get_shuttle_bus_info(user_query: str, chat_context=None, token_counter=None) -> str:
    """한라대학교 통학버스 정보 제공

    Args:
        user_query: 사용자의 통학버스 관련 질문
        chat_context: 대화 문맥 (최근 메시지 리스트)
        token_counter: 토큰 카운터

    Returns:
        통학버스 정보 응답 문자열
    """
    start_ts = time.time()
    logger.debug(f"[SHUTTLE][START] query='{user_query}' chat_ctx={'Y' if chat_context else 'N'}")

    try:
        # 대화 문맥 추출
        if chat_context:
            recent_messages = chat_context[-4:]
            context_info = "\n".join([
                f"{m.get('role','unknown')}: {m.get('content','')}"
                for m in recent_messages if m.get('role') != 'system'
            ])
        else:
            context_info = ""

        # ShuttleBusService 인스턴스 가져오기
        service = _get_shuttle_bus_service()

        # 1단계: 카테고리 분류
        category = await service.classify_category(
            user_input=user_query,
            context_info=context_info,
            token_counter=token_counter
        )

        logger.debug(f"[SHUTTLE] category={category}")

        # 통학버스 관련 질문이 아닌 경우
        if category == "not_shuttle_bus":
            elapsed = time.time() - start_ts
            logger.debug(f"[SHUTTLE][END] elapsed={elapsed:.2f}s result=not_shuttle_bus")
            return "통학버스와 관련 없는 질문입니다. 시내버스, 시외버스 시간표, 예약 방법 등에 대해 질문해주세요."

        # 2단계: 카테고리별 정보 추출
        shuttle_info = service.get_info_by_category(category, user_query)
        logger.debug(f"[SHUTTLE] info extracted len={len(shuttle_info)}")

        # 3단계: 응답 생성
        response = await service.generate_response(
            user_input=user_query,
            shuttle_info=shuttle_info,
            token_counter=token_counter
        )

        elapsed = time.time() - start_ts
        logger.debug(f"[SHUTTLE][END] elapsed={elapsed:.2f}s response_len={len(response)}")

        return response

    except Exception as e:
        elapsed = time.time() - start_ts
        logger.debug(f"[SHUTTLE][ERROR] elapsed={elapsed:.2f}s error={e}")
        import traceback
        traceback.print_exc()
        return f"❌ 통학버스 정보 조회 중 오류가 발생했습니다: {str(e)}"


_department_phone_data: Optional[str] = None


def _load_department_phone_data() -> str:
    """department_phone_numbers.md 파일을 캐싱하여 로드"""
    global _department_phone_data
    if _department_phone_data is None:
        path = Path(__file__).parent / "department_phone_numbers.md"
        with open(path, "r", encoding="utf-8") as f:
            _department_phone_data = f.read()
    return _department_phone_data


def get_department_phone_number(department_query: str) -> str:
    """한라대학교 학과별 전화번호 조회

    department_phone_numbers.md의 표를 파싱하여 질문에 포함된 학과명과
    일치(부분 포함)하는 행을 찾아 반환합니다.

    Args:
        department_query: 사용자가 언급한 학과명 또는 질문 원문

    Returns:
        학과 전화번호 정보 문자열
    """
    logger.debug(f"[DEPT_PHONE][START] query='{department_query}'")
    try:
        content = _load_department_phone_data()
    except Exception as e:
        logger.debug(f"[DEPT_PHONE][ERROR] ❌ 파일 로드 실패: {e}")
        return f"❌ 학과 전화번호 데이터를 불러오지 못했습니다: {e}"

    query = re.sub(r"\s+", "", department_query)
    matches = []

    for line in content.splitlines():
        line = line.strip()
        if not line.startswith("|") or not line.endswith("|"):
            continue
        # 헤더 구분선(|---|---|) 스킵
        if set(line.replace("|", "").strip()) <= {"-"}:
            continue

        cols = [c.strip() for c in line.strip("|").split("|")]
        if len(cols) < 2:
            continue

        dept_col, phone_col = cols[0], cols[1]
        dept_col_normalized = re.sub(r"\s+", "", dept_col)

        if dept_col_normalized in ("학과", ""):
            continue

        if query and (query in dept_col_normalized or dept_col_normalized in query):
            matches.append(f"{dept_col}: {phone_col}")

    if matches:
        result = "(지역번호 033 공통 / 대표전화 033-760-1114)\n" + "\n".join(matches)
        logger.debug(f"[DEPT_PHONE][END] matches={len(matches)}")
        return result

    logger.debug(f"[DEPT_PHONE][END] no match found for query='{department_query}'")
    return "일치하는 학과를 찾지 못했습니다. 학과명을 다시 확인해주세요.\n\n" + content


class FunctionCalling:
    def __init__(self, model, available_functions=None, token_counter=None):
        self.model = model
        self.token_counter = token_counter
        default_functions = {
            "search_internet": search_internet,
            "get_halla_cafeteria_menu": get_halla_cafeteria_menu,
            "get_halla_academic_calendar": get_halla_academic_calendar,
            "get_shuttle_bus_info": get_shuttle_bus_info,
            "get_department_phone_number": get_department_phone_number,
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
            logger.debug(f"[ANALYZER][analyze] ❌ Reasoning generation failed: {e}")
            logger.debug(f"[ANALYZER][analyze] user_message: {user_message}")
            import traceback
            traceback.print_exc()
            reasoning = f"추론 생성 실패 ({e})"
            selected_tools = []  # exception 발생 시 기본값 설정

        # 2단계: 기존 함수 호출 분석 (OpenAI API)

        # 현재 날짜 정보 생성
        current_date = datetime.now()
        date_info = current_date.strftime("%Y년 %m월 %d일 (%A)")
        weekday_map = {
            "Monday": "월요일", "Tuesday": "화요일", "Wednesday": "수요일",
            "Thursday": "목요일", "Friday": "금요일", "Saturday": "토요일", "Sunday": "일요일"
        }
        weekday_kr = weekday_map.get(current_date.strftime("%A"), "")
        date_info = current_date.strftime(f"%Y년 %m월 %d일 ({weekday_kr})")

        structured_input = [
            {
                "role": "system",
                "content": f"""현재 날짜: {date_info}

[필수 규칙]
모든 날짜를 반드시 YYYY-MM-DD 형식으로 계산하여 출력하세요.
- 오늘 → {current_date.strftime("%Y-%m-%d")}
- 내일 → 오늘+1일 계산
- 모레 → 오늘+2일 계산
- 글피/그을피 → 오늘+3일 계산
- 그글피 → 오늘+4일 계산
- "N일 후" → 오늘+N일 계산
- "다음주 월요일" → 해당 날짜 계산
- 날짜 미언급 → 오늘 날짜 출력

사용자가 오타(야모레, 그을피 등)를 쓰더라도 의도를 파악하여 YYYY-MM-DD로 변환."""
            },
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
            logger.debug(f"[ANALYZER][analyze] ❌ OpenAI API call failed: {e}")
            logger.debug(f"[ANALYZER][analyze] user_message: {user_message}")
            logger.debug(f"[ANALYZER][analyze] model: {model.o3_mini}")
            import traceback
            traceback.print_exc()
            return {
                "reasoning": reasoning,
                "selected_tools": selected_tools,
                "output": []
            }
    

###   레거시 def run(self, analyzed,context):
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
                logger.warning("Error occurred(run):",e)
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
    ###
   
    def call_function(self, analyzed_dict):        
        func_name = analyzed_dict["function_call"]["name"]
        func_to_call = self.available_functions[func_name]                
        try:            
            func_args = json.loads(analyzed_dict["function_call"]["arguments"])
            func_response = func_to_call(**func_args)
            return str(func_response)
        except Exception as e:
            logger.warning("Error occurred(call_function):",e)
            return makeup_response("[call_function 오류입니다]")
    