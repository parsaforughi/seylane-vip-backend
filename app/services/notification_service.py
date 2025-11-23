"""Notification helpers for mission events."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import NotificationLog


async def send_notification(
    session: AsyncSession,
    user_id: uuid.UUID,
    type: str,
    payload: dict,
) -> NotificationLog:
    """Record a notification event."""

    notification = NotificationLog(
        user_id=user_id,
        type=type,
        payload=payload,
        sent_at=datetime.utcnow(),
    )
    session.add(notification)
    await session.flush()
    return notification
