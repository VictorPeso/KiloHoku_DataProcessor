"""Create initial astronomy tables.

Revision ID: 20260626_0002
Revises: 20260626_0001
Create Date: 2026-06-26
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260626_0002"
down_revision: str | None = "20260626_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SCHEMA = "astronomy"


def upgrade() -> None:
    op.create_table(
        "astronomical_objects",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("ztf_oid", sa.BigInteger(), nullable=True),
        sa.Column("mean_ra", sa.Double(), nullable=True),
        sa.Column("mean_dec", sa.Double(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id", name="pk_astronomical_objects"),
        sa.UniqueConstraint("source_name", name="uq_astronomical_objects_source_name"),
        schema=SCHEMA,
    )

    op.create_table(
        "source_files",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("file_hash", sa.String(length=64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("source_format", sa.String(length=50), server_default="VOTable", nullable=False),
        sa.Column("source_format_version", sa.String(length=20), nullable=True),
        sa.Column("detected_object_name", sa.String(length=100), nullable=True),
        sa.Column("detected_filter_code", sa.String(length=10), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'importing', 'imported', 'failed', 'duplicate', 'unsupported')",
            name=op.f("ck_source_files_source_files_status"),
        ),
        sa.PrimaryKeyConstraint("id", name="pk_source_files"),
        sa.UniqueConstraint("file_hash", name="uq_source_files_file_hash"),
        schema=SCHEMA,
    )

    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("source_file_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("priority", sa.Integer(), server_default="0", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("max_attempts", sa.Integer(), server_default="3", nullable=False),
        sa.Column("locked_by", sa.String(length=100), nullable=True),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "progress_percent", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False
        ),
        sa.Column("current_step", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("error_code", sa.String(length=100), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.CheckConstraint(
            (
                "status IN ('pending', 'claimed', 'processing', 'completed', "
                "'completed_with_warnings', 'failed', 'cancelled', 'retry_pending')"
            ),
            name=op.f("ck_processing_jobs_processing_jobs_status"),
        ),
        sa.CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name=op.f("ck_processing_jobs_processing_jobs_progress"),
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            [f"{SCHEMA}.source_files.id"],
            name="fk_processing_jobs_source_file_id_source_files",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processing_jobs"),
        schema=SCHEMA,
    )

    op.create_table(
        "photometric_series",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("object_id", sa.BigInteger(), nullable=False),
        sa.Column("source_file_id", sa.BigInteger(), nullable=False),
        sa.Column("filter_code", sa.String(length=10), nullable=False),
        sa.Column("source_filename", sa.Text(), nullable=False),
        sa.Column("source_format", sa.String(length=50), server_default="VOTable", nullable=False),
        sa.Column("source_format_version", sa.String(length=20), nullable=True),
        sa.Column("observation_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=30), server_default="pending", nullable=False),
        sa.Column("processing_error", sa.Text(), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'processing', 'completed', 'completed_with_warnings', 'failed')",
            name=op.f("ck_photometric_series_photometric_series_status"),
        ),
        sa.ForeignKeyConstraint(
            ["object_id"],
            [f"{SCHEMA}.astronomical_objects.id"],
            name="fk_photometric_series_object_id_astronomical_objects",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            [f"{SCHEMA}.source_files.id"],
            name="fk_photometric_series_source_file_id_source_files",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_photometric_series"),
        sa.UniqueConstraint(
            "object_id",
            "filter_code",
            "source_file_id",
            name="uq_series_object_filter_file",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "photometric_observations",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("series_id", sa.BigInteger(), nullable=False),
        sa.Column("oid", sa.BigInteger(), nullable=False),
        sa.Column("exposure_id", sa.Integer(), nullable=False),
        sa.Column("hjd", sa.Double(), nullable=False),
        sa.Column("mjd", sa.Double(), nullable=True),
        sa.Column("magnitude", sa.REAL(), nullable=False),
        sa.Column("magnitude_error", sa.REAL(), nullable=True),
        sa.Column("catalog_flags", sa.Integer(), server_default="0", nullable=False),
        sa.Column("filter_code", sa.String(length=10), nullable=False),
        sa.Column("ra", sa.Double(), nullable=True),
        sa.Column("dec", sa.Double(), nullable=True),
        sa.Column("chi", sa.REAL(), nullable=True),
        sa.Column("sharpness", sa.REAL(), nullable=True),
        sa.Column("file_fractional_day", sa.BigInteger(), nullable=True),
        sa.Column("field_id", sa.Integer(), nullable=True),
        sa.Column("ccd_id", sa.SmallInteger(), nullable=True),
        sa.Column("quadrant_id", sa.SmallInteger(), nullable=True),
        sa.Column("limiting_magnitude", sa.REAL(), nullable=True),
        sa.Column("magnitude_zeropoint", sa.REAL(), nullable=True),
        sa.Column("magnitude_zeropoint_rms", sa.REAL(), nullable=True),
        sa.Column("color_coefficient", sa.REAL(), nullable=True),
        sa.Column("color_coefficient_uncertainty", sa.REAL(), nullable=True),
        sa.Column("exposure_time", sa.REAL(), nullable=True),
        sa.Column("airmass", sa.REAL(), nullable=True),
        sa.Column("program_id", sa.Integer(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["series_id"],
            [f"{SCHEMA}.photometric_series.id"],
            name="fk_photometric_observations_series_id_photometric_series",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_photometric_observations"),
        sa.UniqueConstraint(
            "oid",
            "exposure_id",
            "filter_code",
            name="uq_observation_exposure_filter",
        ),
        schema=SCHEMA,
    )

    op.create_table(
        "processing_errors",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=True),
        sa.Column("source_file_id", sa.BigInteger(), nullable=True),
        sa.Column("series_id", sa.BigInteger(), nullable=True),
        sa.Column("error_code", sa.String(length=100), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("error_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.processing_jobs.id"],
            name="fk_processing_errors_job_id_processing_jobs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            [f"{SCHEMA}.source_files.id"],
            name="fk_processing_errors_source_file_id_source_files",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["series_id"],
            [f"{SCHEMA}.photometric_series.id"],
            name="fk_processing_errors_series_id_photometric_series",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processing_errors"),
        schema=SCHEMA,
    )

    op.create_table(
        "processing_warnings",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=True),
        sa.Column("source_file_id", sa.BigInteger(), nullable=True),
        sa.Column("series_id", sa.BigInteger(), nullable=True),
        sa.Column("warning_code", sa.String(length=100), nullable=False),
        sa.Column("warning_message", sa.Text(), nullable=False),
        sa.Column("warning_details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.processing_jobs.id"],
            name="fk_processing_warnings_job_id_processing_jobs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["source_file_id"],
            [f"{SCHEMA}.source_files.id"],
            name="fk_processing_warnings_source_file_id_source_files",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["series_id"],
            [f"{SCHEMA}.photometric_series.id"],
            name="fk_processing_warnings_series_id_photometric_series",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processing_warnings"),
        schema=SCHEMA,
    )

    op.create_table(
        "processing_results",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("job_id", sa.BigInteger(), nullable=False),
        sa.Column("series_id", sa.BigInteger(), nullable=True),
        sa.Column("result_type", sa.String(length=100), nullable=False),
        sa.Column("result_version", sa.String(length=50), nullable=True),
        sa.Column("result_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("artifact_path", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["job_id"],
            [f"{SCHEMA}.processing_jobs.id"],
            name="fk_processing_results_job_id_processing_jobs",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["series_id"],
            [f"{SCHEMA}.photometric_series.id"],
            name="fk_processing_results_series_id_photometric_series",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_processing_results"),
        schema=SCHEMA,
    )

    op.create_index(
        "idx_source_files_status_created",
        "source_files",
        ["status", "created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_processing_jobs_status_priority_created",
        "processing_jobs",
        ["status", sa.text("priority DESC"), "created_at"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_processing_jobs_locked_at",
        "processing_jobs",
        ["locked_at"],
        unique=False,
        schema=SCHEMA,
        postgresql_where=sa.text("status IN ('claimed', 'processing')"),
    )
    op.create_index(
        "idx_series_object_filter",
        "photometric_series",
        ["object_id", "filter_code"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_observations_series_hjd",
        "photometric_observations",
        ["series_id", "hjd"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_observations_oid_filter_hjd",
        "photometric_observations",
        ["oid", "filter_code", "hjd"],
        schema=SCHEMA,
    )
    op.create_index(
        "idx_observations_valid_series_hjd",
        "photometric_observations",
        ["series_id", "hjd"],
        schema=SCHEMA,
        postgresql_where=sa.text("catalog_flags = 0"),
    )


def downgrade() -> None:
    op.drop_table("processing_results", schema=SCHEMA)
    op.drop_table("processing_warnings", schema=SCHEMA)
    op.drop_table("processing_errors", schema=SCHEMA)
    op.drop_table("photometric_observations", schema=SCHEMA)
    op.drop_table("photometric_series", schema=SCHEMA)
    op.drop_table("processing_jobs", schema=SCHEMA)
    op.drop_table("source_files", schema=SCHEMA)
    op.drop_table("astronomical_objects", schema=SCHEMA)
