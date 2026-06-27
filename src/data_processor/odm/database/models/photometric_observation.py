"""SQLAlchemy model for photometric observations."""

from datetime import datetime

from sqlalchemy import (
    REAL,
    BigInteger,
    DateTime,
    Double,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from data_processor.odm.database.base import Base
from data_processor.odm.database.models._schema import ASTRONOMY_SCHEMA


class PhotometricObservation(Base):
    __tablename__ = "photometric_observations"
    __table_args__ = (
        UniqueConstraint(
            "oid", "exposure_id", "filter_code", name="uq_observation_exposure_filter"
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    series_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey(f"{ASTRONOMY_SCHEMA}.photometric_series.id", ondelete="CASCADE"),
        nullable=False,
    )
    oid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    exposure_id: Mapped[int] = mapped_column(Integer, nullable=False)
    hjd: Mapped[float] = mapped_column(Double, nullable=False)
    mjd: Mapped[float | None] = mapped_column(Double)
    magnitude: Mapped[float] = mapped_column(REAL, nullable=False)
    magnitude_error: Mapped[float | None] = mapped_column(REAL)
    catalog_flags: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    filter_code: Mapped[str] = mapped_column(String(10), nullable=False)
    ra: Mapped[float | None] = mapped_column(Double)
    dec: Mapped[float | None] = mapped_column(Double)
    chi: Mapped[float | None] = mapped_column(REAL)
    sharpness: Mapped[float | None] = mapped_column(REAL)
    file_fractional_day: Mapped[int | None] = mapped_column(BigInteger)
    field_id: Mapped[int | None] = mapped_column(Integer)
    ccd_id: Mapped[int | None] = mapped_column(SmallInteger)
    quadrant_id: Mapped[int | None] = mapped_column(SmallInteger)
    limiting_magnitude: Mapped[float | None] = mapped_column(REAL)
    magnitude_zeropoint: Mapped[float | None] = mapped_column(REAL)
    magnitude_zeropoint_rms: Mapped[float | None] = mapped_column(REAL)
    color_coefficient: Mapped[float | None] = mapped_column(REAL)
    color_coefficient_uncertainty: Mapped[float | None] = mapped_column(REAL)
    exposure_time: Mapped[float | None] = mapped_column(REAL)
    airmass: Mapped[float | None] = mapped_column(REAL)
    program_id: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
