"""Referral intake and completion endpoints."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_user as require_admin
from app.db import get_session
from app.models import Mission, MissionLog, MissionStatus, MissionType, Referral, User
from app.schemas import ReferralCreate, ReferralResponse
from app.security import get_current_user
from app.services.notification_service import send_notification
from app.services.stamp_service import award_stamps

router = APIRouter(prefix="/referral", tags=["referral"])


def _notification_payload(resource_id: uuid.UUID, mission: Mission | None) -> dict:
    return {
        "resource_id": str(resource_id),
        "mission_id": str(mission.id) if mission else None,
        "mission_code": mission.code if mission else None,
        "mission_type": mission.type.value if mission else None,
    }


async def _resolve_referral_mission(
    session: AsyncSession,
    referral: Referral,
) -> tuple[Mission | None, MissionLog | None]:
    mission_log = None
    mission = None
    if referral.mission_log_id:
        mission_log = await session.get(MissionLog, referral.mission_log_id)
        if mission_log:
            mission = await session.get(Mission, mission_log.mission_id)
    elif referral.mission_id:
        mission = await session.get(Mission, referral.mission_id)
    return mission, mission_log


async def mark_referral_first_purchase_record(
    session: AsyncSession,
    referral: Referral,
) -> tuple[Mission | None, MissionLog | None]:
    mission, mission_log = await _resolve_referral_mission(session, referral)
    referral.first_purchase_completed = True
    session.add(referral)
    if mission_log:
        mission_log.status = MissionStatus.APPROVED
        session.add(mission_log)
    elif mission:
        mission_log = MissionLog(
            mission_id=mission.id,
            user_id=referral.referrer_user_id,
            status=MissionStatus.APPROVED,
            payload={"referral_id": str(referral.id)},
        )
        session.add(mission_log)
        await session.flush()
        referral.mission_log_id = mission_log.id
    if mission:
        user = await session.get(User, referral.referrer_user_id)
        if user:
            user.total_points += mission.reward_points
            session.add(user)
        await award_stamps(
            session,
            referral.referrer_user_id,
            mission.reward_stamps,
            mission_log.id if mission_log else None,
        )
    await send_notification(
        session,
        referral.referrer_user_id,
        "REFERRAL_COMPLETED",
        _notification_payload(referral.id, mission),
    )
    return mission, mission_log


@router.post("/", response_model=ReferralResponse)
async def create_referral(
    payload: ReferralCreate,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ReferralResponse:
    referral = Referral(
        referrer_user_id=user.id,
        store_name=payload.store_name,
        manager_name=payload.manager_name,
        phone=payload.phone,
        city=payload.city,
        notes=payload.notes,
    )
    session.add(referral)

    now = datetime.utcnow()
    mission_stmt = (
        select(Mission)
        .where(
            Mission.type == MissionType.REFERRAL,
            Mission.is_active.is_(True),
            or_(Mission.start_at.is_(None), Mission.start_at <= now),
            or_(Mission.end_at.is_(None), Mission.end_at >= now),
        )
        .limit(1)
    )
    mission = await session.scalar(mission_stmt)
    mission_log_id: uuid.UUID | None = None
    if mission:
        mission_log = MissionLog(
            mission_id=mission.id,
            user_id=user.id,
            status=MissionStatus.PENDING,
            payload={"referral_id": str(referral.id)},
        )
        session.add(mission_log)
        await session.flush()
        referral.mission_id = mission.id
        referral.mission_log_id = mission_log.id
        mission_log_id = mission_log.id

    await session.commit()
    await session.refresh(referral)
    return ReferralResponse(
        referral_id=referral.id,
        mission_log_id=mission_log_id,
    )


@router.post("/{referral_id}/mark-first-purchase")
async def mark_first_purchase(
    referral_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    referral = await session.get(Referral, referral_id)
    if referral is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")

    await mark_referral_first_purchase_record(session, referral)

    await session.commit()
    return {"status": "ok"}
