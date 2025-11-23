"""Stamp rewards associated with mission logs."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Stamp(Base, TimestampMixin):
    __tablename__ = "stamps"

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
    mission_log_id: Mapped[uuid.UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mission_logs.id", ondelete="SET NULL"),
        nullable=True,
    )
    value: Mapped[int] = mapped_column(Integer, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="stamps")
    mission_log: Mapped["MissionLog | None"] = relationship("MissionLog", back_populates="stamps")
