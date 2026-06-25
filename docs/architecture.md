# Architecture

The processor is an autonomous worker that polls PostgreSQL for pending work.
It is deployed independently from the backend and writes processed results back
to PostgreSQL.

```text
Frontend -> Backend API -> PostgreSQL <- Data Processor Worker
```

The backend does not execute processing logic. It only reads data and exposes
HTTP endpoints.
