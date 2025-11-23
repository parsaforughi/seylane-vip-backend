"""Authentication endpoints for the VIP Passport backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import User
from app.schemas import TokenResponse
from app.security import create_access_token


class TelegramAuthIn(BaseModel):
    init_data: str


router = APIRouter(prefix="/auth", tags=["auth"])


def verify_telegram_init_data(init_data: str) -> dict:
    """Mock verification for Telegram init data."""

    # TODO: replace this placeholder with real Telegram WebApp verification logic.
    return {"telegram_id": 123456789, "first_name": "Test User"}


@router.post("/telegram", response_model=TokenResponse)
async def telegram_auth(
    payload: TelegramAuthIn, session: AsyncSession = Depends(get_session)
) -> TokenResponse:
    data = verify_telegram_init_data(payload.init_data)
    stmt = select(User).where(User.telegram_id == data["telegram_id"])
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    if user is None:
        user = User(telegram_id=data["telegram_id"])
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token = create_access_token({"user_id": str(user.id)})
    return TokenResponse(access_token=access_token)
