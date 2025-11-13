import argparse
import json
import logging
import os
import sys
from typing import List, Dict, Any

# Ensure local packages can be imported when running as a script
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from extractors.tiktok_parser import TikTokShopScraper
from outputs.exporters import export_data
from extractors.utils_format import load_urls_from_file, load_settings

def configure_logging(verbosity: int) -> None:
    level = logging.WARNING
    if verbosity == 1:
        level = logging.INFO
    elif verbosity >= 2:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="TikTok Shop scraper - extract product details from TikTok Shop URLs."
    )
    parser.add_argument(
        "-i",
        "--input-file",
        type=str,
        default=os.path.join(os.path.dirname(CURRENT_DIR), "data", "input_urls.sample.txt"),
        help="Path to a text file containing TikTok Shop URLs (one per line). "
             "Defaults to data/input_urls.sample.txt",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=os.path.join(os.path.dirname(CURRENT_DIR), "data", "sample_output.json"),
        help="Output file path. Defaults to data/sample_output.json",
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "csv", "xlsx", "html", "xml"],
        default="json",
        help="Output format. One of json, csv, xlsx, html, xml. Defaults to json.",
    )
    parser.add_argument(
        "-s",
        "--settings",
        type=str,
        default=os.path.join(CURRENT_DIR, "config", "settings.example.json"),
        help="Path to settings JSON file. Defaults to src/config/settings.example.json",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase verbosity (-v for INFO, -vv for DEBUG).",
    )
    return parser.parse_args(argv)

def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    configure_logging(args.verbose)
    logger = logging.getLogger("runner")

    logger.info("Loading settings from %s", args.settings)
    settings = load_settings(args.settings)

    logger.info("Loading URLs from %s", args.input_file)
    urls = load_urls_from_file(args.input_file)
    if not urls:
        logger.error("No URLs found in %s. Exiting.", args.input_file)
        sys.exit(1)

    scraper = TikTokShopScraper(
        user_agent=settings.get("user_agent"),
        timeout=settings.get("request_timeout", 15),
    )

    all_products: List[Dict[str, Any]] = []
    for url in urls:
        try:
            logger.info("Scraping URL: %s", url)
            products = scraper.scrape_url(url)
            logger.info("Found %d products from %s", len(products), url)
            all_products.extend(products)
        except Exception as exc:
            logger.exception("Failed to scrape %s: %s", url, exc)

    if not all_products:
        logger.warning("No products were extracted from the provided URLs.")

    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    logger.info("Exporting %d products to %s (%s)", len(all_products), args.output, args.format)
    export_data(all_products, args.output, args.format)

    logger.info("Done. Exported %d products.", len(all_products))

if __name__ == "__main__":
    main()