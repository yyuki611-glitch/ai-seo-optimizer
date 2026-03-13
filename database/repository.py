import sqlite3
from datetime import datetime, timezone
from typing import Optional, List


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def upsert_site(conn: sqlite3.Connection, site: dict) -> int:
    """sitesにINSERT OR IGNOREしてsite_idを返す。"""
    conn.execute(
        """
        INSERT OR IGNORE INTO sites
          (site_name, site_url, crawl_type, sitemap_url, blog_url,
           pagination_url_template, article_url_pattern, article_list_selector,
           use_playwright, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            site["site_name"], site["site_url"], site["crawl_type"],
            site.get("sitemap_url"), site.get("blog_url"),
            site.get("pagination_url_template"), site.get("article_url_pattern"),
            site.get("article_list_selector"), site.get("use_playwright", 0),
            site.get("enabled", 1),
        ),
    )
    conn.commit()
    row = conn.execute(
        "SELECT id FROM sites WHERE site_url = ?", (site["site_url"],)
    ).fetchone()
    return row["id"]


def upsert_article(conn: sqlite3.Connection, article: dict) -> None:
    """article_urlをキーにINSERT or UPDATE。"""
    now = _now()
    existing = get_article_by_url(conn, article["article_url"])
    if existing is None:
        conn.execute(
            """
            INSERT INTO articles
              (site_id, article_type, article_url, title, published_at, updated_at,
               body_text, heading_structure, body_hash, status,
               first_seen_at, last_crawled_at, created_at, updated_record_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article["site_id"], article["article_type"], article["article_url"],
                article.get("title"), article.get("published_at"), article.get("updated_at"),
                article.get("body_text"), article["heading_structure"],
                article["body_hash"], article["status"],
                now, now, now, now,
            ),
        )
    else:
        conn.execute(
            """
            UPDATE articles SET
              title=?, body_text=?, heading_structure=?, body_hash=?,
              status=?, last_crawled_at=?, updated_record_at=?,
              published_at=COALESCE(?, published_at), updated_at=?
            WHERE article_url=?
            """,
            (
                article.get("title"), article.get("body_text"),
                article["heading_structure"], article["body_hash"],
                article["status"], now, now,
                article.get("published_at"), article.get("updated_at"),
                article["article_url"],
            ),
        )
    conn.commit()


def get_article_by_url(conn: sqlite3.Connection, url: str) -> Optional[sqlite3.Row]:
    return conn.execute(
        "SELECT * FROM articles WHERE article_url = ?", (url,)
    ).fetchone()


def insert_crawl_log(conn: sqlite3.Connection, log: dict) -> None:
    conn.execute(
        """
        INSERT INTO crawl_logs (site_id, article_url, status_code, fetch_status, error_message)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            log.get("site_id"), log["article_url"], log.get("status_code"),
            log["fetch_status"], log.get("error_message"),
        ),
    )
    conn.commit()


def get_pending_articles(conn: sqlite3.Connection) -> List[sqlite3.Row]:
    """new/updated の競合記事を返す（後続モジュール向け）。"""
    return conn.execute(
        "SELECT * FROM articles WHERE article_type='competitor' AND status IN ('new','updated')"
    ).fetchall()
