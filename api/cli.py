from __future__ import annotations

import argparse
import os
from pathlib import Path

from feed_module.paths import (
    DEFAULT_DOWNLOADED_SOURCE,
    DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE,
    DEFAULT_OUTPUT_DIR,
)
from logger import DEFAULT_LOG_LEVEL

from .constants import DEFAULT_HOST, DEFAULT_PORT
from source_downloader import DEFAULT_DOWNLOAD_TIMEOUT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serve the content XML feed and propositions JSON feed over a public HTTP API.",
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("FEED_API_HOST", DEFAULT_HOST),
        help=f"Host to bind. Default: {DEFAULT_HOST}",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("FEED_API_PORT", str(DEFAULT_PORT))),
        help=f"Port to bind. Default: {DEFAULT_PORT}",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_DOWNLOADED_SOURCE,
        help=(
            "Path where the downloaded Rozetka source feed is stored before generation. "
            f"Default: {DEFAULT_DOWNLOADED_SOURCE}"
        ),
    )
    parser.add_argument(
        "--supplemental-source",
        type=Path,
        default=DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE,
        help=(
            "Path where the downloaded Prom source feed is stored before generation. "
            f"Default: {DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE}"
        ),
    )
    parser.add_argument(
        "--source-url",
        default=os.environ.get("FEED_SOURCE_URL"),
        help="Rozetka source URL. Environment: FEED_SOURCE_URL",
    )
    parser.add_argument(
        "--supplemental-source-url",
        default=os.environ.get("FEED_SUPPLEMENTAL_SOURCE_URL"),
        help="Prom source URL. Environment: FEED_SUPPLEMENTAL_SOURCE_URL",
    )
    parser.add_argument(
        "--download-timeout",
        type=int,
        default=int(
            os.environ.get("FEED_DOWNLOAD_TIMEOUT", str(DEFAULT_DOWNLOAD_TIMEOUT))
        ),
        help=f"Timeout in seconds for source downloads. Default: {DEFAULT_DOWNLOAD_TIMEOUT}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.environ.get("FEED_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)),
        help=f"Directory for generated feed files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail requests when required partner fields are missing.",
    )
    parser.add_argument(
        "--log-level",
        default=(
            os.environ.get("FEED_API_LOG_LEVEL")
            or os.environ.get("LOG_LEVEL")
            or DEFAULT_LOG_LEVEL
        ),
        help="Logging level. Default: INFO",
    )
    return parser


__all__ = ["build_parser"]
