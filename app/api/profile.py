"""Profile management endpoints for VIP Passport users."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.security import get_current_user
from app.schemas import CompleteProfileIn, UserOut
from app.models import User

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("/me", response_model=UserOut)
async def read_profile(user: User = Depends(get_current_user)) -> User:
    return user


@router.post("/complete", response_model=UserOut)
async def complete_profile(
    payload: CompleteProfileIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> User:
    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(user, field, value)

    if user.vip_since is None:
        user.vip_since = datetime.utcnow()

    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
