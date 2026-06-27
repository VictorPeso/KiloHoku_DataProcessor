# Data Processor

Python project for importing local astronomical VOTable XML light curves into
PostgreSQL and visualizing them with a provisional Streamlit viewer.

The current project is intentionally small. It is organized around four blocks:

- `acquisition`: reads local XML/VOTable files and stores their data.
- `processing`: reserved for normalization and scientific processing routines.
- `odm`: SQLAlchemy models, sessions, and database read/write repositories.
- `viewer`: provisional graphical tools for inspecting imported data.

The backend is expected to be a separate service. Both services share
PostgreSQL, but this repository currently focuses only on importing and viewing
astronomical data during development.

## Basic Flow

```text
Local XML files -> acquisition -> odm/PostgreSQL -> viewer
```

## Common Commands

Install in editable mode:

```powershell
pip install -e ".[dev]"
```

Create the current prototype schema:

```powershell
init-db
```

Preload local light curves:

```powershell
preload-light-curves
```

Run the provisional viewer:

```powershell
light-curve-viewer
```
