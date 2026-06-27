# Database Contract

This document describes the current prototype PostgreSQL contract used by the
local importer and the provisional viewer.

The schema is not final. For now, the XML/VOTable files are considered the
rebuildable source of truth, so the project does not keep Alembic migration
history yet.

## Schema

Astronomical tables live in the PostgreSQL schema configured by:

```text
DATABASE_SCHEMA=astronomy
```

Create the current prototype schema with:

```powershell
init-db
```

Internally this calls SQLAlchemy `Base.metadata.create_all()` for the current
models. This is acceptable for the current prototype stage; it should be
replaced by Alembic once the schema stabilizes.

## Current Tables

The active prototype uses four tables:

- `astronomy.source_files`: imported XML/VOTable file metadata.
- `astronomy.astronomical_objects`: unique astronomical objects such as `ZTF*`.
- `astronomy.photometric_series`: one object/filter/file series.
- `astronomy.photometric_observations`: individual photometric measurements.

## Ownership

This repository owns the astronomical schema while the data model is being
explored.

The backend may read these tables, but should not generate migrations or alter
them automatically. If the backend later needs user/session/application tables,
those should live in a separate backend-owned schema.

## Current Data Flow

```text
Local XML/VOTable files
    -> acquisition.importers.LocalLightCurvePreloader
    -> odm.database SQLAlchemy models/repositories
    -> PostgreSQL astronomy schema
    -> viewer.local_viewer Streamlit app
```
