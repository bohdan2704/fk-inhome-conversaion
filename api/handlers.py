from __future__ import annotations

import json
from collections.abc import Callable
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from time import perf_counter
from typing import TYPE_CHECKING, cast
from urllib.parse import urlparse

from feed_module.paths import DEFAULT_CONTENT_NAME, DEFAULT_PROPOSITIONS_NAME
from logger import format_duration, get_logger

from .constants import CONTENT_ENDPOINT, PROPOSITIONS_ENDPOINT

if TYPE_CHECKING:
    from .service import FeedHTTPServer


LOGGER = get_logger(__name__)


class FeedRequestHandler(BaseHTTPRequestHandler):
    server_version = "FeedAPI/1.0"

    def do_GET(self) -> None:
        self._serve_request(lambda: self._dispatch(send_body=True))

    def do_HEAD(self) -> None:
        self._serve_request(lambda: self._dispatch(send_body=False))

    def do_OPTIONS(self) -> None:
        self._serve_request(self._handle_options)

    def log_message(self, format: str, *args: object) -> None:
        return

    def _serve_request(self, action: Callable[[], tuple[int, int]]) -> None:
        started_at = perf_counter()
        status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
        content_length = 0

        try:
            status, content_length = action()
        except Exception:
            LOGGER.exception(
                "Unhandled request error method=%s path=%s client=%s",
                self.command,
                self.path,
                self.client_address[0],
            )
            try:
                status, content_length = self._send_error(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    "Internal server error.\n",
                    send_body=self.command != "HEAD",
                )
            except (BrokenPipeError, ConnectionResetError):
                status = int(HTTPStatus.INTERNAL_SERVER_ERROR)
                content_length = 0
        finally:
            self._log_request_completion(
                status=status,
                content_length=content_length,
                started_at=started_at,
            )

    def _dispatch(self, *, send_body: bool) -> tuple[int, int]:
        path = urlparse(self.path).path
        if path == "/":
            return self._handle_index(send_body=send_body)
        if path == CONTENT_ENDPOINT:
            return self._handle_feed(
                content_type="application/xml; charset=utf-8",
                filename=DEFAULT_CONTENT_NAME,
                payload_factory=self._api_server().build_content_feed,
                send_body=send_body,
            )
        if path == PROPOSITIONS_ENDPOINT:
            return self._handle_feed(
                content_type="application/xml; charset=utf-8",
                filename=DEFAULT_PROPOSITIONS_NAME,
                payload_factory=self._api_server().build_propositions_feed,
                send_body=send_body,
            )
        return self._send_error(
            HTTPStatus.NOT_FOUND,
            "Not found.\n",
            send_body=send_body,
        )

    def _handle_options(self) -> tuple[int, int]:
        return self._send_response(
            HTTPStatus.NO_CONTENT,
            b"",
            content_type="text/plain; charset=utf-8",
            cache_control="public, max-age=86400",
            send_body=False,
        )

    def _handle_index(self, *, send_body: bool) -> tuple[int, int]:
        payload = json.dumps(
            {
                "service": "feed-api",
                "public": True,
                "endpoints": {
                    "content": CONTENT_ENDPOINT,
                    "propositions": PROPOSITIONS_ENDPOINT,
                },
            },
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        return self._send_response(
            HTTPStatus.OK,
            payload,
            content_type="application/json; charset=utf-8",
            cache_control="public, max-age=300",
            send_body=send_body,
        )

    def _handle_feed(
        self,
        *,
        content_type: str,
        filename: str,
        payload_factory: Callable[[], bytes],
        send_body: bool,
    ) -> tuple[int, int]:
        try:
            payload = payload_factory()
        except Exception as exc:
            LOGGER.exception("Failed to generate %s", filename)
            return self._send_error(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                f"Failed to generate {filename}: {exc}\n",
                send_body=send_body,
            )

        return self._send_response(
            HTTPStatus.OK,
            payload,
            content_type=content_type,
            cache_control="public, max-age=300",
            filename=filename,
            send_body=send_body,
        )

    def _send_error(
        self,
        status: HTTPStatus,
        message: str,
        *,
        send_body: bool,
    ) -> tuple[int, int]:
        payload = message.encode("utf-8")
        return self._send_response(
            status,
            payload,
            content_type="text/plain; charset=utf-8",
            cache_control="no-store",
            send_body=send_body,
        )

    def _send_response(
        self,
        status: HTTPStatus,
        payload: bytes,
        *,
        content_type: str,
        cache_control: str,
        send_body: bool,
        filename: str | None = None,
    ) -> tuple[int, int]:
        self.send_response(status)
        self._write_common_headers(
            content_type=content_type,
            content_length=len(payload),
            cache_control=cache_control,
            filename=filename,
        )
        self.end_headers()
        if send_body:
            self._write_payload(payload)
        return int(status), len(payload)

    def _write_common_headers(
        self,
        *,
        content_type: str,
        content_length: int,
        cache_control: str,
        filename: str | None = None,
    ) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Max-Age", "86400")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        self.send_header("Cache-Control", cache_control)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(content_length))
        if filename:
            self.send_header(
                "Content-Disposition",
                f'inline; filename="{filename}"',
            )

    def _write_payload(self, payload: bytes) -> None:
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError):
            return

    def _log_request_completion(
        self,
        *,
        status: int,
        content_length: int,
        started_at: float,
    ) -> None:
        LOGGER.info(
            "%s %s status=%s bytes=%s duration=%s client=%s",
            self.command,
            urlparse(self.path).path,
            status,
            content_length,
            format_duration(perf_counter() - started_at),
            self.client_address[0],
        )

    def _api_server(self) -> "FeedHTTPServer":
        return cast("FeedHTTPServer", self.server)


__all__ = ["FeedRequestHandler"]
