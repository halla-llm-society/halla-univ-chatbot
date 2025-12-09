"""
함수 호출을 위한 프롬프트 모음
각 함수의 description과 parameters 설명을 중앙 관리합니다.
"""

# 인터넷 검색 함수
SEARCH_INTERNET_DESCRIPTION = """인터넷에서 최신 정보를 검색하는 함수입니다.

⚠️ 이 함수를 사용해야 하는 경우:
- 최신 공지사항, 뉴스, 이벤트 정보
- 한라대학교 웹사이트의 최신 정보
- 일반적인 웹 검색이 필요한 경우

❌ 이 함수를 사용하지 말아야 하는 경우:
- 통학버스, 셔틀버스 관련 질문 → get_shuttle_bus_info 사용
- 학식, 식단 관련 질문 → get_halla_cafeteria_menu 사용
- 학사규정 관련 질문 → RAG 시스템 사용 (자동 처리)

통학버스 시간표, 탑승 위치, 예약 방법 등은 반드시 get_shuttle_bus_info 함수를 사용하세요."""

SEARCH_INTERNET_USER_INPUT = "User's search query input(conversation context will be automatically added)"

# 학식 메뉴 조회 함수
CAFETERIA_DESCRIPTION = "원주 한라대학교 학생식당과 교직원식당의 메뉴를 조회합니다. 주간 식단 페이지에서 특정 날짜/끼니의 메뉴를 추출합니다. 학생식당(/kr/211/)과 교직원식당(/kr/212/) 모두 지원합니다."

CAFETERIA_DATE_DESCRIPTION = """조회할 날짜를 정규화하여 전달합니다.
허용 형식:
- 상대 날짜: "오늘", "내일", "모레", "어제"
- 절대 날짜: YYYY-MM-DD 형식 (예: "2025-11-18")
- 오타 처리: "야모레" → "모레"로 자동 변환
- 자연어: "이틀 후" → "모레", "다음주 월요일" → 날짜 계산
기본값: "오늘" """

CAFETERIA_MEAL_DESCRIPTION = "조회할 끼니. 지정하지 않으면 전체 끼니를 보여줍니다."

CAFETERIA_TYPE_DESCRIPTION = "식당 종류. '학생' 또는 '교직원'. 기본값은 '학생'입니다. 사용자가 '교직원', '교수', '직원' 등의 키워드를 언급하면 '교직원'을 선택하세요."

# 학사일정 조회 함수
ACADEMIC_CALENDAR_DESCRIPTION = "한라대학교 학사일정을 조회합니다. 특정 월의 학사 일정(개강, 종강, 시험, 방학 등)을 제공합니다."

ACADEMIC_CALENDAR_MONTH_DESCRIPTION = """조회할 월을 지정합니다.
허용 형식:
- 상대 월: "이번달", "다음달", "지난달"
- 절대 월: "3월", "12월" (올해 기준)
- YYYY-MM 형식: "2025-03"
- YYYY년 MM월: "2025년 3월"
- 숫자: "3", "12" (1~12는 월로 해석)
기본값: 현재 월"""

# 통학버스 정보 함수
SHUTTLE_BUS_DESCRIPTION = """한라대학교 통학버스(셔틀버스) 정보를 제공하는 전용 함수입니다.

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
- 이용안내: 예약방법, 취소방법, 요금, 적립금"""

SHUTTLE_BUS_QUERY_DESCRIPTION = "사용자의 통학버스 관련 질문 원문. 예: '수원 하교시간', '원주역 등교 버스', '서울 통학버스 예약'"

# 함수 정의 리스트 (analyzer.py에서 사용)
def get_function_definitions():
    """함수 정의를 반환합니다."""
    return [
        {
            "type": "function",
            "name": "search_internet",
            "description": SEARCH_INTERNET_DESCRIPTION,
            "parameters": {
                "type": "object",
                "required": ["user_input"],
                "properties": {
                    "user_input": {
                        "type": "string",
                        "description": SEARCH_INTERNET_USER_INPUT
                    }
                },
                "additionalProperties": False
            }
        },
        {
            "type": "function",
            "name": "get_halla_cafeteria_menu",
            "description": CAFETERIA_DESCRIPTION,
            "parameters": {
                "type": "object",
                "required": ["date"],
                "properties": {
                    "date": {
                        "type": "string",
                        "description": CAFETERIA_DATE_DESCRIPTION,
                    },
                    "meal": {
                        "type": "string",
                        "enum": ["조식", "중식", "석식"],
                        "description": CAFETERIA_MEAL_DESCRIPTION,
                    },
                    "cafeteria_type": {
                        "type": "string",
                        "enum": ["학생", "교직원"],
                        "description": CAFETERIA_TYPE_DESCRIPTION,
                    }
                },
                "additionalProperties": False
            }
        },
        {
            "type": "function",
            "name": "get_halla_academic_calendar",
            "description": ACADEMIC_CALENDAR_DESCRIPTION,
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {
                    "month": {
                        "type": "string",
                        "description": ACADEMIC_CALENDAR_MONTH_DESCRIPTION,
                    }
                },
                "additionalProperties": False
            }
        },
        {
            "type": "function",
            "name": "get_shuttle_bus_info",
            "description": SHUTTLE_BUS_DESCRIPTION,
            "parameters": {
                "type": "object",
                "required": ["user_query"],
                "properties": {
                    "user_query": {
                        "type": "string",
                        "description": SHUTTLE_BUS_QUERY_DESCRIPTION
                    }
                },
                "additionalProperties": False
            }
        }
    ]
