from datetime import datetime
from services.db import draft_collection
from services.db import input_collection
from fastapi import HTTPException

def delete_draft(topic: str, company: str) -> bool:
    result = draft_collection.delete_one({"topic": topic, "company": company})
    return result.deleted_count > 0


def save_draft(topic: str, company: str, draft: str):
    draft_collection.update_one(
        {"topic": topic, "company": company},
        {
            "$set": {
                "draft": draft,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def load_draft(topic: str, company: str):
    doc = draft_collection.find_one({"topic": topic, "company": company})
    return doc["draft"] if doc else None

def save_input_data(topic: str, company: str, data: dict):
    input_collection.update_one(
        {"topic": topic, "company": company},
        {
            "$set": {
                "data": data,
                "updated_at": datetime.utcnow()
            }
        },
        upsert=True
    )

def load_input_data(topic: str, company: str):
    doc = input_collection.find_one({"topic": topic, "company": company})
    return doc.get("data", {}) if doc else {}
