from __future__ import annotations

import argparse
import os
from pathlib import Path

from feed_module.paths import (
    DEFAULT_DOWNLOADED_SOURCE,
    DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE,
)
from logger import DEFAULT_LOG_LEVEL, configure_logging, get_logger

from .downloads import DEFAULT_DOWNLOAD_TIMEOUT, download_xml, sanitize_url_for_log


LOGGER = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download Rozetka and Prom XML sources to local timestamped files.",
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_DOWNLOADED_SOURCE,
        help=(
            "Base path used for saved Rozetka XML snapshots. "
            f"Default: {DEFAULT_DOWNLOADED_SOURCE}"
        ),
    )
    parser.add_argument(
        "--supplemental-source",
        type=Path,
        default=DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE,
        help=(
            "Base path used for saved Prom XML snapshots. "
            f"Default: {DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE}"
        ),
    )
    parser.add_argument(
        "--source-url",
        default=os.environ.get("FEED_SOURCE_URL"),
        help="Rozetka XML source URL. Environment: FEED_SOURCE_URL",
    )
    parser.add_argument(
        "--supplemental-source-url",
        default=os.environ.get("FEED_SUPPLEMENTAL_SOURCE_URL"),
        help="Prom XML source URL. Environment: FEED_SUPPLEMENTAL_SOURCE_URL",
    )
    parser.add_argument(
        "--download-timeout",
        type=int,
        default=int(
            os.environ.get("FEED_DOWNLOAD_TIMEOUT", str(DEFAULT_DOWNLOAD_TIMEOUT))
        ),
        help=f"Timeout in seconds for source XML downloads. Default: {DEFAULT_DOWNLOAD_TIMEOUT}",
    )
    parser.add_argument(
        "--log-level",
        default=(
            os.environ.get("FEED_API_LOG_LEVEL")
            or os.environ.get("FEED_LOG_LEVEL")
            or os.environ.get("LOG_LEVEL")
            or DEFAULT_LOG_LEVEL
        ),
        help="Logging level. Default: INFO",
    )
    return parser


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)

    if not args.source_url:
        raise ValueError("FEED_SOURCE_URL or --source-url is required")
    if not args.supplemental_source_url:
        raise ValueError(
            "FEED_SUPPLEMENTAL_SOURCE_URL or --supplemental-source-url is required"
        )

    LOGGER.info(
        "Downloading source snapshots source_url=%s supplemental_url=%s",
        sanitize_url_for_log(args.source_url),
        sanitize_url_for_log(args.supplemental_source_url),
    )

    source_path = download_xml(
        url=args.source_url,
        destination=args.source,
        timeout=args.download_timeout,
    )
    supplemental_path = download_xml(
        url=args.supplemental_source_url,
        destination=args.supplemental_source,
        timeout=args.download_timeout,
    )

    print(source_path)
    print(supplemental_path)
    return 0


__all__ = ["build_parser", "run"]
