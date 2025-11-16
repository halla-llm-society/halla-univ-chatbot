from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # MongoDB 설정
    STG_MONGODB_URI: str    
    PROD_MONGODB_URI: str
    
    STG_DB_NAME: str = "halla-chatbot-stg"
    PROD_DB_NAME: str = "halla-chatbot-prod"
    
    # 인증 관련 설정 추가
    GOOGLE_CLIENT_ID: str
    ALLOWED_ADMIN_EMAIL: str
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str
    
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 2 # 2시간
    
    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"
        extra = 'ignore'

settings = Settings()