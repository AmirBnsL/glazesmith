import logging
from fastapi import APIRouter, HTTPException
from ..models.schemas import ChatRequest, ChatResponse, RecipeAdjustment
from ..agent.core import get_agent

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        agent = get_agent()
        history_dicts = [{"role": m.role, "content": m.content} for m in request.history]
        recipe_dicts = [{"material": i.material, "percentage": i.percentage} for i in request.recipe]

        result = agent.chat(
            message=request.message,
            history=history_dicts,
            context=request.context,
            original_recipe=recipe_dicts,
        )

        verified = [
            RecipeAdjustment(**adj) for adj in result.get("verified_adjustments", [])
            if isinstance(adj, dict)
        ]

        return ChatResponse(
            reply=result.get("reply", ""),
            verified_adjustments=verified,
            verification_summary=result.get("verification_summary", ""),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Chat failed: %s", e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
