from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from fastapi import APIRouter, Request
from app.config import settings

bot = Bot(
    token=settings.telegram_bot_token,
    default=DefaultBotProperties(parse_mode="HTML")
)

router = Router()


@router.message(Command("start"))
async def start_cmd(message: Message):
    # دکمه Mini App با HTTPS
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="ورود به Mini App",
                    web_app=WebAppInfo(url=settings.miniapp_url)
                )
            ]
        ]
    )

    await message.answer(
        "سلام! خوش آمدید. برای ورود به Mini App روی دکمه زیر بزنید.",
        reply_markup=keyboard
    )


dp = Dispatcher()
dp.include_router(router)

api_router = APIRouter()


@api_router.post("/bot/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update(**data)
    await dp.feed_update(bot, update)
    return {"ok": True}