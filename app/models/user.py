"""User model and its relationships."""

from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, Integer, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    telegram_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, index=True, nullable=False
    )
    store_name: Mapped[str | None] = mapped_column(String, nullable=True)
    manager_name: Mapped[str | None] = mapped_column(String, nullable=True)
    phone: Mapped[str | None] = mapped_column(String, nullable=True)
    city: Mapped[str | None] = mapped_column(String, nullable=True)
    customer_code: Mapped[str | None] = mapped_column(
        String, nullable=True, index=True
    )
    vip_since: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default=text("false"))
    total_points: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))

    missions_logs: Mapped[list["MissionLog"]] = relationship(
        "MissionLog", back_populates="user", cascade="all, delete-orphan"
    )
    purchases: Mapped[list["Purchase"]] = relationship(
        "Purchase", back_populates="user", cascade="all, delete-orphan"
    )
    displays: Mapped[list["Display"]] = relationship(
        "Display", back_populates="user", cascade="all, delete-orphan"
    )
    referrals: Mapped[list["Referral"]] = relationship(
        "Referral", back_populates="referrer", cascade="all, delete-orphan"
    )
    stamps: Mapped[list["Stamp"]] = relationship(
        "Stamp", back_populates="user", cascade="all, delete-orphan"
    )
    notifications: Mapped[list["NotificationLog"]] = relationship(
        "NotificationLog", back_populates="user", cascade="all, delete-orphan"
    )
