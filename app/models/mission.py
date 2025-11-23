"""Missions, logs, and shared enums."""

from __future__ import annotations

import enum
import uuid

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, text, JSON
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class MissionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    DISPLAY = "DISPLAY"
    REFERRAL = "REFERRAL"
    LAUNCH = "LAUNCH"
    PRODUCT_TEST = "PRODUCT_TEST"


class MissionStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Mission(Base, TimestampMixin):
    __tablename__ = "missions"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    code: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[MissionType] = mapped_column(
        SQLEnum(MissionType, name="mission_type"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default=text("true")
    )
    start_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    end_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    reward_points: Mapped[int] = mapped_column(Integer, nullable=False)
    reward_stamps: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, server_default=text("0")
    )

    mission_logs: Mapped[list["MissionLog"]] = relationship(
        "MissionLog", back_populates="mission", cascade="all, delete-orphan"
    )


class MissionLog(Base, TimestampMixin):
    __tablename__ = "mission_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    mission_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[MissionStatus] = mapped_column(
        SQLEnum(MissionStatus, name="mission_status"), nullable=False
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    admin_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="missions_logs")
    mission: Mapped["Mission"] = relationship("Mission", back_populates="mission_logs")
    stamps: Mapped[list["Stamp"]] = relationship(
        "Stamp", back_populates="mission_log", cascade="all, delete-orphan"
    )
