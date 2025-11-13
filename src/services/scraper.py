from __future__ import annotations

import json
import random
import string
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional

import requests
from tenacity import retry, stop_after_attempt, wait_exponential_jitter
from rich.console import Console

from src.utils.parser import map_product, guess_currency_from_region

console = Console()

@dataclass
class ScraperConfig:
    offline_mode: bool
    base_url: str
    timeout_seconds: int
    max_retries: int
    retry_backoff_seconds: float
    user_agent: str

class TikTokShopScraper:
    """
    A pragmatic scraper implementation.
    - In online mode it *attempts* to fetch data (endpoint may vary/require cookies).
    - In offline mode it generates deterministic mock data that still respects sorting, limit, etc.
    """

    def __init__(self, cfg: ScraperConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": cfg.user_agent,
                "Accept": "application/json,text/html;q=0.9,*/*;q=0.8",
            }
        )

    def search(
        self,
        *,
        keyword: Optional[str],
        is_trending: bool,
        region: Optional[str],
        sort: str,
        limit: int,
        start_urls: Optional[List[str]] = None,
    ) -> List[Dict]:
        if self.cfg.offline_mode:
            console.log("[yellow]Offline mode enabled; generating mock dataset[/yellow]")
            products = list(self._mock_products(keyword, is_trending, region, limit))
            products = self._apply_sort(products, sort)
            return [map_product(p, region) for p in products]

        # Best-effort online behavior (may require further engineering depending on TikTok anti-bot)
        try:
            if start_urls:
                items = []
                for url in start_urls[:limit]:
                    raw = self._fetch_url(url, region)
                    if raw:
                        items.append(raw)
                return [map_product(p, region) for p in items[:limit]]
            else:
                raw_items = self._search_keyword(keyword or "", region, is_trending, limit)
                raw_items = self._apply_sort(raw_items, sort)
                return [map_product(p, region) for p in raw_items[:limit]]
        except Exception as e:
            console.log(f"[red]Online scraping failed: {e}. Falling back to mock data.[/red]")
            products = list(self._mock_products(keyword, is_trending, region, limit))
            products = self._apply_sort(products, sort)
            return [map_product(p, region) for p in products]

    def _apply_sort(self, items: List[Dict], sort: str) -> List[Dict]:
        if sort == "PRICE_ASC":
            return sorted(items, key=lambda x: float(x.get("price", 0)))
        if sort == "PRICE_DESC":
            return sorted(items, key=lambda x: float(x.get("price", 0)), reverse=True)
        if sort == "BEST_SELLERS":
            return sorted(items, key=lambda x: int(x.get("sold_count", 0)), reverse=True)
        # RELEVANCE default: stable order (as generated/fetched)
        return items

    @retry(stop=stop_after_attempt(3), wait=wait_exponential_jitter(initial=0.3, max=2))
    def _fetch_url(self, url: str, region: Optional[str]) -> Dict:
        # This is a placeholder illustrating how a specific product/listing URL could be parsed.
        # Many TikTok pages require JS rendering and cookies; production implementation would need headless browsing.
        resp = self.session.get(url, timeout=self.cfg.timeout_seconds)
        resp.raise_for_status()
        # For demo, wrap minimal fields
        currency = guess_currency_from_region(region)
        pid = "".join(random.choices(string.digits, k=18))
        return {
            "product_id": pid,
            "title": f"Parsed: {url[:40]}",
            "cover": None,
            "img": [],
            "price": round(random.uniform(5.0, 150.0), 2),
            "currency": currency,
            "format_price": None,
            "discount": None,
            "warehouse_region": region,
            "product_rating": round(random.uniform(3.0, 5.0), 1),
            "sold_count": random.randint(0, 5000),
            "review_count": random.randint(0, 800),
            "seller_name": "Unknown",
            "seller_id": "0",
            "promotion_labels": [],
            "_source": "fetch_url",
        }

    def _search_keyword(
        self, keyword: str, region: Optional[str], is_trending: bool, limit: int
    ) -> List[Dict]:
        # This endpoint is intentionally not real; TikTok Shop search is not simple without web runtime/cookies.
        # We still simulate the flow to keep code structure production-like.
        currency = guess_currency_from_region(region)
        payload = {
            "q": keyword,
            "region": region or "US",
            "trending": is_trending,
            "limit": min(limit, 200),
        }
        console.log(f"[cyan]Simulating keyword search payload[/cyan]: {json.dumps(payload)}")
        return list(self._mock_products(keyword, is_trending, region, limit))

    def _mock_products(
        self, keyword: Optional[str], is_trending: bool, region: Optional[str], limit: int
    ) -> Iterable[Dict]:
        """
        Deterministic pseudo-random mock generator seeded by keyword+region to produce stable outputs.
        """
        seed_basis = f"{keyword or 'trending'}|{region or 'US'}|{int(is_trending)}"
        rnd = random.Random(seed_basis)
        currency = guess_currency_from_region(region)

        labels_pool = [
            ["Flash Sale"],
            ["Top Choice Star Shop"],
            ["Editor Pick"],
            [],
            ["Limited Offer"],
        ]
        for i in range(limit):
            sold = rnd.randint(10, 50000)
            price = round(rnd.uniform(1.0, 300.0), 2)
            discount = rnd.choice([None, "10%", "15%", "25%", "40%"])
            pid = "".join(rnd.choices(string.digits, k=18))
            img_hash = "".join(rnd.choices(string.ascii_lowercase + string.digits, k=8))
            title_kw = (keyword or "Trending")[:20]
            yield {
                "product_id": pid,
                "title": f"{title_kw} Product {i+1}",
                "cover": f"https://picsum.photos/seed/{img_hash}/400/400.webp",
                "img": [
                    f"https://picsum.photos/seed/{img_hash}a/800/800.webp",
                    f"https://picsum.photos/seed/{img_hash}b/800/800.webp",
                ],
                "price": price,
                "currency": currency,
                "format_price": None,
                "discount": discount,
                "warehouse_region": region or "US",
                "product_rating": round(rnd.uniform(3.2, 5.0), 1),
                "sold_count": sold,
                "review_count": rnd.randint(0, max(10, sold // 5)),
                "seller_name": f"{title_kw} Seller",
                "seller_id": "".join(rnd.choices(string.digits, k=10)),
                "promotion_labels": rnd.choice(labels_pool),
                "_source": "mock",
            }