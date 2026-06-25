# Data Processor

Autonomous worker service for importing, validating, transforming, and analyzing
astronomical XML data.

The backend and this processor are intended to run as independent containers.
Both communicate through PostgreSQL:

```text
Frontend -> Backend API -> PostgreSQL <- Data Processor Worker
```

The backend serves HTTP requests and reads already processed data. The processor
runs in a polling loop, claims pending work from PostgreSQL, processes source
files, and writes normalized results back to the database.

This repository currently contains only the initial architecture skeleton.
