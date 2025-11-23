"""Purchase submissions tied to missions."""

from __future__ import annotations

import uuid

from decimal import Decimal

from datetime import date

from sqlalchemy import Date, Enum as SQLEnum, ForeignKey, JSON, Numeric, String, text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin
from .mission import MissionStatus


class Purchase(Base, TimestampMixin):
    __tablename__ = "purchases"

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
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    purchase_date: Mapped[date] = mapped_column(Date, nullable=False)
    invoice_image_url: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    invoice_image_url: Mapped[str] = mapped_column(String, nullable=False)
    brands: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    invoice_number: Mapped[str | None] = mapped_column(String, nullable=True)
    product_category: Mapped[str | None] = mapped_column(String, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String, nullable=True)
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

    user: Mapped["User"] = relationship("User", back_populates="purchases")
    mission: Mapped["Mission | None"] = relationship("Mission")
    mission_log: Mapped["MissionLog | None"] = relationship(
        "MissionLog", foreign_keys="Purchase.mission_log_id"
    )
