"""Admin-only endpoints for VIP Passport management."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin
from app.api.display import approve_display_record, reject_display_record
from app.api.purchase import approve_purchase_record, reject_purchase_record
from app.api.referral import mark_referral_first_purchase_record
from app.db import get_session
from app.models import Display, Mission, MissionType, Purchase, Referral, User
from app.schemas import DisplayOut, PurchaseOut, UserOut

admin_router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)])


class MissionPayload(BaseModel):
    code: str
    title: str
    description: str
    type: MissionType
    reward_points: int
    reward_stamps: int = 0
    start_at: datetime | None = None
    end_at: datetime | None = None
    is_active: bool = True


def _mission_response(mission: Mission) -> dict:
    return {
        "id": mission.id,
        "code": mission.code,
        "title": mission.title,
        "description": mission.description,
        "type": mission.type.value if mission.type else None,
        "is_active": mission.is_active,
        "reward_points": mission.reward_points,
        "reward_stamps": mission.reward_stamps,
        "start_at": mission.start_at,
        "end_at": mission.end_at,
    }


@admin_router.get("/users")
async def list_users(session: AsyncSession = Depends(get_session)) -> list[UserOut]:
    users = (await session.scalars(select(User))).all()
    return [UserOut.from_orm(user) for user in users]


# Purchases
@admin_router.get("/purchases")
async def list_purchases(session: AsyncSession = Depends(get_session)) -> list[PurchaseOut]:
    purchases = (await session.scalars(select(Purchase))).all()
    return [PurchaseOut.from_orm(p) for p in purchases]


@admin_router.get("/purchases/{purchase_id}")
async def get_purchase(purchase_id: str, session: AsyncSession = Depends(get_session)) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")
    return PurchaseOut.from_orm(purchase)


@admin_router.post("/purchases/{purchase_id}/approve")
async def approve_purchase(
    purchase_id: str,
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")
    await approve_purchase_record(session, purchase)
    await session.commit()
    await session.refresh(purchase)
    return PurchaseOut.from_orm(purchase)


@admin_router.post("/purchases/{purchase_id}/reject")
async def reject_purchase(
    purchase_id: str,
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")
    await reject_purchase_record(session, purchase)
    await session.commit()
    await session.refresh(purchase)
    return PurchaseOut.from_orm(purchase)


# Displays
@admin_router.get("/displays")
async def list_displays(session: AsyncSession = Depends(get_session)) -> list[DisplayOut]:
    displays = (await session.scalars(select(Display))).all()
    return [DisplayOut.from_orm(display) for display in displays]


@admin_router.get("/displays/{display_id}")
async def get_display(display_id: str, session: AsyncSession = Depends(get_session)) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")
    return DisplayOut.from_orm(display)


@admin_router.post("/displays/{display_id}/approve")
async def approve_display(
    display_id: str,
    session: AsyncSession = Depends(get_session),
) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")
    await approve_display_record(session, display)
    await session.commit()
    await session.refresh(display)
    return DisplayOut.from_orm(display)


@admin_router.post("/displays/{display_id}/reject")
async def reject_display(
    display_id: str,
    session: AsyncSession = Depends(get_session),
) -> DisplayOut:
    display = await session.get(Display, display_id)
    if display is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Display not found.")
    await reject_display_record(session, display)
    await session.commit()
    await session.refresh(display)
    return DisplayOut.from_orm(display)


# Referrals
@admin_router.get("/referrals")
async def list_referrals(session: AsyncSession = Depends(get_session)) -> list[dict]:
    referrals = (await session.scalars(select(Referral))).all()
    return [
        {
            "id": referral.id,
            "referrer_user_id": referral.referrer_user_id,
            "store_name": referral.store_name,
            "manager_name": referral.manager_name,
            "phone": referral.phone,
            "city": referral.city,
            "first_purchase_completed": referral.first_purchase_completed,
            "mission_log_id": referral.mission_log_id,
        }
        for referral in referrals
    ]


@admin_router.post("/referrals/{referral_id}/mark-first-purchase")
async def mark_first_purchase(
    referral_id: str,
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    referral = await session.get(Referral, referral_id)
    if referral is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referral not found.")
    await mark_referral_first_purchase_record(session, referral)
    await session.commit()
    return {"status": "ok"}


# Missions
@admin_router.get("/missions")
async def list_missions(session: AsyncSession = Depends(get_session)) -> list[dict]:
    missions = (await session.scalars(select(Mission))).all()
    return [_mission_response(m) for m in missions]


@admin_router.post("/missions")
async def create_mission(
    payload: MissionPayload, session: AsyncSession = Depends(get_session)
) -> dict:
    mission = Mission(
        code=payload.code,
        title=payload.title,
        description=payload.description,
        type=MissionType(payload.type),
        reward_points=payload.reward_points,
        reward_stamps=payload.reward_stamps,
        start_at=payload.start_at,
        end_at=payload.end_at,
        is_active=payload.is_active,
    )
    session.add(mission)
    await session.commit()
    await session.refresh(mission)
    return _mission_response(mission)


@admin_router.put("/missions/{mission_id}")
async def update_mission(
    mission_id: str,
    payload: MissionPayload,
    session: AsyncSession = Depends(get_session),
) -> dict:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")
    mission.code = payload.code
    mission.title = payload.title
    mission.description = payload.description
    mission.type = MissionType(payload.type)
    mission.reward_points = payload.reward_points
    mission.reward_stamps = payload.reward_stamps
    mission.start_at = payload.start_at
    mission.end_at = payload.end_at
    mission.is_active = payload.is_active
    session.add(mission)
    await session.commit()
    await session.refresh(mission)
    return _mission_response(mission)


@admin_router.patch("/missions/{mission_id}/activate")
async def activate_mission(
    mission_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")
    mission.is_active = True
    session.add(mission)
    await session.commit()
    await session.refresh(mission)
    return {"status": "ok"}


@admin_router.patch("/missions/{mission_id}/deactivate")
async def deactivate_mission(
    mission_id: str, session: AsyncSession = Depends(get_session)
) -> dict:
    mission = await session.get(Mission, mission_id)
    if mission is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mission not found.")
    mission.is_active = False
    session.add(mission)
    await session.commit()
    await session.refresh(mission)
    return {"status": "ok"}
