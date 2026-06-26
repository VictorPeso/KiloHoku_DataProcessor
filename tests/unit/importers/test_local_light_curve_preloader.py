"""Tests for the provisional local light-curve preloader."""

import pandas as pd

from data_processor.infrastructure.importers.local_light_curve_preloader import (
    _build_observation_rows,
)


def test_build_observation_rows_maps_votable_fields() -> None:
    dataframe = pd.DataFrame(
        [
            {
                "oid": 123,
                "expid": 456,
                "hjd": 2459000.5,
                "mjd": 59000.1,
                "mag": 18.2,
                "magerr": 0.1,
                "catflags": 0,
                "filtercode": "zg",
                "ra": 1.5,
                "dec": -2.5,
            },
        ],
    )

    rows = _build_observation_rows(series_id=99, dataframe=dataframe)

    assert rows == [
        {
            "series_id": 99,
            "oid": 123,
            "exposure_id": 456,
            "hjd": 2459000.5,
            "mjd": 59000.1,
            "magnitude": 18.2,
            "magnitude_error": 0.1,
            "catalog_flags": 0,
            "filter_code": "zg",
            "ra": 1.5,
            "dec": -2.5,
            "chi": None,
            "sharpness": None,
            "file_fractional_day": None,
            "field_id": None,
            "ccd_id": None,
            "quadrant_id": None,
            "limiting_magnitude": None,
            "magnitude_zeropoint": None,
            "magnitude_zeropoint_rms": None,
            "color_coefficient": None,
            "color_coefficient_uncertainty": None,
            "exposure_time": None,
            "airmass": None,
            "program_id": None,
        },
    ]
