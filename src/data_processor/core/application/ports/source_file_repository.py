"""Port for locating source files or source records to process."""

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SourceFileRecord:
    id: int
    original_filename: str
    storage_path: str
    file_hash: str
    status: str
    file_size_bytes: int | None
    source_format: str
    source_format_version: str | None
    detected_object_name: str | None
    detected_filter_code: str | None
    created_at: datetime
    updated_at: datetime


class SourceFileRepository(Protocol):
    def get_by_id(self, source_file_id: int) -> SourceFileRecord | None:
        """Return a source file by id."""

    def mark_status(
        self,
        *,
        source_file_id: int,
        status: str,
        error_message: str | None = None,
    ) -> None:
        """Update source file processing status."""
