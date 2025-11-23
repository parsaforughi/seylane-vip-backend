"""Display submission and admin flows."""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_user as require_admin
from app.db import get_session
from app.models import Display, Mission, MissionLog, MissionStatus, MissionType, User
from app.schemas import DisplayIn, DisplayOut, DisplaySubmissionOut
from app.security import get_current_user
from app.services.notification_service import send_notification
from app.services.stamp_service import award_stamps

router = APIRouter(prefix="/display", tags=["display"])


async def _find_active_display_mission(session: AsyncSession) -> Mission | None:
    now = datetime.utcnow()
    stmt = (
        select(Mission)
        .where(
            Mission.type == MissionType.DISPLAY,
            Mission.is_active.is_(True),
            or_(Mission.start_at.is_(None), Mission.start_at <= now),
            or_(Mission.end_at.is_(None), Mission.end_at >= now),
        )
        .limit(1)
    )
    return await session.scalar(stmt)


def _notification_payload(resource_id: uuid.UUID, mission: Mission | None) -> dict:
    return {
        "resource_id": str(resource_id),
        "mission_id": str(mission.id) if mission else None,
        "mission_code": mission.code if mission else None,
        "mission_type": mission.type.value if mission else None,
    }


def _display_to_out(display: Display) -> DisplayOut:
    return DisplayOut.from_orm(display)


async def _resolve_display_mission(
    session: AsyncSession,
    display: Display,
) -> tuple[Mission | None, MissionLog | None]:
    mission_log = None
    mission = None
    if display.mission_log_id:
        mission_log = await session.get(MissionLog, display.mission_log_id)
        if mission_log:
            mission = await session.get(Mission, mission_log.mission_id)
    elif display.mission_id:
        mission = await session.get(Mission, display.mission_id)
    return mission, mission_log


async def approve_display_record(
    session: AsyncSession,
    display: Display,
) -> tuple[Mission | None, MissionLog | None]:
    mission, mission_log = await _resolve_display_mission(session, display)
    display.status = MissionStatus.APPROVED
    session.add(display)
    if mission_log:
        mission_log.status = MissionStatus.APPROVED
        session.add(mission_log)
    if mission:
        await _apply_display_rewards(session, display, mission, mission_log)
    await send_notification(
        session,
        display.user_id,
        "DISPLAY_APPROVED",
        _notification_payload(display.id, mission),
    )
    return mission, mission_log


async def reject_display_record(
    session: AsyncSession,
    display: Display,
) -> tuple[Mission | None, MissionLog | None]:
    mission, mission_log = await _resolve_display_mission(session, display)
    display.status = MissionStatus.REJECTED
    session.add(display)
    if mission_log:
        mission_log.status = MissionStatus.REJECTED
        session.add(mission_log)
    await send_notification(
        session,
        display.user_id,
        "DISPLAY_REJECTED",
        _notification_payload(display.id, mission),
    )
    return mission, mission_log


async def _apply_display_rewards(
    session: AsyncSession,
    display: Display,
    mission: Mission,
    mission_log: MissionLog | None,
) -> None:
    user = await session.get(User, display.user_id)
    if user:
        user.total_points += mission.reward_points
        session.add(user)
    if mission.reward_stamps > 0:
        await award_stamps(
            session,
            display.user_id,
            mission.reward_stamps or 100_000_000,
            mission_log.id if mission_log else None,
        )


@router.post("/", response_model=DisplaySubmissionOut)
async def submit_display(
    payload: DisplayIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DisplaySubmissionOut:
    display = Display(
        user_id=user.id,
        brand=payload.brand,
        location_desc=payload.location_desc,
        display_image_url=payload.display_image_url,
        notes=payload.notes,
        status=MissionStatus.PENDING,
    )
    session.add(display)

    mission = await _find_active_display_mission(session)
    mission_log_id: uuid.UUID | None = None
    if mission:
        mission_log = MissionLog(
            mission_id=mission.id,
            user_id=user.id,
            status=MissionStatus.PENDING,
            payload={
                "brand": payload.brand,
                "location_desc": payload.location_desc,
                "display_image_url": payload.display_image_url,
            },
        )
        session.add(mission_log)
        await session.flush()
        display.mission_id = mission.id
        display.mission_log_id = mission_log.id
        mission_log_id = mission_log.id

    await session.commit()
    await session.refresh(display)
    return DisplaySubmissionOut(
        display_id=display.id,
        mission_log_id=mission_log_id,
        display=_display_to_out(display),
    )


@router.post("/{display_id}/approve", response_model=DisplayOut)
async def approve_display(
    display_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")

    display.status = MissionStatus.APPROVED
    session.add(display)

    await approve_display_record(session, display)

    await session.commit()
    await session.refresh(display)
    return _display_to_out(display)


@router.post("/{display_id}/reject", response_model=DisplayOut)
async def reject_display(
    display_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")

    display.status = MissionStatus.REJECTED
    session.add(display)

    await reject_display_record(session, display)

    await session.commit()
    await session.refresh(display)
    return _display_to_out(display)


@router.get("/{display_id}", response_model=DisplayOut)
async def get_display(
    display_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")
    if not user.is_admin and display.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    return _display_to_out(display)
