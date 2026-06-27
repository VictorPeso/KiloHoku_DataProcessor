"""Provisional importer from local VOTable XML files into PostgreSQL."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from tqdm.auto import tqdm

from data_processor.acquisition.xml.votable_light_curve_reader import (
    VOTableLightCurve,
    read_votable_light_curve,
)
from data_processor.odm.database.models.astronomical_object import AstronomicalObject
from data_processor.odm.database.models.photometric_observation import (
    PhotometricObservation,
)
from data_processor.odm.database.models.photometric_series import PhotometricSeries
from data_processor.odm.database.models.source_file import SourceFile
from data_processor.odm.database.session import session_scope


@dataclass(frozen=True)
class PreloadSummary:
    discovered_files: int = 0
    imported_files: int = 0
    skipped_files: int = 0
    failed_files: int = 0
    inserted_observations: int = 0

    def to_message(self) -> str:
        return (
            "Preload finished: "
            f"{self.discovered_files} discovered, "
            f"{self.imported_files} imported, "
            f"{self.skipped_files} skipped, "
            f"{self.failed_files} failed, "
            f"{self.inserted_observations} observations prepared."
        )


class LocalLightCurvePreloader:
    def preload_folder(
        self,
        *,
        folder: Path,
        recursive: bool = False,
        limit: int | None = None,
        dry_run: bool = False,
        show_progress: bool = True,
    ) -> PreloadSummary:
        xml_files = _find_xml_files(folder, recursive=recursive)
        if limit is not None:
            xml_files = xml_files[:limit]

        if dry_run:
            return PreloadSummary(discovered_files=len(xml_files))

        imported_files = 0
        skipped_files = 0
        failed_files = 0
        inserted_observations = 0

        progress = tqdm(
            xml_files,
            desc="Importing light curves",
            unit="file",
            disable=not show_progress,
        )

        for xml_file in progress:
            try:
                with session_scope() as session:
                    result = self.preload_file(session=session, path=xml_file)
                    if result == "imported":
                        imported_files += 1
                        inserted_observations += len(read_votable_light_curve(xml_file).dataframe)
                    else:
                        skipped_files += 1
            except Exception:
                failed_files += 1

        return PreloadSummary(
            discovered_files=len(xml_files),
            imported_files=imported_files,
            skipped_files=skipped_files,
            failed_files=failed_files,
            inserted_observations=inserted_observations,
        )

    def preload_file(self, *, session: Session, path: Path) -> str:
        file_hash = _calculate_sha256(path)
        existing_source_file_id = session.scalar(
            select(SourceFile.id).where(SourceFile.file_hash == file_hash),
        )
        if existing_source_file_id is not None:
            return "skipped"

        curve = read_votable_light_curve(path)
        dataframe = curve.dataframe
        _validate_required_columns(dataframe)

        astronomical_object = _get_or_create_astronomical_object(session, curve)
        source_file = _create_source_file(session, path=path, file_hash=file_hash, curve=curve)
        session.flush()

        series = PhotometricSeries(
            object_id=astronomical_object.id,
            source_file_id=source_file.id,
            filter_code=_series_filter_code(curve),
            source_filename=path.name,
            source_format="VOTable",
            source_format_version="1.3",
            observation_count=len(dataframe),
            status="completed",
        )
        session.add(series)
        session.flush()

        observation_rows = _build_observation_rows(series_id=series.id, dataframe=dataframe)
        if observation_rows:
            statement = insert(PhotometricObservation).values(observation_rows)
            statement = statement.on_conflict_do_nothing(
                index_elements=["oid", "exposure_id", "filter_code"],
            )
            session.execute(statement)

        source_file.status = "imported"
        return "imported"


def _find_xml_files(folder: Path, *, recursive: bool) -> list[Path]:
    if not folder.exists() or not folder.is_dir():
        raise FileNotFoundError(f"Light-curve folder not found: {folder}")

    pattern = "**/*.xml" if recursive else "*.xml"
    return sorted(folder.glob(pattern))


def _calculate_sha256(path: Path) -> str:
    digest = sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_required_columns(dataframe: pd.DataFrame) -> None:
    required_columns = {"oid", "expid", "hjd", "mag", "filtercode"}
    missing_columns = required_columns.difference(dataframe.columns)
    if missing_columns:
        raise ValueError(f"Missing required VOTable columns: {sorted(missing_columns)}")


def _get_or_create_astronomical_object(
    session: Session,
    curve: VOTableLightCurve,
) -> AstronomicalObject:
    astronomical_object = session.scalar(
        select(AstronomicalObject).where(AstronomicalObject.source_name == curve.object_name),
    )
    dataframe = curve.dataframe

    if astronomical_object is None:
        astronomical_object = AstronomicalObject(source_name=curve.object_name)
        session.add(astronomical_object)

    if "oid" in dataframe.columns and not dataframe["oid"].dropna().empty:
        astronomical_object.ztf_oid = int(dataframe["oid"].dropna().iloc[0])
    if "ra" in dataframe.columns and not dataframe["ra"].dropna().empty:
        astronomical_object.mean_ra = float(dataframe["ra"].mean())
    if "dec" in dataframe.columns and not dataframe["dec"].dropna().empty:
        astronomical_object.mean_dec = float(dataframe["dec"].mean())

    session.flush()
    return astronomical_object


def _create_source_file(
    session: Session,
    *,
    path: Path,
    file_hash: str,
    curve: VOTableLightCurve,
) -> SourceFile:
    source_file = SourceFile(
        original_filename=path.name,
        storage_path=str(path),
        file_hash=file_hash,
        file_size_bytes=path.stat().st_size,
        source_format="VOTable",
        source_format_version="1.3",
        detected_object_name=curve.object_name,
        detected_filter_code=curve.file_filter_code,
        status="importing",
    )
    session.add(source_file)
    return source_file


def _series_filter_code(curve: VOTableLightCurve) -> str:
    dataframe = curve.dataframe
    if "filtercode" in dataframe.columns and not dataframe["filtercode"].dropna().empty:
        return str(dataframe["filtercode"].dropna().iloc[0])
    return curve.file_filter_code or "unknown"


def _build_observation_rows(*, series_id: int, dataframe: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for record in dataframe.to_dict(orient="records"):
        rows.append(
            {
                "series_id": series_id,
                "oid": _required_int(record, "oid"),
                "exposure_id": _required_int(record, "expid"),
                "hjd": _required_float(record, "hjd"),
                "mjd": _optional_float(record, "mjd"),
                "magnitude": _required_float(record, "mag"),
                "magnitude_error": _optional_float(record, "magerr"),
                "catalog_flags": _optional_int(record, "catflags") or 0,
                "filter_code": str(record["filtercode"]),
                "ra": _optional_float(record, "ra"),
                "dec": _optional_float(record, "dec"),
                "chi": _optional_float(record, "chi"),
                "sharpness": _optional_float(record, "sharp"),
                "file_fractional_day": _optional_int(record, "filefracday"),
                "field_id": _optional_int(record, "field"),
                "ccd_id": _optional_int(record, "ccdid"),
                "quadrant_id": _optional_int(record, "qid"),
                "limiting_magnitude": _optional_float(record, "limitmag"),
                "magnitude_zeropoint": _optional_float(record, "magzp"),
                "magnitude_zeropoint_rms": _optional_float(record, "magzprms"),
                "color_coefficient": _optional_float(record, "clrcoeff"),
                "color_coefficient_uncertainty": _optional_float(record, "clrcounc"),
                "exposure_time": _optional_float(record, "exptime"),
                "airmass": _optional_float(record, "airmass"),
                "program_id": _optional_int(record, "programid"),
            },
        )
    return rows


def _required_int(record: dict[str, Any], key: str) -> int:
    value = _value_or_none(record.get(key))
    if value is None:
        raise ValueError(f"Missing required integer value: {key}")
    return int(value)


def _optional_int(record: dict[str, Any], key: str) -> int | None:
    value = _value_or_none(record.get(key))
    return None if value is None else int(value)


def _required_float(record: dict[str, Any], key: str) -> float:
    value = _value_or_none(record.get(key))
    if value is None:
        raise ValueError(f"Missing required float value: {key}")
    return float(value)


def _optional_float(record: dict[str, Any], key: str) -> float | None:
    value = _value_or_none(record.get(key))
    return None if value is None else float(value)


def _value_or_none(value: Any) -> Any:
    if value is None:
        return None
    if pd.isna(value):
        return None
    return value
