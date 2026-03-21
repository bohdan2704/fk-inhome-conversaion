from __future__ import annotations

from pathlib import Path
from time import perf_counter

from logger import configure_logging, format_duration, get_logger

from .cli import build_parser
from .constants import (
    CONTENT_ENDPOINT,
    DEFAULT_HOST,
    DEFAULT_PORT,
    PROPOSITIONS_ENDPOINT,
)
from .service import FeedHTTPServer


LOGGER = get_logger(__name__)


def create_server(
    *,
    host: str,
    port: int,
    source_path: str | Path,
    supplemental_source_path: str | Path | None,
    output_dir: str | Path,
    strict: bool = False,
) -> FeedHTTPServer:
    LOGGER.info(
        "Creating API server host=%s port=%s source=%s supplemental=%s output_dir=%s strict=%s",
        host,
        port,
        source_path,
        supplemental_source_path,
        output_dir,
        strict,
    )
    return FeedHTTPServer(
        (host, port),
        source_path=source_path,
        supplemental_source_path=supplemental_source_path,
        output_dir=output_dir,
        strict=strict,
    )


def run(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    configure_logging(args.log_level)
    started_at = perf_counter()
    server = create_server(
        host=args.host,
        port=args.port,
        source_path=args.source,
        supplemental_source_path=(
            args.supplemental_source if args.supplemental_source.exists() else None
        ),
        output_dir=args.output_dir,
        strict=args.strict,
    )
    LOGGER.info(
        "Starting API server host=%s port=%s content_endpoint=%s propositions_endpoint=%s",
        args.host,
        args.port,
        CONTENT_ENDPOINT,
        PROPOSITIONS_ENDPOINT,
    )
    print(f"http://{args.host}:{args.port}{CONTENT_ENDPOINT}")
    print(f"http://{args.host}:{args.port}{PROPOSITIONS_ENDPOINT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        LOGGER.info("API server shutdown requested")
    finally:
        server.server_close()
        LOGGER.info(
            "API server stopped duration=%s",
            format_duration(perf_counter() - started_at),
        )
    return 0


__all__ = [
    "CONTENT_ENDPOINT",
    "DEFAULT_HOST",
    "DEFAULT_PORT",
    "FeedHTTPServer",
    "PROPOSITIONS_ENDPOINT",
    "build_parser",
    "create_server",
    "run",
]
