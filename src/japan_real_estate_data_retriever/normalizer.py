import hashlib
from typing import Any, Dict, Iterable, Optional
from urllib.parse import urldefrag, urlsplit, urlunsplit

from .sites import get_site


UNIFIED_LISTING_FIELDS = (
    "id",
    "source",
    "source_listing_id",
    "source_url",
    "source_site_name",
    "fetched_at",
    "listing_status",
    "title",
    "property_type",
    "property_subtype",
    "transaction_type",
    "price_jpy",
    "price_text",
    "price_per_sqm_text",
    "management_fee_jpy",
    "management_fee_text",
    "repair_reserve_fund_jpy",
    "repair_reserve_fund_text",
    "repair_reserve_fund_initial_text",
    "other_fee_text",
    "deposit_key_money_text",
    "expected_annual_rent_text",
    "gross_yield_text",
    "address",
    "prefecture",
    "city",
    "ward",
    "town",
    "latitude",
    "longitude",
    "nearest_stations",
    "building_name",
    "room_number",
    "layout",
    "floor_area_sqm",
    "floor_area_text",
    "land_area_sqm",
    "land_area_text",
    "balcony_area_sqm",
    "balcony_area_text",
    "building_area_sqm",
    "building_area_text",
    "area_measurement_method",
    "floor",
    "total_floors",
    "basement_floors",
    "structure",
    "built_year",
    "built_month",
    "age_text",
    "total_units",
    "units_for_sale",
    "orientation",
    "parking",
    "rights",
    "zoning",
    "current_status",
    "building_status",
    "delivery_time",
    "management_form",
    "management_staff",
    "management_company",
    "construction_company",
    "defect_warranty",
    "defect_insurance",
    "certifications",
    "reform_renovation",
    "energy_performance",
    "insulation_performance",
    "estimated_utility_cost",
    "features",
    "equipment",
    "remarks",
    "recommended_comment",
    "sale_schedule",
    "event_info",
    "agency_name",
    "agency_phone",
    "agency_address",
    "agency_business_hours",
    "agency_holidays",
    "agency_license",
    "agency_transaction_type",
    "contact_url",
    "images",
    "floor_plan_images",
    "media",
    "image_count",
    "detail_text",
    "source_published_at",
    "source_updated_at",
    "next_update_at",
    "transaction_valid_until",
    "source_structured_fields",
    "search_metadata",
    "raw",
)


def canonical_url(url: str) -> str:
    cleaned, _fragment = urldefrag(url.strip())
    parts = urlsplit(cleaned)
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, parts.query, ""))


def canonical_listing_id(
    source: str,
    source_listing_id: Optional[str] = None,
    source_url: Optional[str] = None,
) -> str:
    site = get_site(source)
    if source_listing_id and source_listing_id.strip():
        return f"{site.source}:{source_listing_id.strip()}"
    if source_url and source_url.strip():
        digest = hashlib.sha256(canonical_url(source_url).encode("utf-8")).hexdigest()[:16]
        return f"{site.source}:url:{digest}"
    raise ValueError("Either source_listing_id or source_url is required to build a listing id.")


def empty_listing(source: str) -> Dict[str, Any]:
    site = get_site(source)
    listing = {field: None for field in UNIFIED_LISTING_FIELDS}
    listing["source"] = site.source
    listing["source_site_name"] = site.display_name
    listing["nearest_stations"] = []
    listing["features"] = []
    listing["equipment"] = []
    listing["images"] = []
    listing["floor_plan_images"] = []
    listing["media"] = []
    listing["source_structured_fields"] = []
    listing["search_metadata"] = {}
    listing["raw"] = {}
    return listing


def normalize_listing(source: str, raw_listing: Dict[str, Any]) -> Dict[str, Any]:
    listing = empty_listing(source)
    for field in UNIFIED_LISTING_FIELDS:
        if field in raw_listing:
            listing[field] = raw_listing[field]

    listing["source"] = get_site(source).source
    listing["source_site_name"] = get_site(source).display_name
    listing["source_listing_id"] = _coerce_optional_string(listing.get("source_listing_id"))
    listing["source_url"] = _coerce_optional_string(listing.get("source_url"))
    listing["id"] = canonical_listing_id(
        listing["source"],
        source_listing_id=listing["source_listing_id"],
        source_url=listing["source_url"],
    )
    listing["raw"] = raw_listing.get("raw") or raw_listing
    return listing


def normalize_many(source: str, raw_listings: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "source": get_site(source).source,
        "items": [normalize_listing(source, item) for item in raw_listings],
    }


def _coerce_optional_string(value: Any) -> Optional[str]:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
