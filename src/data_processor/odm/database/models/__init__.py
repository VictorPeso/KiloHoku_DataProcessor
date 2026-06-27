"""SQLAlchemy models for the current prototype astronomy schema."""

from data_processor.odm.database.models.astronomical_object import AstronomicalObject
from data_processor.odm.database.models.photometric_observation import (
    PhotometricObservation,
)
from data_processor.odm.database.models.photometric_series import PhotometricSeries
from data_processor.odm.database.models.source_file import SourceFile

__all__ = [
    "AstronomicalObject",
    "PhotometricObservation",
    "PhotometricSeries",
    "SourceFile",
]
