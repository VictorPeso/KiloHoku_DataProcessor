"""SQLAlchemy model for processing results."""

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.infrastructure.database.base import Base
from data_processor.infrastructure.database.models._schema import ASTRONOMY_SCHEMA


class ProcessingResult(Base):
    __tablename__ = "processing_results"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    job_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.processing_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    series_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.photometric_series.id", ondelete="CASCADE"),
    )
    result_type: Mapped[str] = mapped_column(String(100), nullable=False)
    result_version: Mapped[str | None] = mapped_column(String(50))
    result_payload: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    artifact_path: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
