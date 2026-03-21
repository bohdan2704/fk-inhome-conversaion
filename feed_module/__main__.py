from __future__ import annotations

import argparse
import os
from pathlib import Path
from time import perf_counter

from feed_module.content import generate_content_xml
from feed_module.paths import (
    DEFAULT_CONTENT_NAME,
    DEFAULT_OUTPUT_DIR,
    DEFAULT_PROPOSITIONS_NAME,
    DEFAULT_SOURCE,
    DEFAULT_SUPPLEMENTAL_SOURCE,
)
from feed_module.propositions import generate_propositions_xml
from logger import DEFAULT_LOG_LEVEL, configure_logging, format_duration, get_logger


LOGGER = get_logger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate both XML feeds from a source YML feed."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to the source YML feed. Default: {DEFAULT_SOURCE}",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help=f"Directory for generated XML files. Default: {DEFAULT_OUTPUT_DIR}",
    )
    parser.add_argument(
        "--content-name",
        default=DEFAULT_CONTENT_NAME,
        help=f"Filename for the content XML feed. Default: {DEFAULT_CONTENT_NAME}",
    )
    parser.add_argument(
        "--propositions-name",
        default=DEFAULT_PROPOSITIONS_NAME,
        help=(
            "Filename for the propositions XML feed. "
            f"Default: {DEFAULT_PROPOSITIONS_NAME}"
        ),
    )
    parser.add_argument(
        "--supplemental-source",
        type=Path,
        default=DEFAULT_SUPPLEMENTAL_SOURCE,
        help=(
            "Optional supplemental XML feed used to enrich the content feed, "
            f"for example with image links. Default: {DEFAULT_SUPPLEMENTAL_SOURCE}"
        ),
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail if required partner fields are missing.",
    )
    parser.add_argument(
        "--log-level",
        default=(
            os.environ.get("FEED_LOG_LEVEL")
            or os.environ.get("LOG_LEVEL")
            or DEFAULT_LOG_LEVEL
        ),
        help="Logging level. Default: INFO",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    configure_logging(args.log_level)
    started_at = perf_counter()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    content_path = output_dir / args.content_name
    propositions_path = output_dir / args.propositions_name
    LOGGER.info(
        "Generating feeds source=%s supplemental=%s output_dir=%s strict=%s",
        args.source,
        args.supplemental_source,
        output_dir,
        args.strict,
    )

    generate_content_xml(
        source_path=args.source,
        output_path=content_path,
        supplemental_source_path=(
            args.supplemental_source if args.supplemental_source.exists() else None
        ),
        strict=args.strict,
    )
    generate_propositions_xml(
        source_path=args.source,
        output_path=propositions_path,
        strict=args.strict,
    )

    LOGGER.info(
        "Generated feeds content=%s propositions=%s duration=%s",
        content_path,
        propositions_path,
        format_duration(perf_counter() - started_at),
    )
    print(content_path)
    print(propositions_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
