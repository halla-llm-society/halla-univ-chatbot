from pydantic import BaseModel
from typing import Optional

# /api/survey 엔드포인트의 request body type
class SurveyRequest(BaseModel):
    userCategory: str
    rating: int
    responseSpeed: str
    responseQuality: str
    comment: Optional[str] = None