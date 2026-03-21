from __future__ import annotations

import argparse
import os
from pathlib import Path

from feed_module.paths import (
    DEFAULT_OUTPUT_DIR,
    DEFAULT_SOURCE,
    DEFAULT_SUPPLEMENTAL_SOURCE,
)
from logger import DEFAULT_LOG_LEVEL

from .constants import DEFAULT_HOST, DEFAULT_PORT


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Serve the generated XML feeds over a public HTTP API.",
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
        default=Path(os.environ.get("FEED_SOURCE_PATH", DEFAULT_SOURCE)),
        help=f"Path to the source YML feed. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--supplemental-source",
        type=Path,
        default=Path(
            os.environ.get(
                "FEED_SUPPLEMENTAL_SOURCE_PATH",
                DEFAULT_SUPPLEMENTAL_SOURCE,
            )
        ),
        help=(
            "Optional supplemental XML feed used to enrich content output. "
            f"Default: {DEFAULT_SUPPLEMENTAL_SOURCE}"
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(os.environ.get("FEED_OUTPUT_DIR", DEFAULT_OUTPUT_DIR)),
        help=f"Directory for generated XML files. Default: {DEFAULT_OUTPUT_DIR}",
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
