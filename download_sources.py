from __future__ import annotations

from feed_module.paths import (
    DEFAULT_DOWNLOADED_SOURCE,
    DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE,
)
from logger import DEFAULT_LOG_LEVEL, configure_logging
from source_downloader import DEFAULT_DOWNLOAD_TIMEOUT, download_xml


SOURCE_URL = (
    "https://fk-inhome.com.ua/productcatalog/rozetka/"
    "?uid=8ecf4c810347463c9439b3af4e7cd6e6&lang=3"
)
SUPPLEMENTAL_SOURCE_URL = (
    "https://fk-inhome.com.ua/productcatalog/prom/"
    "?uid=254bde5b79b34ce7ac5f66ad2f63d32c&lang=3"
)
SOURCE_DESTINATION = DEFAULT_DOWNLOADED_SOURCE
SUPPLEMENTAL_SOURCE_DESTINATION = DEFAULT_DOWNLOADED_SUPPLEMENTAL_SOURCE
DOWNLOAD_TIMEOUT = DEFAULT_DOWNLOAD_TIMEOUT
LOG_LEVEL = DEFAULT_LOG_LEVEL


def main() -> int:
    configure_logging(LOG_LEVEL)

    source_path = download_xml(
        url=SOURCE_URL,
        destination=SOURCE_DESTINATION,
        timeout=DOWNLOAD_TIMEOUT,
    )
    supplemental_path = download_xml(
        url=SUPPLEMENTAL_SOURCE_URL,
        destination=SUPPLEMENTAL_SOURCE_DESTINATION,
        timeout=DOWNLOAD_TIMEOUT,
    )

    print(source_path)
    print(supplemental_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
