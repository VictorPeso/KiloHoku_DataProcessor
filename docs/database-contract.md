# Database Contract

This document defines the initial shared PostgreSQL contract between the backend
and the autonomous data processor.

The backend and the processor run as independent containers. They do not call
each other for normal reads. PostgreSQL is the integration point:

```text
Frontend -> Backend API -> PostgreSQL <- Data Processor Worker
```

The backend should expose already imported and processed data through HTTP. The
processor should poll PostgreSQL, claim pending work, import VOTable XML files,
normalize observations, and write results back to PostgreSQL.

This is a design contract, not an implemented migration yet.

## Current Repository State

- Language: Python.
- Database target: PostgreSQL.
- Current PostgreSQL driver dependency: `psycopg`.
- ORM: SQLAlchemy.
- Migration system: Alembic.
- Astronomy schema owner: this data processor repository.
- Processing runtime: autonomous worker with polling.
- XML source format: VOTable XML with a stable internal table structure.

The real schema contract is defined by Alembic migrations in this repository.
The backend may define read-compatible entities, but it must not generate or run
migrations for astronomy-owned tables.

## Ownership Boundary

This repository should own:

- The worker polling logic.
- Job claiming and status updates needed by the processor.
- VOTable validation and import logic.
- Bulk insertion of photometric observations.
- Scientific processing outputs produced by this processor.
- Processor-facing repositories and SQL queries.

The backend repository should own:

- Public REST endpoints.
- Authentication and authorization.
- User and project ownership.
- User-facing API schemas.
- Frontend-facing query shaping.
- Migrations for backend-owned schemas such as `application`, if needed.

Shared ownership must be explicitly coordinated for:

- Table names and columns.
- Job states.
- Error codes.
- Result schema.
- Indexes used by both API reads and processor writes.

The preferred PostgreSQL schema for all astronomy-owned tables is:

```text
astronomy
```

## Initial Data Model

The database must not create one table per XML file or one table per object.
All VOTable files with the same structure should be imported into common
normalized PostgreSQL tables.

The initial model separates five concepts:

1. Astronomical objects.
2. Source files.
3. Processing jobs.
4. Photometric series.
5. Photometric observations.

Additional result and error tables are included to support processing history.

## Status Values

Use PostgreSQL enums or `CHECK` constraints. Enums are stricter; checks are
easier to evolve. For the first implementation, `CHECK` constraints are likely
sufficient.

Recommended job statuses:

```text
pending
claimed
processing
completed
completed_with_warnings
failed
cancelled
retry_pending
```

Recommended source file statuses:

```text
pending
importing
imported
failed
duplicate
unsupported
```

Recommended series statuses:

```text
pending
processing
completed
completed_with_warnings
failed
```

## Table: astronomical_objects

Represents a star or stellar system.

