from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes.bot import router as bot_router
from logics.botmanager import BotManager
from shared.config import Configuration

configuration = Configuration()


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.bot_manager = BotManager()
    yield


app = FastAPI(debug=configuration.DEBUG, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(bot_router)

if __name__ == '__main__':
    uvicorn.run(app=app, host="0.0.0.0", port=8000)
