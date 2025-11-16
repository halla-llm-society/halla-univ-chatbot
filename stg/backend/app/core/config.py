from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # 인프라 설정
    ROOT_PATH: str = ""
    AI_SERVICE_URL: str = "http://chatbot-ai-container:8000" 

    # MongoDB 설정
    MONGODB_URI: str    
    MONGODB_SUFFIX: str 

    # 사용량 확인
    MONTHLY_COST_LIMIT: float = 1000.
    OPENAI_ADMIN_KEY: str
    OPENAI_PROJECT_ID: str
    COSTS_API_URL: str

    # Discord 설정
    DISCORD_WEBHOOK_URL: str

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"

settings = Settings()