```sql
CREATE TABLE astronomical_objects (
    id BIGSERIAL PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL UNIQUE,
    ztf_oid BIGINT,
    mean_ra DOUBLE PRECISION,
    mean_dec DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Notes:

- `source_name` is the textual identifier, for example `ZTF17aaaacsm`.
- `ztf_oid` is the numeric catalog object identifier from the observations.
- These values are related but not interchangeable.

## Table: source_files

Represents an original XML file known to the system.

```sql
CREATE TABLE source_files (
    id BIGSERIAL PRIMARY KEY,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_hash CHAR(64) NOT NULL UNIQUE,
    file_size_bytes BIGINT,
    source_format VARCHAR(50) NOT NULL DEFAULT 'VOTable',
    source_format_version VARCHAR(20),
    detected_object_name VARCHAR(100),
    detected_filter_code VARCHAR(10),
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_source_files_status CHECK (
        status IN (
            'pending',
            'importing',
            'imported',
            'failed',
            'duplicate',
            'unsupported'
        )
    )
);
```

Notes:

- The XML content should not be stored in PostgreSQL unless a future audit
  requirement demands it.
- `storage_path` can point to a persistent volume, server filesystem path, or
  future object storage key.
- `file_hash` prevents importing the same physical file twice.

## Table: processing_jobs

Represents work claimed by the autonomous worker.

```sql
CREATE TABLE processing_jobs (
    id BIGSERIAL PRIMARY KEY,
    source_file_id BIGINT NOT NULL
        REFERENCES source_files(id)
        ON DELETE CASCADE,

    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    priority INTEGER NOT NULL DEFAULT 0,
    attempts INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,

    locked_by VARCHAR(100),
    locked_at TIMESTAMPTZ,

    progress_percent NUMERIC(5, 2) NOT NULL DEFAULT 0,
    current_step TEXT,

    started_at TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    error_code VARCHAR(100),
    error_message TEXT,

    CONSTRAINT chk_processing_jobs_status CHECK (
        status IN (
            'pending',
            'claimed',
            'processing',
            'completed',
            'completed_with_warnings',
            'failed',
            'cancelled',
            'retry_pending'
        )
    ),
    CONSTRAINT chk_processing_jobs_progress CHECK (
        progress_percent >= 0 AND progress_percent <= 100
    )
);
```

Recommended claiming query pattern:

```sql
SELECT id
FROM processing_jobs
WHERE status IN ('pending', 'retry_pending')
ORDER BY priority DESC, created_at ASC
FOR UPDATE SKIP LOCKED
LIMIT :batch_size;
```

This allows multiple processor containers to claim different jobs without
processing the same file twice.

## Table: photometric_series

Represents an imported photometric series, normally one object and one filter
from one source XML file.

```sql
CREATE TABLE photometric_series (
    id BIGSERIAL PRIMARY KEY,
    object_id BIGINT NOT NULL
        REFERENCES astronomical_objects(id)
        ON DELETE CASCADE,
    source_file_id BIGINT NOT NULL
        REFERENCES source_files(id)
        ON DELETE RESTRICT,

    filter_code VARCHAR(10) NOT NULL,
    source_filename TEXT NOT NULL,
    source_format VARCHAR(50) NOT NULL DEFAULT 'VOTable',
    source_format_version VARCHAR(20),

    observation_count INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(30) NOT NULL DEFAULT 'pending',
    processing_error TEXT,

    imported_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_photometric_series_status CHECK (
        status IN (
            'pending',
            'processing',
            'completed',
            'completed_with_warnings',
            'failed'
        )
    ),
    CONSTRAINT uq_series_object_filter_file UNIQUE (
        object_id,
        filter_code,
        source_file_id
    )
);
```

Notes:

- Multiple series may belong to the same astronomical object.
- A typical filename such as `ZTF17aaaacsm_g.xml` maps to object
  `ZTF17aaaacsm` and filter `g`, while the XML may contain `zg`.
- Filter normalization rules should live in the importer, not in API
  controllers.

## Table: photometric_observations

Each row represents one VOTable `<TR>` observation.

```sql
CREATE TABLE photometric_observations (
    id BIGSERIAL PRIMARY KEY,
    series_id BIGINT NOT NULL
        REFERENCES photometric_series(id)
        ON DELETE CASCADE,

    oid BIGINT NOT NULL,
    exposure_id INTEGER NOT NULL,

    hjd DOUBLE PRECISION NOT NULL,
    mjd DOUBLE PRECISION,

    magnitude REAL NOT NULL,
    magnitude_error REAL,
    catalog_flags INTEGER NOT NULL DEFAULT 0,
    filter_code VARCHAR(10) NOT NULL,

    ra DOUBLE PRECISION,
    dec DOUBLE PRECISION,

    chi REAL,
    sharpness REAL,

    file_fractional_day BIGINT,
    field_id INTEGER,
    ccd_id SMALLINT,
    quadrant_id SMALLINT,

    limiting_magnitude REAL,
    magnitude_zeropoint REAL,
    magnitude_zeropoint_rms REAL,

    color_coefficient REAL,
    color_coefficient_uncertainty REAL,

    exposure_time REAL,
    airmass REAL,
    program_id INTEGER,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_observation_exposure_filter UNIQUE (
        oid,
        exposure_id,
        filter_code
    )
);
```

Column mapping from VOTable:

| XML field | Database column |
| --- | --- |
| `oid` | `oid` |
| `expid` | `exposure_id` |
| `hjd` | `hjd` |
| `mjd` | `mjd` |
| `mag` | `magnitude` |
| `magerr` | `magnitude_error` |
| `catflags` | `catalog_flags` |
| `filtercode` | `filter_code` |
| `ra` | `ra` |
| `dec` | `dec` |
| `chi` | `chi` |
| `sharp` | `sharpness` |
| `filefracday` | `file_fractional_day` |
| `field` | `field_id` |
| `ccdid` | `ccd_id` |
| `qid` | `quadrant_id` |
| `limitmag` | `limiting_magnitude` |
| `magzp` | `magnitude_zeropoint` |
| `magzprms` | `magnitude_zeropoint_rms` |
| `clrcoeff` | `color_coefficient` |
| `clrcounc` | `color_coefficient_uncertainty` |
| `exptime` | `exposure_time` |
| `airmass` | `airmass` |
| `programid` | `program_id` |

Numeric rules:

- Use `DOUBLE PRECISION` for `hjd`, `mjd`, `ra`, and `dec`.
- Use `REAL` for magnitudes and instrumental floating-point values.
- Use `BIGINT` for large identifiers such as `oid` and `filefracday`.
- Do not store HJD or MJD as `TIMESTAMP`.

## Table: processing_errors

Stores structured errors without relying only on a text column in
`processing_jobs`.

```sql
CREATE TABLE processing_errors (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT
        REFERENCES processing_jobs(id)
        ON DELETE CASCADE,
    source_file_id BIGINT
        REFERENCES source_files(id)
        ON DELETE CASCADE,
    series_id BIGINT
        REFERENCES photometric_series(id)
        ON DELETE CASCADE,

    error_code VARCHAR(100) NOT NULL,
    error_message TEXT NOT NULL,
    error_details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Table: processing_warnings

Stores non-fatal issues found during import or processing.

```sql
CREATE TABLE processing_warnings (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT
        REFERENCES processing_jobs(id)
        ON DELETE CASCADE,
    source_file_id BIGINT
        REFERENCES source_files(id)
        ON DELETE CASCADE,
    series_id BIGINT
        REFERENCES photometric_series(id)
        ON DELETE CASCADE,

    warning_code VARCHAR(100) NOT NULL,
    warning_message TEXT NOT NULL,
    warning_details JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

## Table: processing_results

Stores job-level outputs or references to generated artifacts.

```sql
CREATE TABLE processing_results (
    id BIGSERIAL PRIMARY KEY,
    job_id BIGINT NOT NULL
        REFERENCES processing_jobs(id)
        ON DELETE CASCADE,
    series_id BIGINT
        REFERENCES photometric_series(id)
        ON DELETE CASCADE,

    result_type VARCHAR(100) NOT NULL,
    result_version VARCHAR(50),
    result_payload JSONB,
    artifact_path TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

Notes:

- Original imported observations should not be overwritten by calculated
  results.
- Future algorithm outputs can be stored here first, then promoted to dedicated
  tables when their schema stabilizes.

## Recommended Indexes

```sql
CREATE INDEX idx_source_files_status_created
ON source_files (status, created_at);

CREATE INDEX idx_processing_jobs_status_priority_created
ON processing_jobs (status, priority DESC, created_at);

CREATE INDEX idx_processing_jobs_locked_at
ON processing_jobs (locked_at)
WHERE status IN ('claimed', 'processing');

CREATE INDEX idx_series_object_filter
ON photometric_series (object_id, filter_code);

CREATE INDEX idx_observations_series_hjd
ON photometric_observations (series_id, hjd);

CREATE INDEX idx_observations_oid_filter_hjd
ON photometric_observations (oid, filter_code, hjd);

CREATE INDEX idx_observations_valid_series_hjd
ON photometric_observations (series_id, hjd)
WHERE catalog_flags = 0;
```

Avoid adding many more indexes until real backend API queries and processing
queries are known.

## Typical Light Curve Query

```sql
SELECT
    observation.hjd,
    observation.magnitude,
    observation.magnitude_error
FROM photometric_observations AS observation
JOIN photometric_series AS series
    ON series.id = observation.series_id
JOIN astronomical_objects AS object
    ON object.id = series.object_id
WHERE object.source_name = 'ZTF17aaaacsm'
  AND series.filter_code = 'zg'
  AND observation.catalog_flags = 0
ORDER BY observation.hjd;
```

This should return data ready for Python, NumPy, pandas, Astropy, or frontend
visualization through the backend API.

## Import Strategy

The processor should:

1. Poll `processing_jobs` for pending work.
2. Claim jobs using a transaction and `FOR UPDATE SKIP LOCKED`.
3. Mark the job and source file as being processed.
4. Detect and validate VOTable format and namespace.
5. Read `<FIELD>` definitions.
6. Verify required fields are present.
7. Extract object name and filter from filename and/or XML values.
8. Create or fetch `astronomical_objects`.
9. Create or fetch `photometric_series`.
10. Stream `<TR>` rows where practical.
11. Convert each row to typed observation records.
12. Insert observations in batches, not one by one.
13. Update `observation_count`.
14. Store errors and warnings in structured tables.
15. Mark the job as completed, completed with warnings, failed, or retryable.

The import should avoid leaving partially loaded series. This can be done with a
single transaction for moderate files, or with staged/batch strategies for very
large files.

## VOTable XML Requirements

The importer must handle XML namespaces explicitly. VOTable files may use a
default namespace such as:

```xml
xmlns="http://www.ivoa.net/xml/VOTable/v1.3"
```

Do not rely on simple namespace-unaware searches such as:

```python
root.findall("TR")
```

The reader should use namespace-aware parsing or a robust VOTable-compatible
library. Astropy may be considered later, but persistence should not depend on
Astropy-specific internal structures.

## Performance Rules

- Do not perform one `INSERT` per observation.
- Use batched inserts, PostgreSQL `COPY`, or another bulk strategy.
- Stream large XML files when possible.
- Do not require pandas for the import path.
- Use pandas for later analysis steps, not as the mandatory persistence model.
- Avoid unnecessary copies of large observation collections.
- Release XML parser resources after each file.

## Future Extensions

The design should allow future tables such as:

- `processing_runs`
- `algorithm_versions`
- `light_curve_features`
- `classifications`
- `model_predictions`
- `normalized_light_curves`

Future scientific outputs should preserve:

- Original imported data.
- Cleaned or transformed data.
- Algorithm version.
- Parameters used.
- Execution timestamp.
- Quality metrics.

## Implementation Plan

Files to create later:

- `src/data_processor/infrastructure/database/postgres_astronomical_object_repository.py`
- `src/data_processor/infrastructure/database/postgres_photometric_series_repository.py`
- `src/data_processor/infrastructure/database/postgres_photometric_observation_repository.py`
- `src/data_processor/infrastructure/xml/votable_reader.py`
- `src/data_processor/infrastructure/xml/votable_validator.py`
- `src/data_processor/infrastructure/xml/mappers/votable_observation_mapper.py`

Files to modify later:

- `src/data_processor/core/domain/models/astronomical_source.py`
- `src/data_processor/core/domain/models/light_curve.py`
- `src/data_processor/core/domain/models/observation.py`
- `src/data_processor/core/domain/models/processing_job.py`
- `src/data_processor/core/application/ports/*.py`
- `src/data_processor/worker/job_claiming.py`
- `src/data_processor/worker/job_runner.py`

Tests to add later:

- Unit tests for VOTable field validation.
- Unit tests for filename object/filter detection.
- Unit tests for observation type mapping.
- Integration tests for job claiming with PostgreSQL.
- Integration tests for importing a small VOTable fixture.
- Performance smoke tests for large XML streaming and batch insertion.

## Decisions Still Open

- Whether file upload records are created by the backend or discovered by the
  processor from a watched storage location.
- Exact policy for duplicate files with different filenames but the same hash.
- Whether `filter_code` should preserve XML values like `zg` or normalize to
  file suffix values like `g`.
- Whether completed failed partial imports should be rolled back entirely or
  stored with an explicit failed status.
