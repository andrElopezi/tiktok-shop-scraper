from typing import Any, Dict, List
from dateutil import parser as dtparser
from datetime import datetime

def normalize_price(value: Any) -> float:
    """
    Convert various price representations to float.
    """
    if value is None:
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value)
    digits = "".join(ch for ch in s if ch.isdigit() or ch == "." or ch == ",")
    digits = digits.replace(",", "")
    try:
        return float(digits)
    except ValueError:
        return 0.0

def guess_currency_from_region(region: str | None) -> str:
    mapping = {
        "US": "USD",
        "VN": "VND",
        "GB": "GBP",
        "EU": "EUR",
        "PK": "PKR",
        "ID": "IDR",
        "MY": "MYR",
        "TH": "THB",
        "PH": "PHP",
    }
    if not region:
        return "USD"
    return mapping.get(region.upper(), "USD")

def to_iso8601(dt: Any | None) -> str | None:
    if not dt:
        return None
    if isinstance(dt, (int, float)):
        # assume epoch seconds
        return datetime.utcfromtimestamp(float(dt)).isoformat() + "Z"
    if isinstance(dt, str):
        try:
            return dtparser.parse(dt).isoformat()
        except Exception:
            return None
    if isinstance(dt, datetime):
        return dt.isoformat()
    return None

def map_product(raw: Dict[str, Any], region: str | None = None) -> Dict[str, Any]:
    """
    Map a raw product dict (from provider or mock) into the canonical schema.
    """
    currency = raw.get("currency") or guess_currency_from_region(region)
    images: List[str] = raw.get("img") or raw.get("images") or []
    if isinstance(images, str):
        images = [images]

    return {
        "product_id": str(raw.get("product_id") or raw.get("id") or ""),
        "title": raw.get("title") or raw.get("name") or "",
        "cover": raw.get("cover") or (images[0] if images else None),
        "img": images,
        "price": normalize_price(raw.get("price") or raw.get("min_price") or 0),
        "currency": currency,
        "format_price": raw.get("format_price") or f"{normalize_price(raw.get('price')):.2f} {currency}",
        "discount": raw.get("discount"),
        "warehouse_region": raw.get("warehouse_region") or raw.get("ship_from"),
        "product_rating": str(raw.get("product_rating") or raw.get("rating") or ""),
        "sold_count": int(raw.get("sold_count") or raw.get("sold") or 0),
        "review_count": int(raw.get("review_count") or raw.get("reviews") or 0),
        "seller_name": raw.get("seller_name") or raw.get("shop_name") or "",
        "seller_id": str(raw.get("seller_id") or raw.get("shop_id") or ""),
        "promotion_labels": raw.get("promotion_labels") or raw.get("badges") or [],
        "created_at": to_iso8601(raw.get("created_at")),
        "last_seen_at": to_iso8601(raw.get("last_seen_at")),
        "_source": raw.get("_source") or "mock",
    }