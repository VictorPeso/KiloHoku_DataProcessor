# Processing Flow

1. The worker wakes up based on the configured polling interval.
2. It claims a batch of pending jobs from PostgreSQL.
3. Each claimed job is marked as processing.
4. The worker reads source XML references.
5. XML files are validated, parsed, and mapped to internal models.
6. Data is transformed and analyzed by specialized processors.
7. Results and progress are written back to PostgreSQL.
8. The job is marked as completed, completed with warnings, failed, or cancelled.

