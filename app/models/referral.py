"""Referrals for new VIP partners."""

from __future__ import annotations

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Referral(Base, TimestampMixin):
    __tablename__ = "referrals"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v4()"),
        nullable=False,
    )
    referrer_user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_name: Mapped[str] = mapped_column(String, nullable=False)
    manager_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    first_purchase_completed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="false"
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

    referrer: Mapped["User"] = relationship("User", back_populates="referrals")
    mission: Mapped["Mission | None"] = relationship("Mission")
    mission_log: Mapped["MissionLog | None"] = relationship(
        "MissionLog", foreign_keys="Referral.mission_log_id"
    )
