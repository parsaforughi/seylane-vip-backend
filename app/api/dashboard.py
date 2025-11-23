"""Dashboard metrics for VIP Passport users."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models import Mission, MissionLog, MissionStatus, Stamp, User
from app.schemas import DashboardOut, UserOut
from app.security import get_current_user

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def _get_count(session: AsyncSession, status: MissionStatus, user: User) -> int:
    stmt = select(func.count()).select_from(MissionLog).where(
        MissionLog.user_id == user.id,
        MissionLog.status == status,
    )
    result = await session.scalar(stmt)
    return result or 0


@router.get("/", response_model=DashboardOut)
async def dashboard(
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DashboardOut:
    total_stamps_stmt = select(func.count()).select_from(Stamp).where(Stamp.user_id == user.id)
    total_stamps = int((await session.scalar(total_stamps_stmt)) or 0)

    total_points_stmt = (
        select(func.coalesce(func.sum(Mission.reward_points), 0))
        .select_from(MissionLog)
        .join(Mission, MissionLog.mission_id == Mission.id)
        .where(
            MissionLog.user_id == user.id,
            MissionLog.status == MissionStatus.APPROVED,
        )
    )
    total_points = int((await session.scalar(total_points_stmt)) or 0)

    pending = await _get_count(session, MissionStatus.PENDING, user)
    approved = await _get_count(session, MissionStatus.APPROVED, user)
    rejected = await _get_count(session, MissionStatus.REJECTED, user)

    return DashboardOut(
        user=UserOut.from_orm(user),
        total_stamps=total_stamps,
        total_points=total_points,
        missions_pending=pending,
        missions_approved=approved,
        missions_rejected=rejected,
    )
