from fastapi import APIRouter, Request

from shared.schemas import StartBotSchema

router = APIRouter(prefix="", tags=["bot"])


@router.post("/start")
async def start(data: StartBotSchema, request: Request):
    bot_manager = request.app.state.bot_manager
    await bot_manager.start_monitoring(data)
    return {"status": "ok"}


@router.post("/stop")
async def stop(data: StartBotSchema, request: Request):
    bot_manager = request.app.state.bot_manager
    bot_manager.remove_user(user_id=data.user_id, item_id=data.item_id)
    return {"status": "ok"}
