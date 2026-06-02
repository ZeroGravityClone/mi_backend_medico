from fastapi import APIRouter, Depends
from app.schemas.ai import ChatRequest, ChatResponse
from app.services.ai_service import AIService
from app.api.deps import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["artificial intelligence"])

@router.post("/chat", response_model=ChatResponse)
def clinical_assistant_chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """Asistente de Inteligencia Artificial para consultas clínicas rápidas."""
    ai_service = AIService()
    ai_response = ai_service.get_clinical_assistant_response(payload.message)
    return {"response": ai_response}