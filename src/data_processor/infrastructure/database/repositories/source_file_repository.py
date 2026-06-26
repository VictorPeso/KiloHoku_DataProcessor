"""PostgreSQL implementation of the source file repository."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from data_processor.core.application.ports.source_file_repository import SourceFileRecord
from data_processor.infrastructure.database.models.source_file import SourceFile


class PostgresSourceFileRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_by_id(self, source_file_id: int) -> SourceFileRecord | None:
        source_file = self._session.get(SourceFile, source_file_id)
        if source_file is None:
            return None
        return _to_source_file_record(source_file)

    def mark_status(
        self,
        *,
        source_file_id: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        source_file = self._session.get(SourceFile, source_file_id)
        if source_file is None:
            raise LookupError(f"Source file not found: {source_file_id}")

        source_file.status = status
        source_file.error_message = error_message
        source_file.updated_at = datetime.now(UTC)


def _to_source_file_record(source_file: SourceFile) -> SourceFileRecord:
    return SourceFileRecord(
        id=source_file.id,
        original_filename=source_file.original_filename,
        storage_path=source_file.storage_path,
        file_hash=source_file.file_hash,
        status=source_file.status,
        file_size_bytes=source_file.file_size_bytes,
        source_format=source_file.source_format,
        source_format_version=source_file.source_format_version,
        detected_object_name=source_file.detected_object_name,
        detected_filter_code=source_file.detected_filter_code,
        created_at=source_file.created_at,
        updated_at=source_file.updated_at,
    )
