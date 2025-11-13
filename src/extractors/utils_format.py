import json
import logging
import os
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

def clean_price(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    # Ensure price starts with a currency symbol if one is present
    return text

def clean_score(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text

def clean_sold(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    return text

def normalize_product_link(url: str) -> str:
    if not url:
        return url
    # TikTok sometimes uses tracking params; for this example we just strip whitespace.
    return url.strip()

def load_settings(path: str) -> Dict[str, Any]:
    """
    Load scraper settings from a JSON file. If the file does not exist,
    return sensible defaults.
    """
    defaults: Dict[str, Any] = {
        "user_agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "request_timeout": 15,
    }
    if not os.path.exists(path):
        logger.warning("Settings file %s not found. Using defaults.", path)
        return defaults

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            logger.warning("Settings file %s did not contain a JSON object. Using defaults.", path)
            return defaults
        merged = {**defaults, **data}
        return merged
    except Exception as exc:
        logger.error("Failed to load settings from %s: %s. Using defaults.", path, exc)
        return defaults

def load_urls_from_file(path: str) -> List[str]:
    """
    Load TikTok Shop URLs from a newline-delimited text file.
    Empty lines and comments starting with '#' are ignored.
    """
    if not os.path.exists(path):
        logger.error("Input URLs file %s does not exist.", path)
        return []

    urls: List[str] = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            urls.append(line)
    return urls