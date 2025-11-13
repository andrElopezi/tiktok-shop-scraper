import argparse
import json
from pathlib import Path
from typing import Any, Dict

from rich.console import Console
from rich.table import Table

from src.utils.validator import validate_input
from src.services.scraper import TikTokShopScraper, ScraperConfig
from src.services.exporter import export_json

console = Console()

def load_settings(path: str | Path) -> Dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Settings file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def main():
    parser = argparse.ArgumentParser(
        description="TikTok Shop Scraper — extract product data into JSON"
    )
    parser.add_argument(
        "--input",
        type=str,
        default="data/sample_input.json",
        help="Path to input JSON with parameters",
    )
    parser.add_argument(
        "--settings",
        type=str,
        default="src/config/settings.json",
        help="Path to settings JSON",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/example_output.json",
        help="Where to save the output JSON",
    )
    parser.add_argument(
        "--print",
        action="store_true",
        help="Print a small table preview of the results",
    )
    args = parser.parse_args()

    # Load config/settings
    settings = load_settings(args.settings)
    cfg = ScraperConfig(
        offline_mode=bool(settings.get("offline_mode", True)),
        base_url=str(settings.get("base_url")),
        timeout_seconds=int(settings.get("timeout_seconds", 15)),
        max_retries=int(settings.get("max_retries", 3)),
        retry_backoff_seconds=float(settings.get("retry_backoff_seconds", 0.5)),
        user_agent=str(settings.get("user_agent")),
    )

    # Load and validate input
    raw_input = {}
    input_path = Path(args.input)
    if input_path.exists():
        with input_path.open("r", encoding="utf-8") as f:
            raw_input = json.load(f)
    params = validate_input(raw_input)

    # Run scraper
    scraper = TikTokShopScraper(cfg)
    items = scraper.search(
        keyword=params.keyword,
        is_trending=params.isTrending,
        region=params.region or settings.get("default_region"),
        sort=params.sortType or settings.get("default_sort", "RELEVANCE"),
        limit=params.limit,
        start_urls=params.startUrls,
    )

    # Export
    export_json(items, args.output)

    if args.print:
        preview = items[: min(10, len(items))]
        table = Table(title="TikTok Shop Scraper — Preview")
        table.add_column("product_id", overflow="fold")
        table.add_column("title", overflow="fold")
        table.add_column("price")
        table.add_column("currency")
        table.add_column("seller_name", overflow="fold")
        for it in preview:
            table.add_row(
                it.get("product_id", ""),
                it.get("title", ""),
                str(it.get("price", "")),
                it.get("currency", ""),
                it.get("seller_name", ""),
            )
        console.print(table)

    console.log("[green]Done.[/green]")

if __name__ == "__main__":
    main()