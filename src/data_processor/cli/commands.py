"""CLI commands for local development and operations."""

import argparse
import platform
import subprocess
from pathlib import Path

from streamlit.web import cli as streamlit_cli

from data_processor.acquisition.importers.local_light_curve_preloader import (
    LocalLightCurvePreloader,
)
from data_processor.config.logging import configure_logging
from data_processor.config.settings import get_settings
from data_processor.odm.database.schema import create_current_schema


def main() -> None:
    parser = argparse.ArgumentParser(prog="data-processor")
    subparsers = parser.add_subparsers(dest="command", required=True)

    _add_preload_arguments(
        subparsers.add_parser(
            "preload-light-curves",
            help="Preload local VOTable XML light curves into PostgreSQL.",
        ),
    )
    subparsers.add_parser(
        "light-curve-viewer",
        help="Run the local Streamlit light-curve viewer.",
    )
    stop_viewer_parser = subparsers.add_parser(
        "stop-light-curve-viewer",
        help="Stop the local Streamlit light-curve viewer by port.",
    )
    _add_stop_viewer_arguments(stop_viewer_parser)
    subparsers.add_parser(
        "init-db",
        help="Create the current prototype PostgreSQL schema.",
    )

    args = parser.parse_args()

    if args.command == "preload-light-curves":
        _run_preload_light_curves(args)
    elif args.command == "light-curve-viewer":
        light_curve_viewer_main()
    elif args.command == "stop-light-curve-viewer":
        _run_stop_light_curve_viewer(args)
    elif args.command == "init-db":
        init_db_main()


def preload_light_curves_main() -> None:
    parser = argparse.ArgumentParser(prog="preload-light-curves")
    _add_preload_arguments(parser)
    _run_preload_light_curves(parser.parse_args())


def light_curve_viewer_main() -> None:
    streamlit_cli.main_run(["src/data_processor/viewer/local_viewer/app.py"])


def stop_light_curve_viewer_main() -> None:
    parser = argparse.ArgumentParser(prog="stop-light-curve-viewer")
    _add_stop_viewer_arguments(parser)
    _run_stop_light_curve_viewer(parser.parse_args())


def init_db_main() -> None:
    create_current_schema()
    print("Current prototype database schema is ready.")


def _add_preload_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--path",
        type=Path,
        default=None,
        help="Folder containing VOTable XML files. Defaults to LOCAL_LIGHT_CURVES_PATH.",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search XML files recursively.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum number of files to preload.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List files that would be imported without writing to PostgreSQL.",
    )
    parser.add_argument(
        "--no-progress",
        action="store_true",
        help="Disable the terminal progress bar.",
    )


def _add_stop_viewer_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--port",
        type=int,
        default=8501,
        help="Port used by the local Streamlit viewer. Defaults to 8501.",
    )


def _run_preload_light_curves(args: argparse.Namespace) -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    folder = args.path or Path(settings.local_light_curves_path)
    summary = LocalLightCurvePreloader().preload_folder(
        folder=folder,
        recursive=args.recursive,
        limit=args.limit,
        dry_run=args.dry_run,
        show_progress=not args.no_progress,
    )
    print(summary.to_message())


def _run_stop_light_curve_viewer(args: argparse.Namespace) -> None:
    if platform.system() != "Windows":
        raise SystemExit("stop-light-curve-viewer is currently implemented for Windows only.")

    command = [
        "powershell.exe",
        "-NoProfile",
        "-Command",
        (
            "$connections = Get-NetTCPConnection -State Listen "
            f"| Where-Object {{ $_.LocalPort -eq {args.port} }}; "
            "if (-not $connections) { "
            f"Write-Output 'No process is listening on port {args.port}.'; exit 0 "
            "} "
            "$processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique; "
            "foreach ($processId in $processIds) { "
            "$process = Get-Process -Id $processId -ErrorAction SilentlyContinue; "
            "if ($process) { "
            "Stop-Process -Id $processId -Force; "
            f'Write-Output "Stopped process $processId on port {args.port}." '
            "} "
            "}"
        ),
    ]
    result = subprocess.run(command, check=False, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip())
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
