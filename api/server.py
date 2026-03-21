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
    source_url: str | None,
    supplemental_source_path: str | Path | None,
    supplemental_source_url: str | None,
    output_dir: str | Path,
    download_timeout: int,
    strict: bool = False,
) -> FeedHTTPServer:
    LOGGER.info(
        "Creating API server host=%s port=%s source=%s source_url=%s supplemental=%s supplemental_url=%s output_dir=%s download_timeout=%s strict=%s",
        host,
        port,
        source_path,
        bool(source_url),
        supplemental_source_path,
        bool(supplemental_source_url),
        output_dir,
        download_timeout,
        strict,
    )
    return FeedHTTPServer(
        (host, port),
        source_path=source_path,
        source_url=source_url,
        supplemental_source_path=supplemental_source_path,
        supplemental_source_url=supplemental_source_url,
        output_dir=output_dir,
        download_timeout=download_timeout,
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
        source_url=args.source_url,
        supplemental_source_path=args.supplemental_source,
        supplemental_source_url=args.supplemental_source_url,
        output_dir=args.output_dir,
        download_timeout=args.download_timeout,
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
