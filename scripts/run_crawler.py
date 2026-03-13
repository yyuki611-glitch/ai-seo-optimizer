"""
収集モジュール エントリーポイント

Usage:
  python scripts/run_crawler.py [--target competitor|own|both]
"""
import argparse
import logging
import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
load_dotenv()

from database.connection import get_connection, initialize_db
from database.repository import upsert_site
from crawler.orchestrator import discover_urls, process_urls

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
DELAY = float(os.getenv("CRAWLER_DELAY_SECONDS", 1.0))


def load_config(path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_competitor_crawl(conn, competitors: list) -> dict:
    total = {"new": 0, "updated": 0, "unchanged": 0, "failed": 0}
    for site in competitors:
        if not site.get("enabled", True):
            continue
        site_id = upsert_site(conn, site)
        logger.info(f"=== 競合サイト: {site['site_name']} (crawl_type={site['crawl_type']}) ===")
        urls = discover_urls(site)
        logger.info(f"発見URL数: {len(urls)}")
        counts = process_urls(
            conn, urls, site_id, "competitor",
            use_playwright=bool(site.get("use_playwright")),
            delay_seconds=DELAY,
        )
        for k, v in counts.items():
            total[k] += v
        logger.info(f"{site['site_name']}: {counts}")
    return total


def run_own_crawl(conn, own: dict) -> dict:
    site_id = upsert_site(conn, own)
    logger.info(f"=== 自社サイト: {own['site_name']} (crawl_type={own['crawl_type']}) ===")
    urls = discover_urls(own)
    logger.info(f"発見URL数: {len(urls)}")
    return process_urls(conn, urls, site_id, "own", delay_seconds=DELAY)


def main():
    parser = argparse.ArgumentParser(description="AI SEO Optimizer - Crawler")
    parser.add_argument("--target", choices=["competitor", "own", "both"], default="both")
    args = parser.parse_args()

    config_dir = Path(__file__).parent.parent / "config"
    conn = get_connection()
    initialize_db(conn)

    results = {}
    if args.target in ("competitor", "both"):
        cfg = load_config(config_dir / "competitors.yaml")
        results["competitor"] = run_competitor_crawl(conn, cfg.get("sites", []))
    if args.target in ("own", "both"):
        cfg = load_config(config_dir / "own_sites.yaml")
        results["own"] = run_own_crawl(conn, cfg.get("own_site", {}))

    logger.info("=== 実行結果 ===")
    for target, counts in results.items():
        logger.info(f"[{target}] {counts}")
    conn.close()


if __name__ == "__main__":
    main()
