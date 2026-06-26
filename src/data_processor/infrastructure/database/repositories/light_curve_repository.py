"""Read-only repository for local light-curve visualization."""

from dataclasses import dataclass

import pandas as pd
from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from data_processor.infrastructure.database.models.astronomical_object import AstronomicalObject
from data_processor.infrastructure.database.models.photometric_observation import (
    PhotometricObservation,
)
from data_processor.infrastructure.database.models.photometric_series import PhotometricSeries

FILTER_ALIASES = {
    "g": ("g", "zg"),
    "r": ("r", "zr"),
    "i": ("i", "zi"),
}


@dataclass(frozen=True)
class AstronomicalObjectSummary:
    id: int
    source_name: str
    ztf_oid: int | None
    series_count: int
    observation_count: int


class LightCurveReadRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_ztf_objects(self) -> list[AstronomicalObjectSummary]:
        statement = (
            select(
                AstronomicalObject.id.label("object_id"),
                AstronomicalObject.source_name.label("source_name"),
                AstronomicalObject.ztf_oid.label("ztf_oid"),
                PhotometricSeries.id.label("series_id"),
                PhotometricSeries.observation_count.label("observation_count"),
            )
            .join(
                PhotometricSeries,
                PhotometricSeries.object_id == AstronomicalObject.id,
                isouter=True,
            )
            .where(AstronomicalObject.source_name.like("ZTF%"))
            .order_by(AstronomicalObject.source_name.asc())
        )

        summaries: dict[int, AstronomicalObjectSummary] = {}
        series_ids_by_object: dict[int, set[int]] = {}

        for row in self._session.execute(statement):
            object_id = row.object_id
            series_ids_by_object.setdefault(object_id, set())
            if row.series_id is not None:
                series_ids_by_object[object_id].add(row.series_id)

            previous = summaries.get(object_id)
            observation_count = int(row.observation_count or 0)
            summaries[object_id] = AstronomicalObjectSummary(
                id=object_id,
                source_name=row.source_name,
                ztf_oid=row.ztf_oid,
                series_count=len(series_ids_by_object[object_id]),
                observation_count=(previous.observation_count if previous else 0)
                + observation_count,
            )

        return list(summaries.values())

    def get_object_name(self, object_id: int) -> str | None:
        return self._session.scalar(
            select(AstronomicalObject.source_name).where(AstronomicalObject.id == object_id),
        )

    def list_available_filters(self, object_id: int) -> list[str]:
        statement = (
            select(PhotometricSeries.filter_code)
            .where(PhotometricSeries.object_id == object_id)
            .distinct()
            .order_by(PhotometricSeries.filter_code.asc())
        )
        raw_filters = list(self._session.scalars(statement))
        normalized = {_normalize_filter_code(filter_code) for filter_code in raw_filters}
        return [filter_code for filter_code in ["g", "r", "i"] if filter_code in normalized]

    def load_light_curve(
        self,
        *,
        object_id: int,
        selected_filters: list[str],
        only_valid_observations: bool,
    ) -> pd.DataFrame:
        filter_values = _expand_filter_aliases(selected_filters)
        statement = _build_light_curve_statement(
            object_id=object_id,
            filter_values=filter_values,
            only_valid_observations=only_valid_observations,
        )
        rows = self._session.execute(statement).mappings().all()
        return pd.DataFrame(rows)


def _build_light_curve_statement(
    *,
    object_id: int,
    filter_values: list[str],
    only_valid_observations: bool,
) -> Select[tuple]:
    statement = (
        select(
            AstronomicalObject.source_name.label("object_name"),
            PhotometricSeries.filter_code.label("series_filter_code"),
            PhotometricSeries.source_filename,
            PhotometricObservation.hjd,
            PhotometricObservation.mjd,
            PhotometricObservation.magnitude,
            PhotometricObservation.magnitude_error,
            PhotometricObservation.catalog_flags,
            PhotometricObservation.filter_code.label("observation_filter_code"),
            PhotometricObservation.oid,
            PhotometricObservation.exposure_id,
        )
        .join(PhotometricSeries, PhotometricSeries.object_id == AstronomicalObject.id)
        .join(PhotometricObservation, PhotometricObservation.series_id == PhotometricSeries.id)
        .where(AstronomicalObject.id == object_id)
        .where(PhotometricSeries.filter_code.in_(filter_values))
        .order_by(PhotometricSeries.filter_code.asc(), PhotometricObservation.hjd.asc())
    )

    if only_valid_observations:
        statement = statement.where(PhotometricObservation.catalog_flags == 0)

    return statement


def _expand_filter_aliases(selected_filters: list[str]) -> list[str]:
    values: list[str] = []
    for filter_code in selected_filters:
        values.extend(FILTER_ALIASES.get(filter_code, (filter_code,)))
    return values


def _normalize_filter_code(filter_code: str) -> str:
    for normalized, aliases in FILTER_ALIASES.items():
        if filter_code in aliases:
            return normalized
    return filter_code
