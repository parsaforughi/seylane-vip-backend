"""Displays submitted by VIP users."""

from __future__ import annotations

import uuid

from sqlalchemy import Enum as SQLEnum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .mission import MissionStatus


class Display(Base, TimestampMixin):
    __tablename__ = "displays"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    brand: Mapped[str] = mapped_column(String, nullable=False)
    location_desc: Mapped[str] = mapped_column(String, nullable=False)
    display_image_url: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[MissionStatus] = mapped_column(
        SQLEnum(MissionStatus, name="mission_status"), nullable=False
    )
    mission_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("missions.id", ondelete="SET NULL"),
        nullable=True,
    )
    mission_log_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mission_logs.id", ondelete="SET NULL"),
        nullable=True,
    )

    user: Mapped["User"] = relationship("User", back_populates="displays")
    mission: Mapped["Mission | None"] = relationship("Mission")
    mission_log: Mapped["MissionLog | None"] = relationship(
        "MissionLog", foreign_keys="Display.mission_log_id"
    )
