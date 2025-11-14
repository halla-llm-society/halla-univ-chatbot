from pydantic_settings import BaseSettings

class Settings(BaseSettings):

    # MongoDB 설정
    MONGODB_URI: str    
    MONGODB_SUFFIX: str 

    class Config:
        env_file = ".env" 
        env_file_encoding = "utf-8"

settings = Settings()