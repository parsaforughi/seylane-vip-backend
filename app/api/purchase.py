"""Purchase submission and admin management."""

from __future__ import annotations

import uuid
from decimal import Decimal
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_user as require_admin
from app.db import get_session
from app.models import (
    Mission,
    MissionLog,
    MissionStatus,
    MissionType,
    Purchase,
    User,
)
from app.schemas import PurchaseIn, PurchaseOut
from app.security import get_current_user
from app.services.notification_service import send_notification
from app.services.stamp_service import award_stamps

router = APIRouter(prefix="/purchase", tags=["purchase"])


def _mission_log_payload(payload: PurchaseIn) -> dict[str, float | str | list[str] | None]:
    return {
        "amount": payload.amount,
        "invoice_number": payload.invoice_number,
        "brands": payload.brands,
        "product_category": payload.product_category,
        "barcode": payload.barcode,
    }


async def _find_active_purchase_mission(session: AsyncSession) -> Mission | None:
    now = datetime.utcnow()
    stmt = (
        select(Mission)
        .where(
            Mission.type == MissionType.PURCHASE,
            Mission.is_active.is_(True),
            or_(Mission.start_at.is_(None), Mission.start_at <= now),
            or_(Mission.end_at.is_(None), Mission.end_at >= now),
        )
        .limit(1)
    )
    return await session.scalar(stmt)


def _purchase_to_out(purchase: Purchase) -> PurchaseOut:
    return PurchaseOut.from_orm(purchase)


def _notification_payload(resource_id: uuid.UUID, mission: Mission | None) -> dict:
    return {
        "resource_id": str(resource_id),
        "mission_id": str(mission.id) if mission else None,
        "mission_code": mission.code if mission else None,
        "mission_type": mission.type.value if mission else None,
    }


async def _resolve_purchase_mission(
    session: AsyncSession,
    purchase: Purchase,
) -> tuple[Mission | None, MissionLog | None]:
    mission_log = None
    mission = None
    if purchase.mission_log_id:
        mission_log = await session.get(MissionLog, purchase.mission_log_id)
        if mission_log:
            mission = await session.get(Mission, mission_log.mission_id)
    elif purchase.mission_id:
        mission = await session.get(Mission, purchase.mission_id)
    return mission, mission_log


async def approve_purchase_record(
    session: AsyncSession,
    purchase: Purchase,
) -> tuple[Mission | None, MissionLog | None]:
    mission, mission_log = await _resolve_purchase_mission(session, purchase)
    purchase.status = MissionStatus.APPROVED
    session.add(purchase)
    if mission_log:
        mission_log.status = MissionStatus.APPROVED
        session.add(mission_log)
    if mission:
        user = await session.get(User, purchase.user_id)
        if user:
            user.total_points += mission.reward_points
            session.add(user)
        await award_stamps(
            session,
            purchase.user_id,
            mission.reward_stamps,
            mission_log.id if mission_log else None,
        )
    await send_notification(
        session,
        purchase.user_id,
        "PURCHASE_APPROVED",
        _notification_payload(purchase.id, mission),
    )
    return mission, mission_log


async def reject_purchase_record(
    session: AsyncSession,
    purchase: Purchase,
) -> tuple[Mission | None, MissionLog | None]:
    mission, mission_log = await _resolve_purchase_mission(session, purchase)
    purchase.status = MissionStatus.REJECTED
    session.add(purchase)
    if mission_log:
        mission_log.status = MissionStatus.REJECTED
        session.add(mission_log)
    await send_notification(
        session,
        purchase.user_id,
        "PURCHASE_REJECTED",
        _notification_payload(purchase.id, mission),
    )
    return mission, mission_log


@router.post("/", response_model=PurchaseOut)
async def create_purchase(
    payload: PurchaseIn,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = Purchase(
        user_id=user.id,
        amount=Decimal(str(payload.amount)),
        purchase_date=payload.purchase_date,
        description=payload.description,
        invoice_image_url=payload.invoice_image_url,
        brands=payload.brands,
        invoice_number=payload.invoice_number,
        product_category=payload.product_category,
        barcode=payload.barcode,
        status=MissionStatus.PENDING,
    )
    session.add(purchase)

    mission = await _find_active_purchase_mission(session)
    if mission:
        mission_log = MissionLog(
            mission_id=mission.id,
            user_id=user.id,
            status=MissionStatus.PENDING,
            payload=_mission_log_payload(payload),
        )
        session.add(mission_log)
        await session.flush()
        purchase.mission_id = mission.id
        purchase.mission_log_id = mission_log.id

    await session.commit()
    await session.refresh(purchase)
    return _purchase_to_out(purchase)


@router.post("/{purchase_id}/approve", response_model=PurchaseOut)
async def approve_purchase(
    purchase_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")

    mission, _ = await approve_purchase_record(session, purchase)

    await session.commit()
    await session.refresh(purchase)
    return _purchase_to_out(purchase)


@router.post("/{purchase_id}/reject", response_model=PurchaseOut)
async def reject_purchase(
    purchase_id: uuid.UUID,
    _admin: User = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")

    await reject_purchase_record(session, purchase)

    await session.commit()
    await session.refresh(purchase)
    return _purchase_to_out(purchase)


@router.get("/{purchase_id}", response_model=PurchaseOut)
async def get_purchase(
    purchase_id: uuid.UUID,
    user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> PurchaseOut:
    purchase = await session.get(Purchase, purchase_id)
    if purchase is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Purchase not found.")
    if not user.is_admin and purchase.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized.")
    return _purchase_to_out(purchase)
