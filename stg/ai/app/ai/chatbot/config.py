import os
from pathlib import Path
from openai import OpenAI
from dataclasses import dataclass
from datetime import datetime, timedelta
import pytz
# 추가: dotenv 임포트
from dotenv import load_dotenv

# apikey.env 파일 경로 설정 (app/ 디렉토리 기준)
# config.py의 위치: app/ai/chatbot/config.py
# apikey.env의 위치: app/apikey.env
_BASE_DIR = Path(__file__).resolve().parent.parent.parent  # app/
_DOTENV_PATH = _BASE_DIR / "apikey.env"
load_dotenv(_DOTENV_PATH)

@dataclass(frozen=True)
class Model: 
    basic: str = "gpt-3.5-turbo-1106"
    # web_search_preview 툴 미지원 모델(gpt-4-1106-preview) → gpt-4.1로 교체
    # 필요 시 mini 모델로 조정 가능: gpt-4.1-mini
    advanced: str = "gpt-4.1"
    o3_mini: str ="o3-mini"
    o1: str = "o1"

@dataclass(frozen=True)
class EmbeddingModel:
    small: str = "text-embedding-3-small"
    ada: str = "text-embedding-ada-002"
    large: str = "text-embedding-3-large"
    
model = Model()
embedding_model = EmbeddingModel()
api_key = os.getenv("OPENAI_API_KEY")  # 이제 경로와 무관하게 로드됨
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
def today():
    korea = pytz.timezone('Asia/Seoul')# 한국 시간대를 얻습니다.
    now = datetime.now(korea)# 현재 시각을 얻습니다.
    return(now.strftime("%Y%m%d"))# 시각을 원하는 형식의 문자열로 변환합니다.

def yesterday():    
    korea = pytz.timezone('Asia/Seoul')# 한국 시간대를 얻습니다.
    now = datetime.now(korea)# 현재 시각을 얻습니다.
    one_day = timedelta(days=1)    # 하루 (1일)를 나타내는 timedelta 객체를 생성합니다.
    yesterday = now - one_day # 현재 날짜에서 하루를 빼서 어제의 날짜를 구합니다.
    return yesterday.strftime('%Y%m%d') # 어제의 날짜를 yyyymmdd 형식으로 변환합니다.

def currTime():
    # 한국 시간대를 얻습니다.
    korea = pytz.timezone('Asia/Seoul')
    # 현재 시각을 얻습니다.
    now = datetime.now(korea)
    # 시각을 원하는 형식의 문자열로 변환합니다.
    formatted_now = now.strftime("%Y.%m.%d %H:%M:%S")
    return(formatted_now)