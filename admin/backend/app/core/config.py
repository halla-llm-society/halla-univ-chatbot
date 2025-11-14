from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # MongoDB 설정
    STG_MONGODB_URI: str    
    PROD_MONGODB_URI: str

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"

settings = Settings()