from fastapi import FastAPI
from app.api import api_router
from app.db import init_db
from app.bot.bot import api_router as bot_router

app = FastAPI()


@app.on_event("startup")
async def startup_event():
    await init_db()

app.include_router(api_router, prefix="/api/v1")
app.include_router(bot_router)
