import sqlite3
from database.connection import initialize_db
from database.repository import upsert_site, upsert_article, get_article_by_url, insert_crawl_log


def test_initialize_db_creates_tables():
    conn = sqlite3.connect(":memory:")
    initialize_db(conn)
    tables = {
        row[0]
        for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
    }
    assert "sites" in tables
    assert "articles" in tables
    assert "crawl_logs" in tables
    conn.close()


def test_upsert_site_inserts_and_returns_id(db_conn):
    site_id = upsert_site(db_conn, {
        "site_name": "テストサイト",
        "site_url": "https://example.com",
        "crawl_type": "sitemap",
        "sitemap_url": "https://example.com/sitemap.xml",
        "blog_url": None,
        "pagination_url_template": None,
        "article_url_pattern": "/blog/",
        "article_list_selector": None,
        "use_playwright": 0,
        "enabled": 1,
    })
    assert isinstance(site_id, int)


def test_upsert_article_inserts_new(db_conn):
    site_id = upsert_site(db_conn, {
        "site_name": "テストサイト", "site_url": "https://example.com",
        "crawl_type": "sitemap", "sitemap_url": None, "blog_url": None,
        "pagination_url_template": None, "article_url_pattern": "/blog/",
        "article_list_selector": None, "use_playwright": 0, "enabled": 1,
    })
    upsert_article(db_conn, {
        "site_id": site_id, "article_type": "competitor",
        "article_url": "https://example.com/blog/1",
        "title": "テスト記事", "body_text": "本文",
        "heading_structure": "[]", "body_hash": "abc123",
        "status": "new", "published_at": None, "updated_at": None,
    })
    article = get_article_by_url(db_conn, "https://example.com/blog/1")
    assert article["title"] == "テスト記事"
    assert article["status"] == "new"


def test_upsert_article_updates_on_second_call(db_conn):
    site_id = upsert_site(db_conn, {
        "site_name": "テストサイト", "site_url": "https://example.com",
        "crawl_type": "sitemap", "sitemap_url": None, "blog_url": None,
        "pagination_url_template": None, "article_url_pattern": "/blog/",
        "article_list_selector": None, "use_playwright": 0, "enabled": 1,
    })
    data = {
        "site_id": site_id, "article_type": "competitor",
        "article_url": "https://example.com/blog/1",
        "title": "旧タイトル", "body_text": "旧本文",
        "heading_structure": "[]", "body_hash": "old_hash",
        "status": "new", "published_at": None, "updated_at": None,
    }
    upsert_article(db_conn, data)
    data["title"] = "新タイトル"
    data["status"] = "updated"
    upsert_article(db_conn, data)
    article = get_article_by_url(db_conn, "https://example.com/blog/1")
    assert article["title"] == "新タイトル"
    assert article["status"] == "updated"
