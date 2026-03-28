from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import Mapping

from logger import format_duration, get_logger
from .shared import (
    PropositionOverride,
    SourceOffer,
    parse_source_yml,
    resolve_offer_barcode,
    write_json_pretty,
)


LOGGER = get_logger(__name__)


def generate_propositions_xml(
    source_path: str | Path,
    output_path: str | Path,
    overrides: Mapping[str, PropositionOverride] | None = None,
    *,
    supplemental_source_path: str | Path | None = None,
    strict: bool = False,
) -> Path:
    """
    Generate the propositions feed as JSON.

    The PDF in instructions/propositions.pdf documents a JSON structure with:
    {"total": int, "data": [...]}
    """
    started_at = perf_counter()
    LOGGER.info(
        "Generating propositions JSON source=%s output=%s supplemental=%s strict=%s",
        source_path,
        output_path,
        supplemental_source_path,
        strict,
    )
    overrides = overrides or {}
    offers = parse_source_yml(source_path)
    supplemental_by_id: dict[str, SourceOffer] = {}
    if supplemental_source_path:
        supplemental_offers = parse_source_yml(supplemental_source_path)
        supplemental_by_id = {
            offer.offer_id: offer for offer in supplemental_offers if offer.offer_id
        }
    missing_required: list[str] = []
    data_payload: list[dict[str, object]] = []
    total = 0
    offers_with_old_price = 0
    skipped_without_barcode = 0

    for source_offer in offers:
        supplemental_offer_by_id = supplemental_by_id.get(source_offer.offer_id)
        barcode = resolve_offer_barcode(
            source_offer,
            supplemental_offer_by_id=supplemental_offer_by_id,
        )
        if not barcode:
            skipped_without_barcode += 1
            continue

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
        if old_price is not None:
            offers_with_old_price += 1

        data_payload.append(
            {
                "code": code,
                "price": price,
                "old_price": old_price,
                "availability": availability,
                "warranty_type": override.warranty_type,
                "warranty_period": override.warranty_period,
                "max_pay_in_parts": override.max_pay_in_parts,
                "delivery_methods": [
                    {
                        "method": delivery_method.get("method"),
                        "price": delivery_method.get("price"),
                    }
                    for delivery_method in override.delivery_methods
                ],
                "days_to_dispatch": override.days_to_dispatch,
                "checkout_constraints": (
                    {"multiplicity": override.multiplicity}
                    if override.multiplicity is not None
                    else None
                ),
                "manufacture": (
                    {
                        "country_code": override.country_code,
                        "year": override.manufacture_year,
                    }
                    if override.country_code or override.manufacture_year is not None
                    else None
                ),
            }
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

    write_json_pretty({"total": total, "data": data_payload}, output_path)

    if strict and missing_required:
        LOGGER.error(
            "Propositions JSON validation failed output=%s missing_required=%s duration=%s",
            output_path,
            len(missing_required),
            format_duration(perf_counter() - started_at),
        )
        formatted = "\n".join(missing_required)
        raise ValueError(f"Missing partner-required proposition fields:\n{formatted}")

    LOGGER.info(
        "Generated propositions JSON output=%s offers=%s offers_with_old_price=%s skipped_without_barcode=%s missing_required=%s duration=%s",
        output_path,
        total,
        offers_with_old_price,
        skipped_without_barcode,
        len(missing_required),
        format_duration(perf_counter() - started_at),
    )

    return Path(output_path)


__all__ = ["PropositionOverride", "generate_propositions_xml"]
