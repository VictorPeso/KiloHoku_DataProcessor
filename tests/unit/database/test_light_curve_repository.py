"""Tests for database-backed light-curve read queries."""

from sqlalchemy.dialects import postgresql

from data_processor.infrastructure.database.repositories.light_curve_repository import (
    _build_light_curve_statement,
    _expand_filter_aliases,
)


def test_expand_filter_aliases_supports_ztf_filter_codes() -> None:
    assert _expand_filter_aliases(["g", "r", "i"]) == ["g", "zg", "r", "zr", "i", "zi"]


def test_light_curve_statement_filters_object_and_valid_observations() -> None:
    statement = _build_light_curve_statement(
        object_id=1,
        filter_values=["g", "zg"],
        only_valid_observations=True,
    )

    compiled = str(statement.compile(dialect=postgresql.dialect()))

    assert "astronomical_objects.id" in compiled
    assert "photometric_series.filter_code IN" in compiled
    assert "photometric_observations.catalog_flags = " in compiled
    assert "ORDER BY astronomy.photometric_series.filter_code ASC" in compiled
