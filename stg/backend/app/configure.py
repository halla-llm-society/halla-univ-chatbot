import os
from dotenv import load_dotenv

load_dotenv()

ROOT_PATH = os.getenv("ROOT_PATH", "") # stg용 root path
MONGODB_URI = os.getenv("BACKEND_MONGODB_URI") # stg, prod 분리
MONGODB_SUFFIX = os.getenv("BACKEND_MONGODB_SUFFIX") # stg, prod 분리