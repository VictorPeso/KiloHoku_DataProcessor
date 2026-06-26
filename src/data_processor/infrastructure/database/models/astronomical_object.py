"""SQLAlchemy model for astronomical objects."""

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Double, String, func
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.infrastructure.database.base import Base


class AstronomicalObject(Base):
    __tablename__ = "astronomical_objects"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    ztf_oid: Mapped[int | None] = mapped_column(BigInteger)
    mean_ra: Mapped[float | None] = mapped_column(Double)
    mean_dec: Mapped[float | None] = mapped_column(Double)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
