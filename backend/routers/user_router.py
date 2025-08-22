# routers/user_router.py

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId
from services.database import users_collection
from services.jwt_utils import get_current_user
from routers.models.survey_schema import SurveyData

router = APIRouter()

@router.post("/survey")
def save_survey(data: SurveyData, user=Depends(get_current_user)):
    result = users_collection.update_one(
        {"_id": ObjectId(user["id"])},
        {"$set": data.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="사용자 정보 없음")
    return {"message": "설문 저장 완료"}

@router.get("/profile")
def get_profile(user=Depends(get_current_user)):
    doc = users_collection.find_one({"_id": ObjectId(user["id"])})
    if not doc:
        raise HTTPException(status_code=404, detail="사용자 없음")
    return {
        "industry_ko": doc.get("industry_ko"),
        "industry_code": doc.get("industry_code"),
        "employee_count": doc.get("employee_count"),
        "esg_experience": doc.get("esg_experience"),
        "esg_activities": doc.get("esg_activities", []),
        "emphasis_areas": doc.get("emphasis_areas", [])
    }
