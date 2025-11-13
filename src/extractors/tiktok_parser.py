import json
import logging
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

from .utils_format import (
    clean_price,
    clean_score,
    clean_sold,
    normalize_product_link,
)

logger = logging.getLogger(__name__)

@dataclass
class Product:
    title: str
    origin_price: Optional[str]
    sale_price: Optional[str]
    score: Optional[str]
    sold: Optional[str]
    product_link: str
    img: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class TikTokShopScraper:
    """
    Lightweight TikTok Shop scraper.

    This implementation focuses on HTML parsing and JSON metadata extraction.
    It is designed to be robust to changes and to fail gracefully if the
    expected structures cannot be found.
    """

    def __init__(self, user_agent: Optional[str] = None, timeout: int = 15) -> None:
        self.session = requests.Session()
        self.timeout = timeout
        self.session.headers.update(
            {
                "User-Agent": user_agent
                or (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            }
        )

    def scrape_url(self, url: str) -> List[Dict[str, Any]]:
        """
        Decide whether URL is a product or listing URL and parse accordingly.
        """
        response = self.session.get(url, timeout=self.timeout)
        response.raise_for_status()

        html = response.text
        soup = BeautifulSoup(html, "html.parser")

        if self._looks_like_product_page(soup):
            product = self._parse_product_page(soup, url)
            return [product.to_dict()] if product else []
        else:
            return [p.to_dict() for p in self._parse_listing_page(soup, url)]

    @staticmethod
    def _looks_like_product_page(soup: BeautifulSoup) -> bool:
        """
        Heuristic check to differentiate product page vs listing.
        """
        og_type = soup.find("meta", property="og:type")
        if og_type and og_type.get("content") == "product":
            return True

        title_tag = soup.find("title")
        if title_tag and "tiktok shop" in title_tag.text.lower():
            return "product" in title_tag.text.lower()

        return bool(soup.select("meta[itemprop='price'], meta[property='product:price:amount']"))

    def _parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Product]:
        """
        Parse a single product page into a Product dataclass.
        """
        logger.debug("Parsing product page: %s", url)
        title = self._extract_title(soup)
        if not title:
            logger.warning("Could not extract title for %s", url)

        origin_price, sale_price = self._extract_prices(soup)
        score = self._extract_score(soup)
        sold = self._extract_sold(soup)
        img = self._extract_image(soup)

        return Product(
            title=title or "",
            origin_price=clean_price(origin_price),
            sale_price=clean_price(sale_price),
            score=clean_score(score),
            sold=clean_sold(sold),
            product_link=normalize_product_link(url),
            img=img,
        )

    def _parse_listing_page(self, soup: BeautifulSoup, url: str) -> List[Product]:
        """
        Parse a listing / category page. This is highly dependent on TikTok's HTML,
        so we rely on generic product card selectors and JSON blobs.
        """
        logger.debug("Parsing listing page: %s", url)

        products: List[Product] = []

        # Strategy 1: Look for JSON scripts that contain product data
        for script in soup.find_all("script"):
            script_text = script.string or ""
            if not script_text:
                continue
            if '"product"' in script_text.lower() and '"price"' in script_text.lower():
                try:
                    data = self._extract_json_from_script(script_text)
                except ValueError:
                    continue
                products.extend(self._products_from_json_blob(data, url))

        # Strategy 2: Fallback to card-based parsing
        if not products:
            card_selectors = [
                "a[href*='/product/']",
                "div[data-e2e='search-card']",
            ]
            for selector in card_selectors:
                for card in soup.select(selector):
                    product = self._product_from_card(card, url)
                    if product:
                        products.append(product)

        # De-duplicate by product_link
        unique: Dict[str, Product] = {}
        for product in products:
            if product.product_link not in unique:
                unique[product.product_link] = product

        logger.info("Parsed %d products from listing %s", len(unique), url)
        return list(unique.values())

    def _extract_json_from_script(self, text: str) -> Any:
        """
        Attempt to load JSON from a script tag content. TikTok often embeds
        window.__INIT_PROPS__ or similar structures.
        """
        # Naive approach: find first {...} block that parses as JSON.
        start = text.find("{")
        while start != -1:
            end = text.rfind("}")
            if end == -1 or end <= start:
                break
            candidate = text[start : end + 1]
            try:
                return json.loads(candidate)
            except Exception:
                end = text.rfind("}", start, end)
                if end == -1:
                    break
            start = text.find("{", start + 1)
        raise ValueError("Could not extract JSON from script block")

    def _products_from_json_blob(self, data: Any, base_url: str) -> List[Product]:
        products: List[Product] = []

        def walk(node: Any) -> None:
            if isinstance(node, dict):
                if self._looks_like_product_dict(node):
                    products.append(self._product_from_dict(node, base_url))
                for value in node.values():
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(data)
        return products

    @staticmethod
    def _looks_like_product_dict(node: Dict[str, Any]) -> bool:
        keys = {k.lower() for k in node.keys()}
        return {"title", "price"}.issubset(keys) or (
            "name" in keys and "image" in keys and ("price" in keys or "offers" in keys)
        )

    def _product_from_dict(self, node: Dict[str, Any], base_url: str) -> Product:
        title = node.get("title") or node.get("name", "")
        image = None
        if isinstance(node.get("image"), list):
            image = node["image"][0]
        elif isinstance(node.get("image"), str):
            image = node["image"]

        raw_price = None
        origin_price = None
        if isinstance(node.get("price"), (str, int, float)):
            raw_price = str(node["price"])
        elif isinstance(node.get("offers"), dict):
            raw_price = str(node["offers"].get("price"))
        origin_price = raw_price

        score = str(node.get("ratingValue") or node.get("rating", ""))
        sold = str(node.get("sold") or node.get("soldCount") or "")

        link = node.get("url") or base_url
        return Product(
            title=title,
            origin_price=clean_price(origin_price),
            sale_price=clean_price(raw_price),
            score=clean_score(score),
            sold=clean_sold(sold),
            product_link=normalize_product_link(link),
            img=image,
        )

    def _product_from_card(self, card: Any, base_url: str) -> Optional[Product]:
        title_el = card.find("span") or card.find("h3") or card.find("h2")
        title = title_el.get_text(strip=True) if title_el else ""

        price_el = card.find("span", string=lambda x: x and "$" in x)
        price = price_el.get_text(strip=True) if price_el else ""

        link_el = card.find("a", href=True)
        link = link_el["href"] if link_el else base_url

        img_el = card.find("img")
        img = img_el.get("src") if img_el else None

        score = ""
        sold = ""

        if not title and not price:
            return None

        return Product(
            title=title,
            origin_price=None,
            sale_price=clean_price(price),
            score=clean_score(score),
            sold=clean_sold(sold),
            product_link=normalize_product_link(link),
            img=img,
        )

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        og_title = soup.find("meta", property="og:title")
        if og_title and og_title.get("content"):
            return og_title["content"].strip()

        h1 = soup.find("h1")
        if h1 and h1.get_text(strip=True):
            return h1.get_text(strip=True)

        if soup.title and soup.title.string:
            return soup.title.string.strip()

        return None

    @staticmethod
    def _extract_prices(soup: BeautifulSoup) -> tuple[Optional[str], Optional[str]]:
        origin_price = None
        sale_price = None

        origin_meta = soup.find("meta", property="product:original_price:amount")
        sale_meta = soup.find("meta", property="product:price:amount")
        if origin_meta:
            origin_price = origin_meta.get("content")
        if sale_meta:
            sale_price = sale_meta.get("content")

        if not sale_price:
            # look for HTML elements with price-like text
            price_candidates = soup.find_all(
                string=lambda text: text and any(ch.isdigit() for ch in text) and "$" in text
            )
            if price_candidates:
                text = price_candidates[0].strip()
                sale_price = text

        return origin_price, sale_price

    @staticmethod
    def _extract_score(soup: BeautifulSoup) -> Optional[str]:
        rating_meta = soup.find("meta", itemprop="ratingValue")
        if rating_meta and rating_meta.get("content"):
            return rating_meta["content"]

        rating_el = soup.find(string=lambda x: x and "★" in x)
        if rating_el:
            return rating_el.strip()

        return None

    @staticmethod
    def _extract_sold(soup: BeautifulSoup) -> Optional[str]:
        sold_el = soup.find(string=lambda x: x and "sold" in x.lower())
        if sold_el:
            return sold_el.strip()
        return None

    @staticmethod
    def _extract_image(soup: BeautifulSoup) -> Optional[str]:
        og_img = soup.find("meta", property="og:image")
        if og_img and og_img.get("content"):
            return og_img["content"]

        img = soup.find("img")
        if img and img.get("src"):
            return img["src"]

        return None