"""SQLAlchemy model for original source files."""

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.infrastructure.database.base import Base


class SourceFile(Base):
    __tablename__ = "source_files"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'importing', 'imported', 'failed', 'duplicate', 'unsupported')",
            name="source_files_status",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    original_filename: Mapped[str] = mapped_column(Text, nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger)
    source_format: Mapped[str] = mapped_column(String(50), nullable=False, server_default="VOTable")
    source_format_version: Mapped[str | None] = mapped_column(String(20))
    detected_object_name: Mapped[str | None] = mapped_column(String(100))
    detected_filter_code: Mapped[str | None] = mapped_column(String(10))
    status: Mapped[str] = mapped_column(String(30), nullable=False, server_default="pending")
    error_message: Mapped[str | None] = mapped_column(Text)
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
