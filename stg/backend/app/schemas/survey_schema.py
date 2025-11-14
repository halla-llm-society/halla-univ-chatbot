from pydantic import BaseModel, Field
from typing import Optional, Literal


# /api/survey 엔드포인트의 request body type
class SurveyRequest(BaseModel):
    userCategory: Literal[
        "1학년", 
        "2학년", 
        "3학년", 
        "4학년", 
        "대학원생", 
        "교직원", 
        "외부인"
    ]
    
    rating: int = Field(..., ge=1, le=5)
    responseSpeed: Literal["high", "mid", "low"]
    responseQuality: Literal["high", "mid", "low"]
    comment: Optional[str] = Field(None, max_length=100)