"""
통학버스 정보 제공 서비스

카테고리별로 필요한 정보만 추출하여 제공하는 서비스 클래스
"""

import yaml
from pathlib import Path
from typing import Dict, Optional, List

# LLM Manager import
try:
    from app.ai.llm import get_provider
except ImportError:
    from ..llm import get_provider


class ShuttleBusService:
    """통학버스 정보 조회 및 응답 생성 서비스"""

    def __init__(self):
        self.prompts = self._load_prompts()
        self.schedule_data = self._load_schedule_data()

    def _load_prompts(self) -> Dict:
        """프롬프트 YAML 파일 로드"""
        prompt_path = Path(__file__).parent / "shuttle_bus_prompts.yaml"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _load_schedule_data(self) -> Dict:
        """통학버스 스케줄 데이터를 딕셔너리로 구조화"""
        return {
            "city_bus_go": {
                "route_1": {
                    "name": "시내버스 등교 1노선",
                    "route": "만종역 → 대명원 → 시외버스터미널 → 무실동 SK주유소 앞 → 원주역 → 학교",
                    "stops": [
                        {"name": "만종역", "times": ["08:20"], "location": "만종역 역사 앞 버스정류장. 주변: 통일화원 꽃농장, 영진건재철물, GS칼텍스 주유소"},
                        {"name": "대명원", "times": ["08:24"], "location": "대명원 버스정류장. GS칼텍스 주유소 건너편 도로"},
                        {"name": "시외버스터미널", "times": ["08:35", "09:45"], "location": "남원주 토종순대 건물 앞, 지하주차장 입구 옆 인도. 주변: 그랜드 치과병원"},
                        {"name": "무실동 SK주유소 앞", "times": ["08:38", "09:48"], "location": "제일주유소(SK주유소) 앞 도로변. 주변: 다이소 원주무실점, 원주중부교회, 롯데시네마 원주무실"},
                        {"name": "원주역", "times": ["08:45", "09:55", "10:25"], "location": "원주역 역사 정문 앞 버스정류장, 역 광장 및 육교 근처"}
                    ]
                },
                "route_2": {
                    "name": "시내버스 등교 2노선",
                    "route": "청솔 8차아파트 → 청솔 5차아파트 → 한국가스공사 → 오성마을입구 → 오페라 웨딩홀 → 원주역 → 학교",
                    "stops": [
                        {"name": "청솔 8차아파트", "times": ["08:15", "09:15"], "location": "청솔6.8차아파트 버스정류장. 주변: 홈플러스"},
                        {"name": "청솔 5차아파트", "times": ["08:16", "09:16"], "location": "청솔5차아파트 버스정류장. 주변: 미래교회"},
                        {"name": "한국가스공사", "times": ["08:18", "09:18"], "location": "한국가스공사 정문 기준 오른쪽에서 앞쪽 방향. 갈색 건물 쪽으로 이동. ※정류장이 아닌 지정 탑승 위치"},
                        {"name": "오성마을입구", "times": ["08:19", "09:19"], "location": "오성마을 버스정류장. 주변: 세경웰러스 아파트"},
                        {"name": "오페라 웨딩홀", "times": ["08:24", "09:24"], "location": "오페라웨딩홀 버스정류장. 오페라웨딩컨벤션 앞 도로변"},
                        {"name": "원주역", "times": ["08:30", "09:30"], "location": "원주역 역사 정문 앞 버스정류장 (1노선과 동일)"}
                    ]
                }
            },
            "city_bus_return": {
                "name": "시내버스 하교",
                "route": "학교 → 원주역 → 무실동 → 이화마을입구 → 시외버스터미널",
                "schedule": [
                    {"departure": "14:20", "wonju_station": "14:27", "musil": "14:34", "ihwa": "14:37", "terminal": "14:40"},
                    {"departure": "15:10", "wonju_station": "15:17", "musil": "15:24", "ihwa": "15:27", "terminal": "15:30"},
                    {"departure": "16:20", "wonju_station": "16:27", "musil": "16:34", "ihwa": "16:37", "terminal": "16:40"},
                    {"departure": "17:20", "wonju_station": "17:27", "musil": "17:34", "ihwa": "17:37", "terminal": "17:40"},
                    {"departure": "18:20", "wonju_station": "18:27", "musil": "18:34", "ihwa": "18:37", "terminal": "18:40"}
                ],
                "stops_info": "원주역(등교 노선과 동일), 무실동(등교 1노선의 무실동 SK주유소 앞과 인근), 이화마을입구, 시외버스터미널(등교 1노선과 인근)"
            },
            "intercity_bus_go": {
                "seoul": {
                    "name": "서울지역 시외버스 등교",
                    "routes": [
                        {"name": "잠실종합운동장", "departure": "07:00", "via": "천호역 07:20", "location": "잠실 종합운동장 전철역 2번 출구"},
                        {"name": "강변역", "departure": "07:10", "via": "상일동 07:25", "location": "강변역 테크노마트 정문 앞 택시 승강장 부근"},
                        {"name": "상봉터미널", "departure": "07:10", "via": "구리 07:25", "location": "상봉터미널 건너편 이마트 앞"},
                        {"name": "천호역", "departure": "07:20", "via": "상일동 07:25", "location": "천호역 10번출구, 풍납토성 앞 버스정류장"},
                        {"name": "노원역", "departure": "06:50", "via": "하계역 07:00", "location": "노원역 7호선 4번 출구 롯데백화점 측편"}
                    ],
                    "important": "⚠️ 시외버스는 통학버스예매시스템 (halla.beplanbus.com)에서 선예약 필수"
                },
                "suwon_yeoju": {
                    "name": "수원/여주지역 시외버스 등교",
                    "departure": "라마다호텔 06:50",
                    "stops": [
                        {"name": "라마다호텔", "time": "06:50", "location": "동수원 라마다호텔 앞"},
                        {"name": "아주대삼거리", "time": "06:55", "location": "수원매탄1동 우체국 옆 씽크대 공장 앞 (HOLLYS COFFEE SHOP 앞)"},
                        {"name": "영통지구", "time": "07:05", "location": "황곡초교 부근 고가 밑 신명 아파트 뒤 버스정류장"},
                        {"name": "기흥역", "time": "07:20", "location": "기흥역 5번출구 앞"},
                        {"name": "여주전철역", "time": "08:20", "location": "여주역 전철역 입구 도로, 대로변 횡단보도 앞"}
                    ],
                    "important": "⚠️ 시외버스는 통학버스예매시스템 (halla.beplanbus.com)에서 선예약 필수. 예약 인원에 따라 미운행될 수 있음"
                }
            },
            "intercity_bus_return": {
                "seoul": {
                    "name": "서울지역 시외버스 하교",
                    "departure": "학교 15:30",
                    "route": "구리·상봉 17:20 → 강변 17:30 (월~목만 운행) → 구리·상봉·하계·노원 18:30 → 강변",
                    "important": "⚠️ 강변 노선은 월~목요일만 17:20에 운행. 금요일은 18:30에만 운행"
                },
                "suwon_yeoju": {
                    "name": "수원/여주지역 시외버스 하교",
                    "departure": "학교 18:10",
                    "route": "여주역 → 기흥역 → 영통지구 → 아주대삼거리 → 동수원사거리 → 라마다호텔",
                    "important": "⚠️ 예약 인원에 따라 미운행될 수 있음"
                }
            },
            "usage_guide": {
                "reservation": {
                    "title": "예약 방법",
                    "content": """
**1단계: 회원 가입 (필수)**
- 학번, 성명, 휴대폰 번호 인증 후 가입
- 신입생 학번: 생년월일 + 이니셜

**2단계: 통학권 구매**
- 사이트: halla.beplanbus.com
- 예약 가능 기간: 이용일 최대 15일 전부터
- 등교: 전일 17시 마감
- 하교: 출발 전까지

**3단계: QR 바코드 탑승**
- 카카오알림 링크에서 "통학증 보기"로 QR바코드 인증
"""
                },
                "cancellation": {
                    "title": "취소 및 변경",
                    "content": """
**취소 가능 시간**
- 등교 버스: 탑승 전일 17시까지
- 하교 버스: 버스 출발 2시간 전까지
- 취소는 적립금으로만 진행

**노선/탑승일 변경**
- 변경 가능 시간: 취소와 동일
- 이용일 기준 1일 1회만 가능
- 요금 차액은 적립금으로 반영
"""
                },
                "pricing": {
                    "title": "요금 안내",
                    "content": """
**시외버스 요금**
- 서울/수원: 편도 8,500원 / 왕복 17,000원 / 현금 9,000원
- 여주: 편도 4,600원 / 왕복 9,200원 / 현금 5,000원

**주의사항**
- 현금 승차는 자리 여유가 있을 때만 가능
- 신용카드/페이 결제 불가 (현금만)
- 차량별 예약자 5인 미만 시 미운행 가능
"""
                },
                "points": {
                    "title": "적립금 안내",
                    "content": """
**적립**
- 예약 취소 시 적립금으로 전환

**사용**
- 예약 결제 시 사용 가능
- 적립금이 승차권보다 크면 전액 사용 가능
- 적립금이 적으면 최소 1,000원 카드 결제 후 사용

**환불**
- 미사용 적립금은 학기 종료 후 자동 소멸
- 자퇴/휴학/군입대 시 증빙서류로 환불 가능 (7일 소요, 수수료 3.68%)
"""
                },
                "faq": {
                    "title": "자주 묻는 질문",
                    "content": """
**Q1. 휴대폰 인증이 안돼요**
- 전화번호 확인 및 스팸 보관함 확인

**Q2. 결제 진행이 안돼요**
- 팝업 차단 해제 확인

**Q3. 본인 명의 카드만 되나요?**
- 가족 명의 카드 가능 (단, 법인 카드 불가)

**Q4. 아이폰에서 결제 인증 후 진행 안됨**
- 다른 브라우저(크롬/사파리)에서 진행

**Q5. 예약이 안돼요**
- 인원 조기 마감 또는 노선 미운행 가능성
"""
                }
            }
        }

    async def classify_category(self, user_input: str, context_info: str = "", token_counter=None) -> str:
        """사용자 질문의 카테고리 분류"""
        try:
            prompt_config = self.prompts["category_classifier"]
            prompt = prompt_config["user_prompt_template"].format(
                user_input=user_input,
                context_info=context_info or "(없음)"
            )

            provider = get_provider("category")
            messages = [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
            raw, usage = await provider.simple_completion(messages)
            raw = raw.strip()

            # API usage 기반 토큰 계산
            if token_counter and usage:
                token_counter.update_from_api_usage(
                    usage=usage,
                    role="category",
                    model=provider.get_model_name(),
                    category="function"
                )

            print(f"[ShuttleBus] 카테고리 분류 결과: {raw}")

            # 정규화 및 선택 (긴 문자열부터 체크하여 부분 매칭 문제 방지)
            allowed = [
                "intercity_bus_go", "intercity_bus_return",  # 긴 것 먼저
                "city_bus_go", "city_bus_return",
                "usage_guide", "not_shuttle_bus"
            ]

            # 정확한 매칭 우선
            raw_normalized = raw.strip().lower()
            for cat in allowed:
                if cat == raw_normalized:
                    return cat

            # 부분 매칭 (긴 것부터)
            for cat in allowed:
                if cat in raw_normalized:
                    return cat

            return "not_shuttle_bus"

        except Exception as e:
            print(f"[ShuttleBus] 카테고리 분류 오류: {e}")
            return "not_shuttle_bus"

    def get_info_by_category(self, category: str, user_input: str = "") -> str:
        """카테고리별 필요한 정보만 추출"""

        if category == "not_shuttle_bus":
            return "통학버스와 관련 없는 질문입니다."

        data = self.schedule_data.get(category, {})

        # 시내버스 등교
        if category == "city_bus_go":
            # 특정 정류장 언급 확인
            user_lower = user_input.lower()

            # 1노선 키워드
            route1_keywords = ["만종", "대명원", "무실", "시외버스터미널"]
            # 2노선 키워드
            route2_keywords = ["청솔", "한국가스공사", "오성", "오페라"]

            if any(k in user_input for k in route1_keywords):
                return self._format_city_bus_go_route(data["route_1"])
            elif any(k in user_input for k in route2_keywords):
                return self._format_city_bus_go_route(data["route_2"])
            else:
                # 둘 다 제공
                return (
                    self._format_city_bus_go_route(data["route_1"]) +
                    "\n\n" +
                    self._format_city_bus_go_route(data["route_2"])
                )

        # 시내버스 하교
        elif category == "city_bus_return":
            return self._format_city_bus_return(data)

        # 시외버스 등교
        elif category == "intercity_bus_go":
            user_lower = user_input.lower()
            seoul_keywords = ["서울", "잠실", "강변", "상봉", "천호", "노원", "하계", "구리", "상일"]
            suwon_keywords = ["수원", "여주", "라마다", "아주대", "영통", "기흥"]

            if any(k in user_input for k in seoul_keywords):
                return self._format_intercity_go_seoul(data["seoul"])
            elif any(k in user_input for k in suwon_keywords):
                return self._format_intercity_go_suwon_yeoju(data["suwon_yeoju"])
            else:
                # 둘 다 제공
                return (
                    self._format_intercity_go_seoul(data["seoul"]) +
                    "\n\n" +
                    self._format_intercity_go_suwon_yeoju(data["suwon_yeoju"])
                )

        # 시외버스 하교
        elif category == "intercity_bus_return":
            user_lower = user_input.lower()
            seoul_keywords = ["서울", "잠실", "강변", "상봉", "천호", "노원", "하계", "구리"]
            suwon_keywords = ["수원", "여주", "라마다", "아주대", "영통", "기흥"]

            if any(k in user_input for k in seoul_keywords):
                return self._format_intercity_return(data["seoul"])
            elif any(k in user_input for k in suwon_keywords):
                return self._format_intercity_return(data["suwon_yeoju"])
            else:
                return (
                    self._format_intercity_return(data["seoul"]) +
                    "\n\n" +
                    self._format_intercity_return(data["suwon_yeoju"])
                )

        # 이용안내
        elif category == "usage_guide":
            # 세부 카테고리 판단
            user_lower = user_input.lower()

            if "예약" in user_input or "신청" in user_input:
                return data["reservation"]["content"]
            elif "취소" in user_input or "변경" in user_input:
                return data["cancellation"]["content"]
            elif "요금" in user_input or "얼마" in user_input or "가격" in user_input:
                return data["pricing"]["content"]
            elif "적립금" in user_input or "환불" in user_input:
                return data["points"]["content"]
            elif "?" in user_input or "질문" in user_input:
                return data["faq"]["content"]
            else:
                # 전체 제공
                result = ""
                for key in ["reservation", "pricing", "cancellation", "points"]:
                    result += f"\n\n## {data[key]['title']}\n{data[key]['content']}"
                return result

        return "정보를 찾을 수 없습니다."

    def _format_city_bus_go_route(self, route_data: Dict) -> str:
        """시내버스 등교 노선 포맷팅"""
        result = f"## {route_data['name']}\n"
        result += f"**경로**: {route_data['route']}\n\n"

        for stop in route_data["stops"]:
            times_str = ", ".join(stop["times"])
            result += f"### {stop['name']}\n"
            result += f"- 시간: {times_str}\n"
            result += f"- 위치: {stop['location']}\n\n"

        return result

    def _format_city_bus_return(self, data: Dict) -> str:
        """시내버스 하교 포맷팅"""
        result = f"## {data['name']}\n"
        result += f"**경로**: {data['route']}\n\n"
        result += "### 시간표\n\n"
        result += "| 학교 출발 | 원주역 | 무실동 | 이화마을 | 터미널 |\n"
        result += "|----------|--------|--------|----------|--------|\n"

        for schedule in data["schedule"]:
            result += f"| {schedule['departure']} | {schedule['wonju_station']} | {schedule['musil']} | {schedule['ihwa']} | {schedule['terminal']} |\n"

        result += f"\n**정류장 안내**: {data['stops_info']}"
        return result

    def _format_intercity_go_seoul(self, data: Dict) -> str:
        """시외버스 서울 등교 포맷팅"""
        result = f"## {data['name']}\n"
        result += f"{data['important']}\n\n"

        for route in data["routes"]:
            result += f"### {route['name']}\n"
            result += f"- 출발: {route['departure']}\n"
            result += f"- 경유: {route['via']}\n"
            result += f"- 위치: {route['location']}\n\n"

        return result

    def _format_intercity_go_suwon_yeoju(self, data: Dict) -> str:
        """시외버스 수원/여주 등교 포맷팅"""
        result = f"## {data['name']}\n"
        result += f"{data['important']}\n\n"
        result += f"**출발**: {data['departure']}\n\n"

        for stop in data["stops"]:
            result += f"### {stop['name']}\n"
            result += f"- 시간: {stop['time']}\n"
            result += f"- 위치: {stop['location']}\n\n"

        return result

    def _format_intercity_return(self, data: Dict) -> str:
        """시외버스 하교 포맷팅"""
        result = f"## {data['name']}\n"
        result += f"**출발**: {data['departure']}\n"
        result += f"**경로**: {data['route']}\n\n"
        result += f"{data['important']}"
        return result

    async def generate_response(self, user_input: str, shuttle_info: str, token_counter=None) -> str:
        """응답 생성 에이전트"""
        try:
            prompt_config = self.prompts["response_generator"]
            prompt = prompt_config["user_prompt_template"].format(
                user_input=user_input,
                shuttle_info=shuttle_info
            )

            provider = get_provider("function_analyze")
            messages = [{"role": "user", "content": [{"type": "input_text", "text": prompt}]}]
            response, usage = await provider.simple_completion(messages)

            # API usage 기반 토큰 계산
            if token_counter and usage:
                token_counter.update_from_api_usage(
                    usage=usage,
                    role="function_analyze",
                    model=provider.get_model_name(),
                    category="function"
                )

            return response.strip()

        except Exception as e:
            print(f"[ShuttleBus] 응답 생성 오류: {e}")
            return shuttle_info  # 폴백: 원본 정보 반환
