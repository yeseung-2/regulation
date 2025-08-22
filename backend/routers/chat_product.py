from fastapi import APIRouter
from pydantic import BaseModel
from services.rag_router import ask_with_context  # services에서 import

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/rag")
def chat_rag(req: ChatRequest):
    result = ask_with_context(req.message)
    return result