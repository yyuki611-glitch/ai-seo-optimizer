"""
収集フローのオーケストレーター。
サイト設定の crawl_type に基づいて URL 発見戦略を切り替え、
HTML取得 → 本文抽出 → ハッシュ判定 → DB保存 を実行する。
"""
import json
import logging
import time
from typing import List, Dict, Any

from crawler.fetchers.sitemap_fetcher import fetch_urls_from_sitemap
from crawler.fetchers.pagination_fetcher import fetch_urls_from_pagination
from crawler.fetchers.single_page_fetcher import fetch_urls_from_single_page
from crawler.html_fetcher import fetch_html
from crawler.content_extractor import extract_content
from crawler.hash_detector import generate_hash, detect_status
from database.repository import get_article_by_url, upsert_article, insert_crawl_log

logger = logging.getLogger(__name__)


def discover_urls(site: dict) -> List[str]:
    """crawl_type に応じて記事URLを発見する。"""
    crawl_type = site["crawl_type"]

    if crawl_type == "sitemap":
        return fetch_urls_from_sitemap(
            sitemap_url=site["sitemap_url"],
            url_pattern=site.get("article_url_pattern", ""),
        )
    elif crawl_type == "pagination":
        return fetch_urls_from_pagination(
            pagination_url_template=site["pagination_url_template"],
            article_url_pattern=site.get("article_url_pattern", ""),
            article_list_selector=site.get("article_list_selector", "a"),
        )
    elif crawl_type == "single_page":
        return fetch_urls_from_single_page(
            blog_url=site["blog_url"],
            article_url_pattern=site.get("article_url_pattern", ""),
            article_list_selector=site.get("article_list_selector", "a"),
        )
    else:
        logger.error(f"未知のcrawl_type: {crawl_type}")
        return []


def process_urls(
    conn,
    urls: List[str],
    site_id: int,
    article_type: str,
    use_playwright: bool = False,
    delay_seconds: float = 1.0,
) -> Dict[str, int]:
    """URL一覧を処理してDB保存。新規・更新・未変更・失敗の件数を返す。"""
    counts = {"new": 0, "updated": 0, "unchanged": 0, "failed": 0}

    for url in urls:
        try:
            result = fetch_html(url, use_playwright=use_playwright)
            insert_crawl_log(conn, {
                "site_id": site_id,
                "article_url": url,
                "status_code": result["status_code"],
                "fetch_status": result["fetch_status"],
                "error_message": result.get("error_message"),
            })

            if result["fetch_status"] != "success":
                counts["failed"] += 1
                continue

            content = extract_content(result["html"])
            body_hash = generate_hash(content["body_text"] or "")
            existing = get_article_by_url(conn, url)
            status = detect_status(body_hash, existing["body_hash"] if existing else None)

            upsert_article(conn, {
                "site_id": site_id,
                "article_type": article_type,
                "article_url": url,
                "title": content["title"],
                "published_at": content["published_at"],
                "updated_at": content["updated_at"],
                "body_text": content["body_text"],
                "heading_structure": json.dumps(
                    content["heading_structure"], ensure_ascii=False
                ),
                "body_hash": body_hash,
                "status": status,
            })
            counts[status] += 1
            logger.info(f"[{status}] {url}")

        except Exception as e:
            logger.error(f"処理例外: {url} / {e}")
            counts["failed"] += 1

        time.sleep(delay_seconds)

    return counts
