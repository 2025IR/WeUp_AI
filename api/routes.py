from fastapi import APIRouter
from capstone_ai.api.models import ChatRequest, ChatResponse
from capstone_ai.service.chat_service import ChatService

router = APIRouter()

service = ChatService()

@router.post("/ai/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return service.handle(req)