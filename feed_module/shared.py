from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from html import escape, unescape
from html.parser import HTMLParser
from pathlib import Path
from time import perf_counter
from typing import Any, Iterable
import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

from logger import format_duration, get_logger


NON_DIGIT_RE = re.compile(r"\D+")
TAG_RE = re.compile(r"<[^>]+>")
TITLE_LABEL_RE = re.compile(r"\b(Колір|Розмір|Розміри)\s*:\s*", re.IGNORECASE)
TITLE_SIZE_RE = re.compile(r"^(?:S|M|L|XL|XXL|XXXL)$", re.IGNORECASE)
TITLE_DIAMETER_RE = re.compile(r"(?:^|[\s,(])d\s*([0-9]+(?:[.,][0-9]+)?)\s*(?:см)?$", re.IGNORECASE)
FORBIDDEN_SECTION_PREFIXES = (
    "комплектац",
    "гарантія",
    "доставка",
    "оплата",
    "контакт",
)
FORBIDDEN_BLOCK_PREFIXES = (
    "комплектац",
    "гарантія",
    "доставка",
    "оплата",
    "контакт",
)
BARCODE_PARAM_NAMES = {
    "barcode",
    "ean",
    "ean13",
    "ean-13",
    "штрихкод",
    "штрих-код",
    "баркод",
}
BRAND_PARAM_NAMES = {
    "brand",
    "бренд",
    "виробник",
}
WEIGHT_PARAM_NAMES = {
    "вага в упаковці",
    "вага упаковки",
    "weight in package",
    "package weight",
}
HEIGHT_PARAM_NAMES = {"висота в упаковці", "package height"}
WIDTH_PARAM_NAMES = {"ширина в упаковці", "package width"}
LENGTH_PARAM_NAMES = {"довжина в упаковці", "package length", "глибина в упаковці"}
DEFAULT_DELIVERY_METHODS = [
    {"method": "nova-post:branch", "price": 0},
    {"method": "nova-post:cargo_branch", "price": 0},
    {"method": "nova-post:postomat", "price": 0},
    {"method": "courier:nova-post", "price": 0},
]


LOGGER = get_logger(__name__)


@dataclass(slots=True)
class SourceOffer:
    offer_id: str
    title: str
    vendor_code: str | None
    category_id: str | None
    category_name: str | None
    price: int | None
    old_price: int | None
    quantity_in_stock: int
    available: bool
    description_html: str
    brand: str | None = None
    barcode: str | None = None
    images: list[str] = field(default_factory=list)
    params: list[tuple[str, str]] = field(default_factory=list)
    weight_kg: str | None = None
    height_cm: str | None = None
    width_cm: str | None = None
    length_cm: str | None = None


@dataclass(slots=True)
class ContentOverride:
    code: str | None = None
    barcode: str | None = None
    brand: str | None = None
    category: str | None = None
    category_id: str | None = None
    weight_kg: str | None = None
    height_cm: str | None = None
    width_cm: str | None = None
    length_cm: str | None = None
    images: list[str] = field(default_factory=list)
    extra_params: list[tuple[str, str]] = field(default_factory=list)


@dataclass(slots=True)
class PropositionOverride:
    code: str | None = None
    price: int | None = None
    old_price: int | None = None
    availability: bool | None = None
    warranty_type: str = "no"
    warranty_period: int = 0
    max_pay_in_parts: int = 3
    days_to_dispatch: int = 1
    delivery_methods: list[dict[str, Any]] = field(
        default_factory=lambda: [method.copy() for method in DEFAULT_DELIVERY_METHODS]
    )
    multiplicity: int | None = None
    country_code: str | None = None
    manufacture_year: int | None = None


