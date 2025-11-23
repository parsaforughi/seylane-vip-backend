"""Mission engine for VIP Passport users and admins."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_user as require_admin
from app.db import get_session
from app.models import Mission, MissionLog, MissionStatus, User
from app.schemas import MissionLogOut, MissionOut
from app.security import get_current_user
from app.services.notification_service import send_notification
from app.services.stamp_service import award_stamps

router = APIRouter(prefix="/missions", tags=["missions"])


def _notification_payload(resource_id: uuid.UUID, mission: Mission | None) -> dict:
    return {
        "resource_id": str(resource_id),
        "mission_id": str(mission.id) if mission else None,
        "mission_code": mission.code if mission else None,
        "mission_type": mission.type.value if mission else None,
    }


@router.get("/", response_model=list[MissionOut])
async def list_missions(
    user: User = Depends(get_current_user), session: AsyncSession = Depends(get_session)
) -> list[MissionOut]:
    now = datetime.utcnow()
    stmt = select(Mission).where(
        Mission.is_active.is_(True),
        or_(Mission.start_at.is_(None), Mission.start_at <= now),
        or_(Mission.end_at.is_(None), Mission.end_at >= now),
    )
    missions = (await session.scalars(stmt)).all()
    logs = (await session.scalars(select(MissionLog).where(MissionLog.user_id == user.id))).all()
    log_map = {log.mission_id: log.status for log in logs}

    def _status_for(mission_id: uuid.UUID) -> str:
        status_value = log_map.get(mission_id)
        if status_value is None:
            return "NONE"
        return status_value.value

    return [
        MissionOut(
            id=mission.id,
            code=mission.code,
            title=mission.title,
            description=mission.description,
            type=mission.type,
            is_active=mission.is_active,
            user_status=_status_for(mission.id),
        )
        for mission in missions
    ]


@router.post("/{mission_id}/start", response_model=MissionLogOut)
async def start_mission(
    mission_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> MissionLogOut:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    now = datetime.utcnow()
    if not mission.is_active or (mission.start_at and mission.start_at > now) or (
        mission.end_at and mission.end_at < now
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mission not available.")

    existing = await session.scalar(
        select(MissionLog).where(
            MissionLog.mission_id == mission_id,
            MissionLog.user_id == user.id,
        )
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Mission already started.")

    mission_log = MissionLog(
        mission_id=mission_id,
        user_id=user.id,
        status=MissionStatus.PENDING,
        payload={},
    )
    session.add(mission_log)
    await session.commit()
    await session.refresh(mission_log)
    return MissionLogOut.from_orm(mission_log)


@router.post("/{mission_id}/approve/{log_id}", response_model=MissionLogOut)
async def approve_mission(
    mission_id: uuid.UUID,
    log_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> MissionLogOut:
    mission_log = await session.get(MissionLog, log_id)
    if mission_log is None or mission_log.mission_id != mission_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission log not found.")

    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")

    mission_log.status = MissionStatus.APPROVED
    session.add(mission_log)

    await award_stamps(session, mission_log.user_id, mission.reward_stamps, mission_log.id)
    await send_notification(
        session,
        mission_log.user_id,
        "MISSION_APPROVED",
        _notification_payload(mission_log.id, mission),
    )

    await session.commit()
    await session.refresh(mission_log)
    return MissionLogOut.from_orm(mission_log)


@router.post("/{mission_id}/reject/{log_id}", response_model=MissionLogOut)
async def reject_mission(
    mission_id: uuid.UUID,
    log_id: uuid.UUID,
    admin_note: str | None = Body(None),
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> MissionLogOut:
    mission_log = await session.get(MissionLog, log_id)
    if mission_log is None or mission_log.mission_id != mission_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission log not found.")

    mission_log.status = MissionStatus.REJECTED
    if admin_note is not None:
        mission_log.admin_note = admin_note
    session.add(mission_log)

    await send_notification(
        session,
        mission_log.user_id,
        "MISSION_REJECTED",
        _notification_payload(mission_log.id, mission_log.mission),
    )

    await session.commit()
    await session.refresh(mission_log)
    return MissionLogOut.from_orm(mission_log)
