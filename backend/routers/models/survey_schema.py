# routers/models/survey_schema.py

from pydantic import BaseModel
from typing import List

class SurveyData(BaseModel):
    industry_ko: str
    industry_code: str
    employee_count: str
    esg_experience: str
    esg_activities: List[str]
    emphasis_areas: List[str]
