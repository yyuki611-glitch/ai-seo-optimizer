CREATE TABLE IF NOT EXISTS sites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_name TEXT NOT NULL,
    site_url TEXT NOT NULL UNIQUE,
    crawl_type TEXT NOT NULL CHECK(crawl_type IN ('sitemap', 'pagination', 'single_page')),
    sitemap_url TEXT,
    blog_url TEXT,
    pagination_url_template TEXT,
    article_url_pattern TEXT,
    article_list_selector TEXT,
    use_playwright INTEGER NOT NULL DEFAULT 0,
    enabled INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS articles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    article_type TEXT NOT NULL CHECK(article_type IN ('competitor', 'own')),
    article_url TEXT NOT NULL UNIQUE,
    title TEXT,
    published_at TEXT,
    updated_at TEXT,
    body_text TEXT,
    heading_structure TEXT,
    body_hash TEXT,
    status TEXT NOT NULL CHECK(status IN ('new', 'updated', 'unchanged', 'failed')),
    first_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_crawled_at TEXT NOT NULL DEFAULT (datetime('now')),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_record_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (site_id) REFERENCES sites(id)
);

CREATE TABLE IF NOT EXISTS crawl_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    site_id INTEGER,
    article_url TEXT NOT NULL,
    status_code INTEGER,
    fetch_status TEXT NOT NULL CHECK(fetch_status IN ('success', 'failed', 'skipped')),
    error_message TEXT,
    crawled_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (site_id) REFERENCES sites(id)
);
