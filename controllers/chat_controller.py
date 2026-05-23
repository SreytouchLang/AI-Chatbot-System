from fastapi import APIRouter
from services.chat_service import conversation
from schemas.router_schema import ChatRequest, ChatResponse

router = APIRouter(tags=["chat"])

@router.post("/chat", response_model=ChatResponse)
def chat_controller(request: ChatRequest) -> ChatResponse:
    result = conversation(
        user_id=request.user_id,
        q=request.q,
        top_k=request.top_k,
    )
    return ChatResponse(data=result)
