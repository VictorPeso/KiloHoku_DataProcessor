"""Small VOTable reader for local light-curve visualization."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from lxml import etree

LIGHT_CURVE_COLUMNS = ["hjd", "mjd", "mag", "magerr", "filtercode", "oid", "catflags"]
NUMERIC_COLUMNS = [
    "oid",
    "expid",
    "hjd",
    "mjd",
    "mag",
    "magerr",
    "catflags",
    "ra",
    "dec",
    "chi",
    "sharp",
    "filefracday",
    "field",
    "ccdid",
    "qid",
    "limitmag",
    "magzp",
    "magzprms",
    "clrcoeff",
    "clrcounc",
    "exptime",
    "airmass",
    "programid",
]


@dataclass(frozen=True)
class VOTableLightCurve:
    path: Path
    object_name: str
    file_filter_code: str | None
    dataframe: pd.DataFrame


def read_votable_light_curve(path: str | Path) -> VOTableLightCurve:
    resolved_path = Path(path)
    root = etree.parse(str(resolved_path)).getroot()

    field_names = _extract_field_names(root)
    rows = _extract_rows(root, field_names)
    dataframe = pd.DataFrame(rows, columns=field_names)
    dataframe = _convert_known_columns(dataframe)

    object_name, file_filter_code = infer_object_and_filter_from_filename(resolved_path.name)
    return VOTableLightCurve(
        path=resolved_path,
        object_name=object_name,
        file_filter_code=file_filter_code,
        dataframe=dataframe,
    )


def infer_object_and_filter_from_filename(filename: str) -> tuple[str, str | None]:
    stem = Path(filename).stem
    if "_" not in stem:
        return stem, None

    object_name, filter_code = stem.rsplit("_", maxsplit=1)
    return object_name, filter_code


def _extract_field_names(root: etree._Element) -> list[str]:
    fields = root.xpath(".//*[local-name()='FIELD']")
    field_names = [field.get("name") or field.get("ID") for field in fields]
    return [field_name for field_name in field_names if field_name]


def _extract_rows(root: etree._Element, field_names: list[str]) -> list[dict[str, Any]]:
    table_rows = root.xpath(".//*[local-name()='TR']")
    rows: list[dict[str, Any]] = []

    for table_row in table_rows:
        cells = table_row.xpath("./*[local-name()='TD']")
        values = [(cell.text or "").strip() for cell in cells]
        rows.append(dict(zip(field_names, values, strict=False)))

    return rows


def _convert_known_columns(dataframe: pd.DataFrame) -> pd.DataFrame:
    converted = dataframe.copy()
    for column in NUMERIC_COLUMNS:
        if column in converted.columns:
            converted[column] = pd.to_numeric(converted[column], errors="coerce")
    return converted
