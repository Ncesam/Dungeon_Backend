import uvicorn
from fastapi import FastAPI

from api.routes.bot import router as bot_router
from database.repository import get_session
from logics.botmanager import BotManager
from shared.config import Configuration

configuration = Configuration()
app = FastAPI(debug=configuration.DEBUG)

app.include_router(bot_router)


async def lifetime(app: FastAPI):
    async with get_session() as session:
        bot_manager = BotManager(session)
        yield app


if __name__ == '__main__':
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
