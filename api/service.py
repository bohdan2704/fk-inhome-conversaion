from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from time import perf_counter

from feed_module.content import generate_content_xml
from feed_module.paths import DEFAULT_CONTENT_NAME, DEFAULT_PROPOSITIONS_NAME
from feed_module.propositions import generate_propositions_xml
from logger import format_duration, get_logger

from .handlers import FeedRequestHandler


LOGGER = get_logger(__name__)


class FeedHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        source_path: str | Path,
        supplemental_source_path: str | Path | None,
        output_dir: str | Path,
        *,
        strict: bool = False,
    ) -> None:
        super().__init__(server_address, FeedRequestHandler)
        self.source_path = Path(source_path)
        self.supplemental_source_path = (
            Path(supplemental_source_path)
            if supplemental_source_path is not None
            else None
        )
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.strict = strict
        self.feed_lock = Lock()
        LOGGER.info(
            "Initialized feed server address=%s source=%s supplemental=%s output_dir=%s strict=%s",
            server_address,
            self.source_path,
            self.supplemental_source_path,
            self.output_dir,
            self.strict,
        )

    def build_content_feed(self) -> bytes:
        started_at = perf_counter()
        with self.feed_lock:
            output_path = self.output_dir / DEFAULT_CONTENT_NAME
            supplemental = self.supplemental_source_path
            if supplemental is not None and not supplemental.exists():
                supplemental = None
            LOGGER.info(
                "Building content feed output=%s source=%s supplemental=%s",
                output_path,
                self.source_path,
                supplemental,
            )
            generate_content_xml(
                source_path=self.source_path,
                output_path=output_path,
                supplemental_source_path=supplemental,
                strict=self.strict,
            )
            payload = output_path.read_bytes()
            LOGGER.info(
                "Built content feed output=%s bytes=%s duration=%s",
                output_path,
                len(payload),
                format_duration(perf_counter() - started_at),
            )
            return payload

    def build_propositions_feed(self) -> bytes:
        started_at = perf_counter()
        with self.feed_lock:
            output_path = self.output_dir / DEFAULT_PROPOSITIONS_NAME
            LOGGER.info(
                "Building propositions feed output=%s source=%s",
                output_path,
                self.source_path,
            )
            generate_propositions_xml(
                source_path=self.source_path,
                output_path=output_path,
                strict=self.strict,
            )
            payload = output_path.read_bytes()
            LOGGER.info(
                "Built propositions feed output=%s bytes=%s duration=%s",
                output_path,
                len(payload),
                format_duration(perf_counter() - started_at),
            )
            return payload


__all__ = ["FeedHTTPServer"]
