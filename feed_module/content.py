from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Mapping
import xml.etree.ElementTree as ET

from logger import format_duration, get_logger
from .shared import (
    ContentOverride,
    SourceOffer,
    add_text_node,
    build_description_from_params,
    build_inferred_brand_lookup,
    collect_missing_content_fields,
    enrich_description_with_title_params,
    extract_brand,
    extract_tags,
    extract_title_params,
    fallback_type_from_title,
    merge_params,
    normalize_description,
    normalize_title,
    parse_source_yml,
    resolve_offer_barcode,
    write_xml_with_cdata,
)


LOGGER = get_logger(__name__)


def generate_content_xml(
    source_path: str | Path,
    output_path: str | Path,
    overrides: Mapping[str, ContentOverride] | None = None,
    *,
    supplemental_source_path: str | Path | None = None,
    strict: bool = False,
) -> Path:
    """
    Generate the product-content XML from the source YML.

    The docs in instructions/prices.pdf require fields that are not present in the sample
    YML feed, most notably barcode and package dimensions. When `supplemental_source_path`
    is provided, product images are merged from that auxiliary feed by offer id, with a
    vendor-code fallback for safety. Explicit supplemental barcodes are merged only by
    matching `offer id`, so numeric article values are not treated as barcodes. Pass
    `overrides` keyed by source offer id for any remaining partner-required fields.
    """
    started_at = perf_counter()
    LOGGER.info(
        "Generating content XML source=%s output=%s supplemental=%s strict=%s",
        source_path,
        output_path,
        supplemental_source_path,
        strict,
    )
    overrides = overrides or {}
    offers = parse_source_yml(source_path)
    inferred_brands = build_inferred_brand_lookup(offers)
    supplemental_by_id: dict[str, SourceOffer] = {}
    supplemental_by_vendor: dict[str, SourceOffer] = {}
    if supplemental_source_path:
        supplemental_offers = parse_source_yml(supplemental_source_path)
        supplemental_by_id = {
            offer.offer_id: offer for offer in supplemental_offers if offer.offer_id
        }
        supplemental_by_vendor = {
            offer.vendor_code: offer
            for offer in supplemental_offers
            if offer.vendor_code and offer.images
        }

    root = ET.Element("Market")
    offers_node = ET.SubElement(root, "offers")
    missing_required: list[str] = []
    exported_offers = 0
    offers_with_images = 0
    skipped_without_barcode = 0

    for source_offer in offers:
        if not source_offer.available:
            continue

        override = overrides.get(source_offer.offer_id, ContentOverride())
        supplemental_offer_by_id = supplemental_by_id.get(source_offer.offer_id)
        supplemental_offer = supplemental_offer_by_id
        if supplemental_offer is None and source_offer.vendor_code:
            supplemental_offer = supplemental_by_vendor.get(source_offer.vendor_code)

        code = override.code or source_offer.offer_id
        vendor_code = source_offer.vendor_code or (
            supplemental_offer.vendor_code if supplemental_offer else None
        )
        brand = (
            override.brand
            or source_offer.brand
            or extract_brand(source_offer.description_html)
            or inferred_brands.get(source_offer.offer_id)
        )
        barcode = resolve_offer_barcode(
            source_offer,
            override_barcode=override.barcode,
            supplemental_offer_by_id=supplemental_offer_by_id,
        )
        if not barcode:
            skipped_without_barcode += 1
            continue

        offer_node = ET.SubElement(offers_node, "offer")
        category = override.category or source_offer.category_name
        category_id = override.category_id or source_offer.category_id
        title = normalize_title(source_offer.title)
        title_params = extract_title_params(title)
        description_html = normalize_description(source_offer.description_html)
        description_html = enrich_description_with_title_params(
            description_html,
            title_params,
        )
        tags = merge_params(
            source_offer.params,
            extract_tags(description_html),
            title_params,
        )
        if not tags:
            fallback_type = fallback_type_from_title(title)
            if fallback_type:
                tags = [("Тип", fallback_type)]
        if override.extra_params:
            tags = merge_params(tags, replacement=override.extra_params)
        if not description_html:
            description_html = build_description_from_params(tags)
        images = dedupe_images(
            override.images,
            source_offer.images,
            supplemental_offer.images if supplemental_offer else [],
        )
        weight_kg = override.weight_kg or source_offer.weight_kg
        height_cm = override.height_cm or source_offer.height_cm
        width_cm = override.width_cm or source_offer.width_cm
        length_cm = override.length_cm or source_offer.length_cm

        add_text_node(offer_node, "id", source_offer.offer_id)
        add_text_node(offer_node, "code", code)
        add_text_node(offer_node, "vendor_code", vendor_code)
        add_text_node(offer_node, "title", title)
        add_text_node(offer_node, "barcode", barcode)
        add_text_node(offer_node, "category", category)
        add_text_node(offer_node, "category_id", category_id)
        add_text_node(offer_node, "brand", brand)
        add_text_node(offer_node, "availability", "Є в наявності")
        add_text_node(offer_node, "weight", weight_kg)
        add_text_node(offer_node, "height", height_cm)
        add_text_node(offer_node, "width", width_cm)
        add_text_node(offer_node, "length", length_cm)

        if description_html:
            description_node = ET.SubElement(offer_node, "description")
            description_node.text = description_html

        if images:
            offers_with_images += 1
            image_link_node = ET.SubElement(offer_node, "image_link")
            for image_url in images:
                add_text_node(image_link_node, "picture", image_url)

        if tags:
            tags_node = ET.SubElement(offer_node, "tags")
            for name, value in tags:
                if name and value:
                    param_node = ET.SubElement(tags_node, "param", {"name": name})
                    param_node.text = value

        collect_missing_content_fields(
            missing_required,
            source_offer,
            vendor_code=vendor_code,
            brand=brand,
            barcode=barcode,
            category=category,
            category_id=category_id,
            description_html=description_html,
            tags=tags,
            images=images,
            weight_kg=weight_kg,
            height_cm=height_cm,
            width_cm=width_cm,
            length_cm=length_cm,
        )
        exported_offers += 1

    write_xml_with_cdata(root, output_path, cdata_tags={"description"})

    if strict and missing_required:
        LOGGER.error(
            "Content XML validation failed output=%s missing_required=%s duration=%s",
            output_path,
            len(missing_required),
            format_duration(perf_counter() - started_at),
        )
        formatted = "\n".join(missing_required)
        raise ValueError(f"Missing partner-required content fields:\n{formatted}")

    LOGGER.info(
        "Generated content XML output=%s offers=%s offers_with_images=%s skipped_without_barcode=%s missing_required=%s duration=%s",
        output_path,
        exported_offers,
        offers_with_images,
        skipped_without_barcode,
        len(missing_required),
        format_duration(perf_counter() - started_at),
    )

    return Path(output_path)


def dedupe_images(*image_groups: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for group in image_groups:
        for image in group:
            normalized = image.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
    return deduped


__all__ = ["ContentOverride", "generate_content_xml"]
