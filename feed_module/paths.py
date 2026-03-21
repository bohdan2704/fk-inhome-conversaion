from __future__ import annotations

from pathlib import Path


MODULE_DIR = Path(__file__).resolve().parent
DEFAULT_SOURCE = MODULE_DIR / "xml_example" / "fk-inhome.com.ua.xml"
DEFAULT_SUPPLEMENTAL_SOURCE = MODULE_DIR / "xml_example" / "fk-inhome.com.ua=2.xml"
DEFAULT_OUTPUT_DIR = MODULE_DIR / "generated"
DEFAULT_CONTENT_NAME = "content_feed.xml"
DEFAULT_PROPOSITIONS_NAME = "propositions_feed.xml"


__all__ = [
    "DEFAULT_CONTENT_NAME",
    "DEFAULT_OUTPUT_DIR",
    "DEFAULT_PROPOSITIONS_NAME",
    "DEFAULT_SOURCE",
    "DEFAULT_SUPPLEMENTAL_SOURCE",
    "MODULE_DIR",
]