class DescriptionSanitizer(HTMLParser):
    """Reduce source HTML to the subset accepted by the partner feed."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=False)
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._append_start_tag(tag, attrs)

    def handle_startendtag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized = self._normalize_tag(tag)
        if normalized == "br":
            self.parts.append("<br>")
            return
        if normalized == "img":
            self.parts.append(self._render_img(attrs))

    def handle_endtag(self, tag: str) -> None:
        normalized = self._normalize_tag(tag)
        if normalized in {"h5", "p", "ul", "li"}:
            self.parts.append(f"</{normalized}>")

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.parts.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.parts.append(f"&#{name};")

    def get_html(self) -> str:
        return "".join(self.parts)

    def _append_start_tag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        normalized = self._normalize_tag(tag)
        if normalized in {"h5", "p", "ul", "li"}:
            self.parts.append(f"<{normalized}>")
        elif normalized == "br":
            self.parts.append("<br>")
        elif normalized == "img":
            self.parts.append(self._render_img(attrs))

    @staticmethod
    def _normalize_tag(tag: str) -> str | None:
        lowered = tag.lower()
        if lowered in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            return "h5"
        if lowered == "ol":
            return "ul"
        if lowered == "pre":
            return "p"
        if lowered in {"p", "ul", "li", "br", "img"}:
            return lowered
        return None

    @staticmethod
    def _render_img(attrs: list[tuple[str, str | None]]) -> str:
        values = {name.lower(): value or "" for name, value in attrs}
        src = values.get("src", "").strip()
        if not src:
            return ""
        alt = values.get("alt", "").strip()
        escaped_alt = escape(alt, quote=True)
        escaped_src = escape(src, quote=True)
        return f'<img alt="{escaped_alt}" src="{escaped_src}">'


def parse_source_yml(source_path: str | Path) -> list[SourceOffer]:
    """Read the source YML feed and return normalized offers."""
    started_at = perf_counter()
    source_path = Path(source_path)
    LOGGER.info("Parsing source feed path=%s", source_path)
    tree = ET.parse(source_path)
    root = tree.getroot()
    shop = root.find("shop")
    if shop is None:
        raise ValueError(f"{source_path} does not contain a <shop> node")

    categories: dict[str, str] = {}
    for category_node in shop.findall("./categories/category"):
        category_id = (category_node.get("id") or "").strip()
        if category_id:
            categories[category_id] = clean_text(category_node.text)

    offers: list[SourceOffer] = []
    offers_with_images = 0
    available_offers = 0
    for offer_node in shop.findall("./offers/offer"):
        quantity = parse_int(
            offer_node.findtext("quantity_in_stock")
            or offer_node.findtext("stock_quantity")
        ) or 0
        available = (offer_node.get("available") or "").strip().lower() == "true"
        category_id = clean_text(offer_node.findtext("categoryId")) or None
        params = extract_source_params(offer_node)
        vendor_code = clean_text(offer_node.findtext("vendorCode")) or find_param_value(
            params,
            {"артикул", "vendorcode", "vendor_code", "sku", "article"},
        )

        offers.append(
            SourceOffer(
                offer_id=(offer_node.get("id") or "").strip(),
                title=clean_text(offer_node.findtext("name")),
                vendor_code=vendor_code or None,
                category_id=category_id,
                category_name=categories.get(category_id or ""),
                price=parse_int(offer_node.findtext("price")),
                old_price=parse_int(
                    offer_node.findtext("oldprice")
                    or offer_node.findtext("oldPrice")
                    or offer_node.findtext("price_old")
                ),
                quantity_in_stock=quantity,
                available=available and quantity > 0,
                description_html=(offer_node.findtext("description") or "").strip(),
                brand=extract_source_brand(offer_node, params),
                barcode=extract_source_barcode(offer_node, params),
                images=extract_source_images(offer_node),
                params=params,
                weight_kg=extract_source_measure(
                    offer_node,
                    "weight",
                    params,
                    WEIGHT_PARAM_NAMES,
                ),
                height_cm=extract_source_measure(
                    offer_node,
                    "height",
                    params,
                    HEIGHT_PARAM_NAMES,
                ),
                width_cm=extract_source_measure(
                    offer_node,
                    "width",
                    params,
                    WIDTH_PARAM_NAMES,
                ),
                length_cm=extract_source_measure(
                    offer_node,
                    "length",
                    params,
                    LENGTH_PARAM_NAMES,
                    fallback_tags=("depth",),
                ),
            )
        )
        if offers[-1].images:
            offers_with_images += 1
        if offers[-1].available:
            available_offers += 1

    LOGGER.info(
        "Parsed source feed path=%s categories=%s offers=%s available_offers=%s offers_with_images=%s duration=%s",
        source_path,
        len(categories),
        len(offers),
        available_offers,
        offers_with_images,
        format_duration(perf_counter() - started_at),
    )
    return offers


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    return unescape(value).replace("\xa0", " ").strip()


def parse_int(value: str | None) -> int | None:
    cleaned = clean_text(value)
    if not cleaned:
        return None
    digits = NON_DIGIT_RE.sub("", cleaned)
    return int(digits) if digits else None


def stringify_number(value: Any) -> str | None:
    if value is None:
        return None
    return str(value)


def stringify_bool(value: bool | None) -> str | None:
    if value is None:
        return None
    return "true" if value else "false"


def add_text_node(parent: ET.Element, tag: str, value: str | None) -> None:
    if value in (None, ""):
        return
    node = ET.SubElement(parent, tag)
    node.text = value


def normalize_title(value: str) -> str:
    title = re.sub(r"\s+", " ", value).strip()
    title = TITLE_LABEL_RE.sub(lambda match: f"{match.group(1)}: ", title)
    title = re.sub(r"\(\s+", "(", title)
    title = re.sub(r"\s+\)", ")", title)
    return title[:100]


def normalize_description(html: str) -> str:
    html = html.strip()
    if not html:
        return ""

    sanitizer = DescriptionSanitizer()
    sanitizer.feed(html)
    sanitizer.close()

    sanitized = sanitizer.get_html()
    sanitized = remove_forbidden_description_sections(sanitized)
    sanitized = cleanup_description_html(sanitized)
    return sanitized


def extract_brand(description_html: str) -> str | None:
    patterns = (
        r"Виробник\s*:?\s*</h[1-6]>\s*<p[^>]*>(.*?)</p>",
        r"Бренд\s*:?\s*</h[1-6]>\s*<p[^>]*>(.*?)</p>",
        r"бренду\s+([A-Za-z][A-Za-z0-9&.' -]+)",
    )
    for pattern in patterns:
        match = re.search(pattern, description_html, flags=re.IGNORECASE | re.DOTALL)
        if match:
            brand = text_from_html(match.group(1))
            if brand:
                return brand
    return None


def build_inferred_brand_lookup(offers: Iterable[SourceOffer]) -> dict[str, str]:
    single_counts: Counter[str] = Counter()
    pair_counts: Counter[str] = Counter()
    single_display: dict[str, str] = {}
    pair_display: dict[str, str] = {}
    candidates_by_offer: dict[str, tuple[str | None, str | None]] = {}

    for offer in offers:
        single, pair = extract_title_brand_candidates(offer.title)
        candidates_by_offer[offer.offer_id] = (single, pair)
        if single:
            key = single.lower()
            single_counts[key] += 1
            single_display.setdefault(key, single)
        if pair:
            key = pair.lower()
            pair_counts[key] += 1
            pair_display.setdefault(key, pair)

    inferred: dict[str, str] = {}
    for offer in offers:
        if offer.brand or extract_brand(offer.description_html):
            continue

        single, pair = candidates_by_offer[offer.offer_id]
        if pair and pair_counts[pair.lower()] >= 2:
            inferred[offer.offer_id] = pair_display[pair.lower()]
        elif single and single_counts[single.lower()] >= 3:
            inferred[offer.offer_id] = single_display[single.lower()]
    return inferred


def extract_tags(description_html: str) -> list[tuple[str, str]]:
    candidates: list[str] = []
    candidates.extend(
        text_from_html(item)
        for item in re.findall(r"<li[^>]*>(.*?)</li>", description_html, re.I | re.S)
    )

    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", description_html, re.I | re.S)
    for paragraph_html in paragraphs:
        paragraph_html = re.sub(r"<br\s*/?>", "\n", paragraph_html, flags=re.IGNORECASE)
        for line in split_candidate_lines(text_from_html(paragraph_html)):
            normalized = line.lstrip()
            if normalized.startswith("-") or ":" in normalized or " - " in normalized:
                candidates.append(line)

    tags: list[tuple[str, str]] = []
    for candidate in candidates:
        tag = split_param(candidate)
        if tag:
            tags.append(tag)
    return tags


def extract_title_params(title: str) -> list[tuple[str, str]]:
    normalized_title = normalize_title(title)
    params: list[tuple[str, str]] = []

    label_patterns = (
        ("Колір", re.compile(r"\bКолір\s*:?\s*(.+)$", re.IGNORECASE)),
        ("Розмір", re.compile(r"\bРозмір\s*:?\s*(.+)$", re.IGNORECASE)),
        ("Розміри", re.compile(r"\bРозміри\s*:?\s*(.+)$", re.IGNORECASE)),
    )
    for name, pattern in label_patterns:
        match = pattern.search(normalized_title)
        if not match:
            continue
        value = clean_text(match.group(1)).strip(" ,.;")
        if value:
            params.append((name, value))

    diameter_match = TITLE_DIAMETER_RE.search(normalized_title)
    if diameter_match:
        params.append(("Діаметр", diameter_match.group(1).replace(".", ",")))

    return dedupe_params(params)


def enrich_description_with_title_params(
    description_html: str,
    title_params: list[tuple[str, str]],
) -> str:
    if not title_params:
        return description_html

    description_text = normalize_inline_text(text_from_html(description_html)).lower()
    missing_params = [
        (name, value)
        for name, value in title_params
        if normalize_inline_text(value).lower() not in description_text
    ]
    if not missing_params:
        return description_html

    if not description_html:
        items = "".join(
            f"<li>{escape(name, quote=False)}: {escape(value, quote=False)}</li>"
            for name, value in missing_params
        )
        return f"<h5>Характеристики:</h5><ul>{items}</ul>"

    additions = "".join(
        f"<p>{escape(name, quote=False)}: {escape(value, quote=False)}</p>"
        for name, value in missing_params
    )
    return f"{description_html}{additions}"


def build_description_from_params(params: list[tuple[str, str]]) -> str:
    if not params:
        return ""
    items = "".join(
        f"<li>{escape(name, quote=False)}: {escape(value, quote=False)}</li>"
        for name, value in params[:8]
    )
    return f"<h5>Характеристики:</h5><ul>{items}</ul>"


def fallback_type_from_title(title: str) -> str | None:
    normalized_title = normalize_title(title)
    normalized_title = re.sub(r"\bКолір\s*:?\s*.+$", "", normalized_title, flags=re.IGNORECASE)
    normalized_title = re.sub(r"\bРозмір\s*:?\s*.+$", "", normalized_title, flags=re.IGNORECASE)
    normalized_title = re.sub(r"\bРозміри\s*:?\s*.+$", "", normalized_title, flags=re.IGNORECASE)
    normalized_title = re.sub(r"(?:^|[\s,(])d\s*[0-9]+(?:[.,][0-9]+)?\s*(?:см)?$", "", normalized_title, flags=re.IGNORECASE)
    normalized_title = re.sub(r"\s+", " ", normalized_title).strip(" ,.;")
    if not normalized_title:
        return None
    return normalized_title


def merge_params(
    primary: Iterable[tuple[str, str]],
    secondary: Iterable[tuple[str, str]] = (),
    replacement: Iterable[tuple[str, str]] = (),
) -> list[tuple[str, str]]:
    merged = dedupe_params(list(primary) + list(secondary))
    replacement_list = dedupe_params(list(replacement))
    if not replacement_list:
        return merged

    replacement_names = {normalize_param_name(name) for name, _ in replacement_list}
    filtered = [
        (name, value)
        for name, value in merged
        if normalize_param_name(name) not in replacement_names
    ]
    return dedupe_params(filtered + replacement_list)


def split_candidate_lines(value: str) -> Iterable[str]:
    for line in re.split(r"[\n\r]+", value):
        stripped = line.strip(" \u2022\t")
        if stripped:
            yield stripped


def split_param(value: str) -> tuple[str, str] | None:
    text = normalize_inline_text(value)
    if not text:
        return None

    if ":" in text:
        key, raw_value = text.split(":", 1)
        key = key.strip(" -")
        raw_value = raw_value.strip()
        if is_valid_param(key, raw_value):
            return key, raw_value

    if text.startswith("-") and "-" in text[1:]:
        key, raw_value = text[1:].split("-", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if is_valid_param(key, raw_value):
            return key, raw_value

    if re.match(r"^[^-\n]{1,40}-\s*.+$", text):
        key, raw_value = text.split("-", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if is_valid_param(key, raw_value):
            return key, raw_value
    return None


def text_from_html(value: str) -> str:
    text = TAG_RE.sub("", value)
    return clean_text(text)


def collect_missing_content_fields(
    missing: list[str],
    source_offer: SourceOffer,
    *,
    vendor_code: str | None,
    brand: str | None,
    barcode: str | None,
    category: str | None,
    category_id: str | None,
    description_html: str | None,
    tags: list[tuple[str, str]],
    images: list[str],
    weight_kg: str | None,
    height_cm: str | None,
    width_cm: str | None,
    length_cm: str | None,
) -> None:
    required_checks = {
        "vendor_code": vendor_code,
        "brand": brand,
        "barcode": barcode,
        "category": category,
        "category_id": category_id,
        "description": description_html,
        "image_link": images[0] if images else None,
        "tags": tags[0] if tags else None,
        "weight": weight_kg,
        "height": height_cm,
        "width": width_cm,
        "length": length_cm,
    }
    for field_name, value in required_checks.items():
        if value in (None, "", []):
            missing.append(f"offer {source_offer.offer_id}: content.{field_name} is required")


def write_xml_with_cdata(
    root: ET.Element,
    output_path: str | Path,
    *,
    cdata_tags: set[str],
) -> None:
    raw_xml = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    document = minidom.parseString(raw_xml)

    for tag_name in cdata_tags:
        for node in document.getElementsByTagName(tag_name):
            text_value = "".join(
                child.data
                for child in list(node.childNodes)
                if child.nodeType == child.TEXT_NODE
            )
            while node.firstChild:
                node.removeChild(node.firstChild)
            if text_value:
                node.appendChild(document.createCDATASection(text_value))

    pretty_bytes = document.toprettyxml(indent="    ", encoding="utf-8")
    pretty_text = "\n".join(
        line for line in pretty_bytes.decode("utf-8").splitlines() if line.strip()
    )
    Path(output_path).write_text(pretty_text + "\n", encoding="utf-8")


def cleanup_description_html(html: str) -> str:
    html = re.sub(r"<p>\s*(?:&nbsp;|\s|<br>)*</p>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<li>\s*(?:&nbsp;|\s|<br>)*</li>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"<ul>\s*</ul>", "", html, flags=re.IGNORECASE)
    html = re.sub(r"(?:<br>\s*){3,}", "<br><br>", html, flags=re.IGNORECASE)
    html = re.sub(r"\s+</", "</", html)
    html = re.sub(r">\s+<", "><", html)
    return html.strip()


def remove_forbidden_description_sections(html: str) -> str:
    headings = list(re.finditer(r"<h5>(.*?)</h5>", html, flags=re.IGNORECASE | re.DOTALL))
    if not headings:
        return remove_forbidden_blocks(html)

    parts: list[str] = []
    if headings[0].start() > 0:
        parts.append(remove_forbidden_blocks(html[: headings[0].start()]))

    for index, match in enumerate(headings):
        next_start = headings[index + 1].start() if index + 1 < len(headings) else len(html)
        section_html = html[match.start() : next_start]
        heading_text = normalize_inline_text(text_from_html(match.group(1))).lower()
        if any(heading_text.startswith(prefix) for prefix in FORBIDDEN_SECTION_PREFIXES):
            continue
        parts.append(remove_forbidden_blocks(section_html))
    return "".join(parts)


def remove_forbidden_blocks(html: str) -> str:
    block_pattern = re.compile(
        r"<p>.*?</p>|<li>.*?</li>|<img\b[^>]*>",
        flags=re.IGNORECASE | re.DOTALL,
    )

    def replace_block(match: re.Match[str]) -> str:
        block = match.group(0)
        block_text = normalize_inline_text(text_from_html(block)).lower().strip(" :")
        if any(block_text.startswith(prefix) for prefix in FORBIDDEN_BLOCK_PREFIXES):
            return ""
        if "http://" in block_text or "https://" in block_text or "www." in block_text:
            return ""
        if "телефон" in block_text or "e-mail" in block_text or "email" in block_text:
            return ""
        return block

    return block_pattern.sub(replace_block, html)


def extract_source_params(offer_node: ET.Element) -> list[tuple[str, str]]:
    params: list[tuple[str, str]] = []
    for param_node in offer_node.findall("param"):
        name = clean_text(param_node.get("name"))
        value = clean_text(param_node.text)
        if name and value:
            params.append((name, value))
    return dedupe_params(params)


def extract_source_images(offer_node: ET.Element) -> list[str]:
    images: list[str] = []
    for picture_node in offer_node.findall("picture"):
        image = clean_text(picture_node.text)
        if image:
            images.append(image)
    return images


def extract_source_brand(
    offer_node: ET.Element,
    params: list[tuple[str, str]],
) -> str | None:
    direct = clean_text(offer_node.findtext("vendor") or offer_node.findtext("brand"))
    if direct:
        return direct
    return find_param_value(params, BRAND_PARAM_NAMES)


def extract_source_barcode(
    offer_node: ET.Element,
    params: list[tuple[str, str]],
) -> str | None:
    direct = clean_text(offer_node.findtext("barcode"))
    if direct:
        return direct
    return find_param_value(params, BARCODE_PARAM_NAMES)


def resolve_offer_barcode(
    source_offer: SourceOffer,
    *,
    override_barcode: str | None = None,
    supplemental_offer_by_id: SourceOffer | None = None,
) -> str | None:
    if override_barcode:
        return override_barcode
    if source_offer.barcode:
        return source_offer.barcode
    if supplemental_offer_by_id and supplemental_offer_by_id.barcode:
        return supplemental_offer_by_id.barcode
    return None


def extract_source_measure(
    offer_node: ET.Element,
    primary_tag: str,
    params: list[tuple[str, str]],
    param_names: set[str],
    *,
    fallback_tags: tuple[str, ...] = (),
) -> str | None:
    direct = clean_text(offer_node.findtext(primary_tag))
    if direct:
        return direct
    for tag_name in fallback_tags:
        fallback = clean_text(offer_node.findtext(tag_name))
        if fallback:
            return fallback
    return find_param_value(params, param_names)


def find_param_value(
    params: Iterable[tuple[str, str]],
    names: set[str],
) -> str | None:
    normalized_names = {normalize_param_name(name) for name in names}
    for name, value in params:
        if normalize_param_name(name) in normalized_names and value:
            return value
    return None


def normalize_param_name(value: str) -> str:
    return normalize_inline_text(value).lower()


def normalize_inline_text(value: str) -> str:
    return re.sub(r"\s+", " ", clean_text(value)).strip()


def dedupe_params(params: Iterable[tuple[str, str]]) -> list[tuple[str, str]]:
    seen: set[tuple[str, str]] = set()
    deduped: list[tuple[str, str]] = []
    for name, value in params:
        normalized_name = normalize_inline_text(name)
        normalized_value = normalize_inline_text(value)
        if not normalized_name or not normalized_value:
            continue
        key = (normalized_name.lower(), normalized_value.lower())
        if key in seen:
            continue
        seen.add(key)
        deduped.append((normalized_name, normalized_value))
    return deduped


def is_valid_param(key: str, raw_value: str) -> bool:
    key = normalize_inline_text(key)
    raw_value = normalize_inline_text(raw_value)
    if not key or not raw_value:
        return False
    if len(key) > 60 or len(raw_value) > 200:
        return False
    if len(key.split()) > 6:
        return False
    if key.lower() in {"опис", "характеристики", "виробник"}:
        return False
    if any(key.lower().startswith(prefix) for prefix in FORBIDDEN_BLOCK_PREFIXES):
        return False
    return True


def extract_title_brand_candidates(title: str) -> tuple[str | None, str | None]:
    runs = re.findall(r"[A-Za-z][A-Za-z0-9&.'-]*(?:\s+[A-Za-z][A-Za-z0-9&.'-]*)*", title)
    for run in runs:
        tokens: list[str] = []
        for token in run.split():
            cleaned = token.strip(".,")
            if "_" in cleaned:
                break
            if re.fullmatch(r"[dx]?\d+[A-Za-z0-9.-]*", cleaned, flags=re.IGNORECASE):
                break
            if TITLE_SIZE_RE.fullmatch(cleaned):
                break
            tokens.append(cleaned)
            if len(tokens) == 2:
                break
        if not tokens:
            continue
        single = tokens[0]
        pair = " ".join(tokens[:2]) if len(tokens) > 1 else None
        return single, pair
    return None, None


__all__ = [
    "ContentOverride",
    "DEFAULT_DELIVERY_METHODS",
    "PropositionOverride",
    "SourceOffer",
    "add_text_node",
    "build_inferred_brand_lookup",
    "collect_missing_content_fields",
    "build_description_from_params",
    "enrich_description_with_title_params",
    "extract_brand",
    "extract_tags",
    "extract_title_params",
    "fallback_type_from_title",
    "merge_params",
    "normalize_description",
    "normalize_title",
    "parse_source_yml",
    "resolve_offer_barcode",
    "stringify_bool",
    "stringify_number",
    "write_xml_with_cdata",
]
