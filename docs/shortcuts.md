# Command Shortcuts

These commands are available after installing the project in editable mode:

```powershell
pip install -e ".[dev]"
```

Run them from the project root with the virtual environment activated:

```powershell
.\.venv\Scripts\Activate.ps1
```

## Main CLI

General project command:

```powershell
data-processor --help
```

Preload local light curves through the main CLI:

```powershell
data-processor preload-light-curves --limit 20
```

Run the local viewer through the main CLI:

```powershell
data-processor light-curve-viewer
```

Stop the local viewer through the main CLI:

```powershell
data-processor stop-light-curve-viewer
```

## Direct Shortcuts

Preload XML/VOTable light curves from `LOCAL_LIGHT_CURVES_PATH`:

```powershell
preload-light-curves
```

Preview how many files would be imported:

```powershell
preload-light-curves --dry-run
```

Import a limited number of files:

```powershell
preload-light-curves --limit 20
```

Disable the progress bar:

```powershell
preload-light-curves --no-progress
```

Search recursively:

```powershell
preload-light-curves --recursive
```

Use a custom folder:

```powershell
preload-light-curves --path "C:\path\to\light_curves"
```

Run the local Streamlit viewer:

```powershell
light-curve-viewer
```

The viewer opens at:

```text
http://localhost:8501
```

Stop the local Streamlit viewer running in the background:

```powershell
stop-light-curve-viewer
```

If the viewer is running on a different port:

```powershell
stop-light-curve-viewer --port 8502
```

## Alembic

Alembic commands are documented in:

```text
alembic/COMMANDS.md
```
