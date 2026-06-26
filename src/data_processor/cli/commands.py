"""CLI commands for local development and operations."""

import argparse
from pathlib import Path

from streamlit.web import cli as streamlit_cli

from data_processor.config.logging import configure_logging
from data_processor.config.settings import get_settings
from data_processor.infrastructure.importers.local_light_curve_preloader import (
    LocalLightCurvePreloader,
)


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

    args = parser.parse_args()

    if args.command == "preload-light-curves":
        _run_preload_light_curves(args)
    elif args.command == "light-curve-viewer":
        light_curve_viewer_main()


def preload_light_curves_main() -> None:
    parser = argparse.ArgumentParser(prog="preload-light-curves")
    _add_preload_arguments(parser)
    _run_preload_light_curves(parser.parse_args())


def light_curve_viewer_main() -> None:
    streamlit_cli.main_run(["src/data_processor/local_viewer/app.py"])


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


if __name__ == "__main__":
    main()
