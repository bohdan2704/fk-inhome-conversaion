from __future__ import annotations

from pathlib import Path
from shutil import copyfileobj
from time import perf_counter
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen

from logger import format_duration, get_logger


LOGGER = get_logger(__name__)
DEFAULT_DOWNLOAD_TIMEOUT = 60
DEFAULT_USER_AGENT = "convert-api/1.0"


def download_xml(
    *,
    url: str,
    destination: str | Path,
    timeout: int = DEFAULT_DOWNLOAD_TIMEOUT,
) -> Path:
    destination_path = Path(destination)
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = destination_path.with_suffix(destination_path.suffix + ".tmp")
    started_at = perf_counter()
    safe_url = sanitize_url_for_log(url)

    LOGGER.info(
        "Downloading XML source url=%s destination=%s timeout=%ss",
        safe_url,
        destination_path,
        timeout,
    )

    request = Request(
        url,
        headers={
            "User-Agent": DEFAULT_USER_AGENT,
            "Accept": "application/xml,text/xml;q=0.9,*/*;q=0.8",
        },
    )

    with urlopen(request, timeout=timeout) as response:
        status = getattr(response, "status", response.getcode())
        if status != 200:
            raise RuntimeError(f"Failed to download {safe_url}: HTTP {status}")
        with temporary_path.open("wb") as file_obj:
            copyfileobj(response, file_obj)

    temporary_path.replace(destination_path)
    file_size = destination_path.stat().st_size
    LOGGER.info(
        "Downloaded XML source url=%s destination=%s bytes=%s duration=%s",
        safe_url,
        destination_path,
        file_size,
        format_duration(perf_counter() - started_at),
    )
    return destination_path


def sanitize_url_for_log(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))


__all__ = [
    "DEFAULT_DOWNLOAD_TIMEOUT",
    "download_xml",
    "sanitize_url_for_log",
]
