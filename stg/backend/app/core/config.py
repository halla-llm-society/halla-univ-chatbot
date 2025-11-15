from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # 인프라 설정
    ROOT_PATH: str = ""
    AI_SERVICE_URL: str = "http://chatbot-ai-container:8000" 

    # MongoDB 설정
    MONGODB_URI: str    
    MONGODB_SUFFIX: str 

    # Redis(AWS ElastiCache) 설정
    REDIS_HOST: str = "local-redis"
    REDIS_PORT: int = 6379
    MONTHLY_COST_LIMIT: float = 1000.

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"

settings = Settings()