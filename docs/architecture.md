# Architecture

The current repository is a development-stage data processor focused on local
VOTable XML ingestion, PostgreSQL persistence, and provisional visualization.

It is not yet an autonomous polling worker. That idea may return later, but the
current codebase keeps only the pieces needed for the working prototype.

## Blocks

```text
src/data_processor/
├── acquisition/  XML/VOTable acquisition from local files
├── processing/   future normalization and scientific processing routines
├── odm/          SQLAlchemy models, sessions, and repositories
└── viewer/       provisional Streamlit visual inspection tool
```

## Current Runtime Flow

```text
Local XML files -> acquisition -> odm/PostgreSQL -> viewer
```

The backend is a separate service. It should read data from PostgreSQL and
expose it through an API, but it should not execute this Python code internally.

## Database Strategy

The schema is still provisional. Because the XML files can repopulate the
database, the project currently uses SQLAlchemy metadata to create the current
prototype schema with `init-db`.

Alembic migrations are intentionally deferred until the astronomical schema is
stable enough to deserve migration history.
