from __future__ import annotations

from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from time import perf_counter

from feed_module.content import generate_content_xml
from feed_module.paths import DEFAULT_CONTENT_NAME, DEFAULT_PROPOSITIONS_NAME
from feed_module.propositions import generate_propositions_xml
from logger import format_duration, get_logger
from source_downloader import DEFAULT_DOWNLOAD_TIMEOUT, download_xml

from .handlers import FeedRequestHandler


LOGGER = get_logger(__name__)


class FeedHTTPServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        source_path: str | Path,
        source_url: str | None,
        supplemental_source_path: str | Path | None,
        supplemental_source_url: str | None,
        output_dir: str | Path,
        *,
        download_timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
        strict: bool = False,
    ) -> None:
        super().__init__(server_address, FeedRequestHandler)
        self.source_path = Path(source_path)
        self.source_url = source_url
        self.supplemental_source_path = (
            Path(supplemental_source_path)
            if supplemental_source_path is not None
            else None
        )
        self.supplemental_source_url = supplemental_source_url
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.download_timeout = download_timeout
        self.strict = strict
        self.feed_lock = Lock()
        LOGGER.info(
            "Initialized feed server address=%s source=%s source_url=%s supplemental=%s supplemental_url=%s output_dir=%s download_timeout=%s strict=%s",
            server_address,
            self.source_path,
            bool(self.source_url),
            self.supplemental_source_path,
            bool(self.supplemental_source_url),
            self.output_dir,
            self.download_timeout,
            self.strict,
        )

    def build_content_feed(self) -> bytes:
        started_at = perf_counter()
        with self.feed_lock:
            source_path, supplemental_path = self._refresh_source_files()
            output_path = self.output_dir / DEFAULT_CONTENT_NAME
            LOGGER.info(
                "Building content feed output=%s source=%s supplemental=%s",
                output_path,
                source_path,
                supplemental_path,
            )
            generate_content_xml(
                source_path=source_path,
                output_path=output_path,
                supplemental_source_path=supplemental_path,
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
            source_path, _ = self._refresh_source_files()
            output_path = self.output_dir / DEFAULT_PROPOSITIONS_NAME
            LOGGER.info(
                "Building propositions feed output=%s source=%s",
                output_path,
                source_path,
            )
            generate_propositions_xml(
                source_path=source_path,
                output_path=output_path,
                supplemental_source_path=supplemental_path,
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

    def _refresh_source_files(self) -> tuple[Path, Path | None]:
        if self.source_url:
            source_path = download_xml(
                url=self.source_url,
                destination=self.source_path,
                timeout=self.download_timeout,
            )
        elif not self.source_path.exists():
            raise FileNotFoundError(self.source_path)
        else:
            source_path = self.source_path

        supplemental_path = self.supplemental_source_path
        if self.supplemental_source_url:
            if supplemental_path is None:
                raise ValueError(
                    "supplemental_source_path is required when supplemental_source_url is set"
                )
            supplemental_path = download_xml(
                url=self.supplemental_source_url,
                destination=supplemental_path,
                timeout=self.download_timeout,
            )
        elif supplemental_path is not None and not supplemental_path.exists():
            supplemental_path = None

        return source_path, supplemental_path


__all__ = ["FeedHTTPServer"]
