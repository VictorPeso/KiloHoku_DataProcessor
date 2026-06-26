"""SQLAlchemy models used as Alembic metadata source."""

from data_processor.infrastructure.database.models.astronomical_object import AstronomicalObject
from data_processor.infrastructure.database.models.photometric_observation import (
    PhotometricObservation,
)
from data_processor.infrastructure.database.models.photometric_series import PhotometricSeries
from data_processor.infrastructure.database.models.processing_error import ProcessingError
from data_processor.infrastructure.database.models.processing_job import ProcessingJob
from data_processor.infrastructure.database.models.processing_result import ProcessingResult
from data_processor.infrastructure.database.models.processing_warning import ProcessingWarning
from data_processor.infrastructure.database.models.source_file import SourceFile

__all__ = [
    "AstronomicalObject",
    "PhotometricObservation",
    "PhotometricSeries",
    "ProcessingError",
    "ProcessingJob",
    "ProcessingResult",
    "ProcessingWarning",
    "SourceFile",
]
