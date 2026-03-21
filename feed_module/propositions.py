from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Mapping
import xml.etree.ElementTree as ET

from logger import format_duration, get_logger
from .shared import (
    PropositionOverride,
    add_text_node,
    parse_source_yml,
    stringify_bool,
    stringify_number,
    write_xml_with_cdata,
)


LOGGER = get_logger(__name__)


def generate_propositions_xml(
    source_path: str | Path,
    output_path: str | Path,
    overrides: Mapping[str, PropositionOverride] | None = None,
    *,
    strict: bool = False,
) -> Path:
    """
    Generate the propositions feed as XML.

    The PDF in instructions/propositions.pdf describes these fields in JSON form, so this
    function maps the same field names into XML:
    <OffersFeed><total>...<data><offer>...</offer></data></OffersFeed>
    """
    started_at = perf_counter()
    LOGGER.info(
        "Generating propositions XML source=%s output=%s strict=%s",
        source_path,
        output_path,
        strict,
    )
    overrides = overrides or {}
    offers = parse_source_yml(source_path)
    missing_required: list[str] = []
    root = ET.Element("OffersFeed")
    data_node = ET.SubElement(root, "data")
    total = 0
    offers_with_old_price = 0

    for source_offer in offers:
        override = overrides.get(source_offer.offer_id, PropositionOverride())
        code = override.code or source_offer.offer_id
        price = override.price if override.price is not None else source_offer.price
        old_price = (
            override.old_price if override.old_price is not None else source_offer.old_price
        )
        availability = (
            override.availability
            if override.availability is not None
            else source_offer.available
        )

        offer_node = ET.SubElement(data_node, "offer")
        add_text_node(offer_node, "code", code)
        add_text_node(offer_node, "price", stringify_number(price))
        add_text_node(offer_node, "old_price", stringify_number(old_price))
        if old_price is not None:
            offers_with_old_price += 1
        add_text_node(offer_node, "availability", stringify_bool(availability))
        add_text_node(offer_node, "warranty_type", override.warranty_type)
        add_text_node(
            offer_node,
            "warranty_period",
            stringify_number(override.warranty_period),
        )
        add_text_node(
            offer_node,
            "max_pay_in_parts",
            stringify_number(override.max_pay_in_parts),
        )
        add_text_node(
            offer_node,
            "days_to_dispatch",
            stringify_number(override.days_to_dispatch),
        )

        if override.delivery_methods:
            delivery_methods_node = ET.SubElement(offer_node, "delivery_methods")
            for delivery_method in override.delivery_methods:
                method_node = ET.SubElement(delivery_methods_node, "delivery_method")
                add_text_node(method_node, "method", delivery_method.get("method"))
                add_text_node(
                    method_node,
                    "price",
                    stringify_number(delivery_method.get("price")),
                )

        if override.multiplicity is not None:
            checkout_constraints_node = ET.SubElement(
                offer_node,
                "checkout_constraints",
            )
            add_text_node(
                checkout_constraints_node,
                "multiplicity",
                stringify_number(override.multiplicity),
            )

        if override.country_code or override.manufacture_year is not None:
            manufacture_node = ET.SubElement(offer_node, "manufacture")
            add_text_node(manufacture_node, "country_code", override.country_code)
            add_text_node(
                manufacture_node,
                "year",
                stringify_number(override.manufacture_year),
            )

        total += 1

        if price is None:
            missing_required.append(
                f"offer {source_offer.offer_id}: propositions.price is required"
            )
        if code is None:
            missing_required.append(
                f"offer {source_offer.offer_id}: propositions.code is required"
            )

    total_node = ET.Element("total")
    total_node.text = str(total)
    root.insert(0, total_node)
    write_xml_with_cdata(root, output_path, cdata_tags=set())

    if strict and missing_required:
        LOGGER.error(
            "Propositions XML validation failed output=%s missing_required=%s duration=%s",
            output_path,
            len(missing_required),
            format_duration(perf_counter() - started_at),
        )
        formatted = "\n".join(missing_required)
        raise ValueError(f"Missing partner-required proposition fields:\n{formatted}")

    LOGGER.info(
        "Generated propositions XML output=%s offers=%s offers_with_old_price=%s missing_required=%s duration=%s",
        output_path,
        total,
        offers_with_old_price,
        len(missing_required),
        format_duration(perf_counter() - started_at),
    )

    return Path(output_path)


__all__ = ["PropositionOverride", "generate_propositions_xml"]
