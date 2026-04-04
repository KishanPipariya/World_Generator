from fastapi import APIRouter, Depends

from app.deps import get_llm_service
from app.services.llm_service import LLMService

router = APIRouter(tags=["health"])


@router.get("/health")
def health(llm: LLMService = Depends(get_llm_service)) -> dict[str, object]:
    return {
        "status": "ok",
        "llm": {"mode": llm.mode, "enabled": llm.enabled()},
    }
