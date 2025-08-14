from fastapi import APIRouter

from shared.context import bot_manager_ctx
from shared.schemas import StartBotSchema

router = APIRouter(prefix="/bot", tags=["bot"])


@router.post("/start")
async def start(data: StartBotSchema):
    bot_manager = bot_manager_ctx.get()
    await bot_manager.start_monitoring(data)
    return {"status": "ok"}


@router.post("/stop")
async def stop(data: StartBotSchema):
    bot_manager = bot_manager_ctx.get()
    bot_manager.remove_user(user_id=data.user_id, item_id=data.item_id)
    return {"status": "ok"}
