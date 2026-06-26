# Migrations

This repository owns the PostgreSQL `astronomy` schema.

The backend may read from this schema, but it must not generate or run
migrations for these tables. The real schema contract is defined by Alembic
migrations in this repository.

## Local Commands

Run migrations:

```powershell
alembic upgrade head
```

Create a new migration after SQLAlchemy models change:

```powershell
alembic revision --autogenerate -m "describe change"
```

## Docker

Production deployment should run migrations before starting services that
depend on the schema:

```text
data-processor-migrations -> data-processor-worker
```

The worker must not create tables dynamically with `Base.metadata.create_all()`
in production.

## Schema

All astronomy-owned tables should live under:

```text
astronomy
```

The Alembic version table also lives in this schema.
