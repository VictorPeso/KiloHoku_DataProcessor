"""SQLAlchemy model for structured processing warnings."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.infrastructure.database.base import Base
from data_processor.infrastructure.database.models._schema import ASTRONOMY_SCHEMA


class ProcessingWarning(Base):
    __tablename__ = "processing_warnings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.processing_jobs.id", ondelete="CASCADE"),
    )
    source_file_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.source_files.id", ondelete="CASCADE"),
    )
    series_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.photometric_series.id", ondelete="CASCADE"),
    )
    warning_code: Mapped[str] = mapped_column(String(100), nullable=False)
    warning_message: Mapped[str] = mapped_column(Text, nullable=False)
    warning_details: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
