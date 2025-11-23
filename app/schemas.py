"""Pydantic schemas used across the backend API."""

from __future__ import annotations

import uuid
from datetime import date, datetime

from pydantic import BaseModel

from app.models import MissionStatus, MissionType


class UserOut(BaseModel):
    id: uuid.UUID
    telegram_id: int
    store_name: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    city: str | None = None
    customer_code: str | None = None
    vip_since: datetime | None = None

    class Config:
        orm_mode = True


class CompleteProfileIn(BaseModel):
    store_name: str | None = None
    manager_name: str | None = None
    phone: str | None = None
    city: str | None = None
    customer_code: str | None = None


class DashboardOut(BaseModel):
    user: UserOut
    total_stamps: int
    total_points: int
    missions_pending: int
    missions_approved: int
    missions_rejected: int


class MissionOut(BaseModel):
    id: uuid.UUID
    code: str
    title: str
    description: str
    type: MissionType
    is_active: bool
    user_status: str


class MissionLogOut(BaseModel):
    id: uuid.UUID
    mission_id: uuid.UUID
    status: MissionStatus
    payload: dict
    admin_note: str | None = None

    class Config:
        orm_mode = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class DisplayIn(BaseModel):
    brand: str
    location_desc: str
    display_image_url: str
    notes: str | None = None


class DisplayOut(BaseModel):
    id: uuid.UUID
    status: MissionStatus
    brand: str
    location_desc: str
    display_image_url: str
    notes: str | None = None
    created_at: datetime

    class Config:
        orm_mode = True


class DisplaySubmissionOut(BaseModel):
    display_id: uuid.UUID
    mission_log_id: uuid.UUID | None
    display: DisplayOut


class ReferralCreate(BaseModel):
    store_name: str
    manager_name: str
    phone: str
    city: str
    notes: str | None = None


class ReferralResponse(BaseModel):
    referral_id: uuid.UUID
    mission_log_id: uuid.UUID | None


class PurchaseIn(BaseModel):
    amount: float
    purchase_date: date
    brands: list[str] | None = None
    description: str | None = None
    invoice_image_url: str
    invoice_number: str | None = None
    product_category: str | None = None
    barcode: str | None = None


class PurchaseOut(BaseModel):
    id: uuid.UUID
    status: MissionStatus
    amount: float
    purchase_date: date
    brands: list[str] | None = None
    description: str | None = None
    invoice_image_url: str
    invoice_number: str | None = None
    product_category: str | None = None
    barcode: str | None = None
    created_at: datetime

    class Config:
        orm_mode = True
