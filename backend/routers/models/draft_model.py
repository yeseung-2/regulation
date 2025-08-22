# draft_model.py
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class HistoryItem(BaseModel):
    date: str
    description: str

class Draft(BaseModel):
    user_id: str
    company: str
    topic: str
    department: Optional[str] = ""
    html: str
    history: List[HistoryItem]
    is_final: Optional[bool] = False
    timestamp: Optional[datetime] = None