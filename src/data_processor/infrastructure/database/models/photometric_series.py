"""SQLAlchemy model for photometric series."""

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.infrastructure.database.base import Base
from data_processor.infrastructure.database.models._schema import ASTRONOMY_SCHEMA


class PhotometricSeries(Base):
    __tablename__ = "photometric_series"
    __table_args__ = (
        CheckConstraint(
            (
                "status IN ('pending', 'processing', 'completed', "
                "'completed_with_warnings', 'failed')"
            ),
            name="photometric_series_status",
        ),
        UniqueConstraint(
            "object_id", "filter_code", "source_file_id", name="uq_series_object_filter_file"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    object_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.astronomical_objects.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_file_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.source_files.id", ondelete="RESTRICT"),
        nullable=False,
    )
    filter_code: Mapped[str] = mapped_column(String(10), nullable=False)
    source_filename: Mapped[str] = mapped_column(Text, nullable=False)
    source_format: Mapped[str] = mapped_column(String(50), nullable=False, server_default="VOTable")
    source_format_version: Mapped[str | None] = mapped_column(String(20))
    observation_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pending")
    processing_error: Mapped[str | None] = mapped_column(Text)
    imported_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
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
