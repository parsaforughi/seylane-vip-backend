"""Stamp awarding helpers."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Stamp


async def award_stamps(
    session: AsyncSession, user_id: uuid.UUID, amount: int, mission_log_id: uuid.UUID | None
) -> Stamp | None:
    """Create a stamp record when a mission grants stamp rewards."""

    if amount is None or amount <= 0:
        return None

    stamp = Stamp(user_id=user_id, mission_log_id=mission_log_id, value=amount)
    session.add(stamp)
    await session.flush()
    return stamp
