# AI検索最適化記事生成プロジェクト — Phase 1 収集モジュール 実装プラン（改訂版）

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 競合14サイト＋自社1サイトの実際の構造調査に基づき、3つの取得戦略（サイトマップ型・ページネーション型・一括スクレイプ型）を設定ファイルで切り替えながら記事を収集し、新規・更新・未変更を判定してSQLiteに保存する収集モジュールを構築する

**Architecture:** `competitors.yaml` に `crawl_type`（sitemap / pagination / single_page）と `use_playwright`（bool）を持たせ、オーケストレーターが設定に応じたフェッチャーを選択する。本文取得は requests を標準とし、`use_playwright: true` のサイトのみ Playwright にフォールバック。本文抽出・ハッシュ生成・DB保存は戦略非依存の共通コンポーネントとして設計し、疎結合を保つ。

**Tech Stack:** Python 3.11+, SQLite, requests, beautifulsoup4, lxml, pyyaml, python-dotenv, playwright, pytest

---

## サイト別クロール戦略（実調査に基づく）

| サイト | crawl_type | 主要URL | use_playwright |
|--------|-----------|---------|---------------|
| grooveinc.jp（自社） | pagination | /blog/page/{page} | false |
| bxo.co.jp | sitemap | /post-sitemap.xml | false |
| itsumo365.co.jp | sitemap | /sitemap.xml | false |
| wac-works-ec.jp | sitemap | /post-sitemap.xml | **true** |
| pureflat.co.jp | sitemap | /wp-sitemap-posts-post-1.xml | false |
| cyber-records.co.jp | sitemap | /post-sitemap.xml | false |
| force-r.co.jp | pagination | /column/page/{page}/ | false |
| sobani.co.jp | sitemap | /columnlist-sitemap.xml | false |
| picaro.co.jp | sitemap | /sitemap.xml | false |
| ubunbase.ubun.jp | sitemap | /post-sitemap.xml | false |
| finner.co.jp | sitemap | /post-sitemap.xml | false |
| meetsc.co.jp | single_page | /blog/ | false |
| dentsudigital.co.jp | sitemap | /sitemap.xml | false |
| hakuhodody-one.co.jp | sitemap | /news-sitemap.xml | false |
| oneder.hakuhodody-one.co.jp | sitemap | /sitemap.xml | false |

---

## ファイル構成

```
ai-seo-optimizer/
├── crawler/
│   ├── __init__.py
│   ├── fetchers/
│   │   ├── __init__.py
│   │   ├── sitemap_fetcher.py      # サイトマップXMLから記事URL一覧を取得
│   │   ├── pagination_fetcher.py   # ページネーションを辿って記事URL一覧を取得
│   │   └── single_page_fetcher.py  # 1ページに全記事がある場合の取得
│   ├── html_fetcher.py             # URLからHTMLを取得（requests + Playwright fallback）
│   ├── content_extractor.py        # HTMLから本文・タイトル・見出し・日付を抽出
│   ├── hash_detector.py            # 本文ハッシュ生成と変更判定
│   └── orchestrator.py             # 戦略切り替えと全体フロー調整
├── database/
│   ├── __init__.py
│   ├── connection.py               # SQLite接続管理
│   ├── repository.py               # sites/articles/crawl_logsへのCRUD
│   └── schema.sql                  # テーブル定義
├── config/
│   ├── competitors.yaml            # 競合サイト設定（実URLを記載済み）
│   └── own_sites.yaml              # 自社サイト設定
├── scripts/
│   └── run_crawler.py              # CLIエントリーポイント
├── tests/
│   ├── conftest.py
│   ├── test_sitemap_fetcher.py
│   ├── test_pagination_fetcher.py
│   ├── test_single_page_fetcher.py
│   ├── test_html_fetcher.py
│   ├── test_content_extractor.py
│   ├── test_hash_detector.py
│   └── test_repository.py
├── .github/
│   └── workflows/
│       └── crawler.yml
├── requirements.txt
├── .env.template
└── README.md
```

---

## Chunk 1: プロジェクト基盤

### Task 1: ディレクトリ作成と依存関係定義

**Files:**
- Create: `~/Desktop/Claude Code/test/ai-seo-optimizer/requirements.txt`
- Create: `~/Desktop/Claude Code/test/ai-seo-optimizer/.env.template`
- Create: `~/Desktop/Claude Code/test/ai-seo-optimizer/.gitignore`

- [ ] **Step 1: プロジェクトディレクトリを作成する**

```bash
mkdir -p ~/Desktop/"Claude Code"/test/ai-seo-optimizer/{crawler/fetchers,database,config,scripts,tests,.github/workflows}
touch ~/Desktop/"Claude Code"/test/ai-seo-optimizer/crawler/__init__.py
touch ~/Desktop/"Claude Code"/test/ai-seo-optimizer/crawler/fetchers/__init__.py
touch ~/Desktop/"Claude Code"/test/ai-seo-optimizer/database/__init__.py
```

- [ ] **Step 2: requirements.txt を作成する**

```
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
pyyaml==6.0.1
python-dotenv==1.0.1
playwright==1.44.0
pytest==8.1.1
pytest-mock==3.14.0
```

- [ ] **Step 3: .env.template を作成する**

```
# クローラー設定
CRAWLER_USER_AGENT=Mozilla/5.0 (compatible; ai-seo-optimizer/1.0)
CRAWLER_TIMEOUT=30
CRAWLER_DELAY_SECONDS=1

# DB設定
DB_PATH=data/articles.db
```

- [ ] **Step 4: .gitignore を作成する**

```
data/
*.db
.env
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 5: pip install を実行する**

```bash
cd ~/Desktop/"Claude Code"/test/ai-seo-optimizer
pip install -r requirements.txt
playwright install chromium
```

Expected: Successfully installed と表示される

- [ ] **Step 6: git init とコミット**

```bash
cd ~/Desktop/"Claude Code"/test/ai-seo-optimizer
git init
git add requirements.txt .env.template .gitignore
git commit -m "chore: initial project setup"
```

---

### Task 2: DBスキーマとコネクション定義

**Files:**
- Create: `database/schema.sql`
- Create: `database/connection.py`
- Create: `tests/conftest.py`
- Create: `tests/test_repository.py`（接続テストのみ）

- [ ] **Step 1: schema.sql を作成する**

```sql
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
    heading_structure TEXT,  -- JSON配列
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
```

- [ ] **Step 2: connection.py を作成する**

```python
# database/connection.py
import sqlite3
import os
from pathlib import Path


def get_connection(db_path: str | None = None) -> sqlite3.Connection:
    """SQLite接続を返す。db_path未指定時は環境変数 DB_PATH を使用。"""
    path = db_path or os.getenv("DB_PATH", "data/articles.db")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def initialize_db(conn: sqlite3.Connection) -> None:
    """schema.sql を読み込みテーブルを作成する。"""
    schema_path = Path(__file__).parent / "schema.sql"
    conn.executescript(schema_path.read_text())
    conn.commit()
```

- [ ] **Step 3: conftest.py を作成する**

```python
# tests/conftest.py
import pytest
import sqlite3
from database.connection import initialize_db


@pytest.fixture
def db_conn():
    """インメモリSQLiteコネクション（テスト毎に初期化）。"""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    initialize_db(conn)
    yield conn
    conn.close()
```

- [ ] **Step 4: DBコネクションの基本テストを書く**

```python
# tests/test_repository.py
import sqlite3
from database.connection import initialize_db


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
```

- [ ] **Step 5: テストを実行して通過を確認する**

```bash
cd ~/Desktop/"Claude Code"/test/ai-seo-optimizer
pytest tests/test_repository.py -v
```

Expected: PASSED

- [ ] **Step 6: コミット**

```bash
git add database/ tests/
git commit -m "feat: add database schema and connection module"
```

---

## Chunk 2: 設定ファイルと3種類のURL取得フェッチャー

### Task 3: 設定ファイルの定義（実URL入り）

**Files:**
- Create: `config/competitors.yaml`
- Create: `config/own_sites.yaml`

- [ ] **Step 1: competitors.yaml を実URLで作成する**

```yaml
# config/competitors.yaml
sites:
  - site_id: bxo
    site_name: "EC相談室"
    site_url: "https://bxo.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://bxo.co.jp/post-sitemap.xml"
    blog_url: ""
    article_url_pattern: "/magazine/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: itsumo365
    site_name: "株式会社いつも"
    site_url: "https://itsumo365.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://itsumo365.co.jp/sitemap.xml"
    blog_url: ""
    article_url_pattern: "/blog/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: wac_works
    site_name: "Wacworks"
    site_url: "https://wac-works-ec.jp"
    crawl_type: sitemap
    sitemap_url: "https://wac-works-ec.jp/post-sitemap.xml"
    blog_url: ""
    article_url_pattern: ""
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: true
    enabled: true

  - site_id: pureflat
    site_name: "ピュアフラット"
    site_url: "https://pureflat.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://pureflat.co.jp/wp-sitemap-posts-post-1.xml"
    blog_url: ""
    article_url_pattern: "/column/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: cyber_records
    site_name: "サイバーレコーズ"
    site_url: "https://www.cyber-records.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://www.cyber-records.co.jp/post-sitemap.xml"
    blog_url: ""
    article_url_pattern: ""
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: force_r
    site_name: "force-r"
    site_url: "https://force-r.co.jp"
    crawl_type: pagination
    sitemap_url: ""
    blog_url: "https://force-r.co.jp/column/"
    article_url_pattern: "/column/"
    article_list_selector: "figure a"
    pagination_url_template: "https://force-r.co.jp/column/page/{page}/"
    use_playwright: false
    enabled: true

  - site_id: sobani
    site_name: "sobani"
    site_url: "https://sobani.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://sobani.co.jp/columnlist-sitemap.xml"
    blog_url: ""
    article_url_pattern: "/columnlist/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: picaro
    site_name: "ピカロ"
    site_url: "https://www.picaro.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://www.picaro.co.jp/sitemap.xml"
    blog_url: ""
    article_url_pattern: "/blog-posts/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: ubunbase
    site_name: "ubunbase"
    site_url: "https://ubunbase.ubun.jp"
    crawl_type: sitemap
    sitemap_url: "https://ubunbase.ubun.jp/post-sitemap.xml"
    blog_url: ""
    article_url_pattern: "/blog/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: finner
    site_name: "finner"
    site_url: "https://finner.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://finner.co.jp/post-sitemap.xml"
    blog_url: ""
    article_url_pattern: "/media/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: meetsc
    site_name: "meetsc"
    site_url: "https://meetsc.co.jp"
    crawl_type: single_page
    sitemap_url: ""
    blog_url: "https://meetsc.co.jp/blog/"
    article_url_pattern: "/blog/"
    article_list_selector: ".card a"
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: dentsudigital
    site_name: "電通デジタル"
    site_url: "https://www.dentsudigital.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://www.dentsudigital.co.jp/sitemap.xml"
    blog_url: ""
    article_url_pattern: "/knowledge-charge/articles/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: hakuhodody_one
    site_name: "博報堂DYワン"
    site_url: "https://www.hakuhodody-one.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://www.hakuhodody-one.co.jp/news-sitemap.xml"
    blog_url: ""
    article_url_pattern: "/news/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true

  - site_id: oneder
    site_name: "oneder"
    site_url: "https://oneder.hakuhodody-one.co.jp"
    crawl_type: sitemap
    sitemap_url: "https://oneder.hakuhodody-one.co.jp/sitemap.xml"
    blog_url: ""
    article_url_pattern: "/blog/"
    article_list_selector: ""
    pagination_url_template: ""
    use_playwright: false
    enabled: true
```

- [ ] **Step 2: own_sites.yaml を作成する**

```yaml
# config/own_sites.yaml
own_site:
  site_id: grooveinc
  site_name: "GROOVE Inc. ブログ"
  site_url: "https://grooveinc.jp"
  crawl_type: pagination
  blog_url: "https://grooveinc.jp/blog"
  article_url_pattern: "/blog/"
  article_list_selector: ".blogList__item a"
  pagination_url_template: "https://grooveinc.jp/blog/page/{page}"
  use_playwright: false
```

- [ ] **Step 3: コミット**

```bash
git add config/
git commit -m "feat: add config yaml with real site URLs and crawl strategies"
```

---

### Task 4: サイトマップフェッチャー

**Files:**
- Create: `crawler/fetchers/sitemap_fetcher.py`
- Test: `tests/test_sitemap_fetcher.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_sitemap_fetcher.py
from unittest.mock import patch, MagicMock
from crawler.fetchers.sitemap_fetcher import fetch_urls_from_sitemap

SAMPLE_SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://example.com/blog/article-1/</loc></url>
  <url><loc>https://example.com/blog/article-2/</loc></url>
  <url><loc>https://example.com/page/about/</loc></url>
</urlset>"""

SAMPLE_SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://example.com/post-sitemap.xml</loc></sitemap>
  <sitemap><loc>https://example.com/page-sitemap.xml</loc></sitemap>
</sitemapindex>"""


def _mock_get(url, **kwargs):
    mock = MagicMock()
    mock.status_code = 200
    if "index" in url or url == "https://example.com/sitemap.xml":
        mock.content = SAMPLE_SITEMAP_INDEX.encode()
    else:
        mock.content = SAMPLE_SITEMAP.encode()
    return mock


def test_fetch_urls_from_sitemap_filters_by_pattern():
    with patch("crawler.fetchers.sitemap_fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(
            status_code=200, content=SAMPLE_SITEMAP.encode()
        )
        urls = fetch_urls_from_sitemap(
            sitemap_url="https://example.com/post-sitemap.xml",
            url_pattern="/blog/"
        )
    assert "https://example.com/blog/article-1/" in urls
    assert "https://example.com/blog/article-2/" in urls
    assert "https://example.com/page/about/" not in urls


def test_fetch_urls_from_sitemap_handles_sitemap_index():
    with patch("crawler.fetchers.sitemap_fetcher.requests.get", side_effect=_mock_get):
        urls = fetch_urls_from_sitemap(
            sitemap_url="https://example.com/sitemap.xml",
            url_pattern="/blog/"
        )
    assert "https://example.com/blog/article-1/" in urls


def test_fetch_urls_from_sitemap_returns_empty_on_http_error():
    with patch("crawler.fetchers.sitemap_fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=404)
        urls = fetch_urls_from_sitemap("https://example.com/sitemap.xml", "/blog/")
    assert urls == []


def test_fetch_urls_from_sitemap_deduplicates():
    doubled = SAMPLE_SITEMAP.replace(
        "</urlset>",
        "  <url><loc>https://example.com/blog/article-1/</loc></url>\n</urlset>"
    )
    with patch("crawler.fetchers.sitemap_fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, content=doubled.encode())
        urls = fetch_urls_from_sitemap("https://example.com/sitemap.xml", "/blog/")
    assert urls.count("https://example.com/blog/article-1/") == 1
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_sitemap_fetcher.py -v
```

Expected: ImportError

- [ ] **Step 3: sitemap_fetcher.py を実装する**

```python
# crawler/fetchers/sitemap_fetcher.py
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"


def fetch_urls_from_sitemap(
    sitemap_url: str,
    url_pattern: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> list[str]:
    """
    サイトマップから記事URL一覧を取得する。
    サイトマップインデックス（<sitemapindex>）の場合は子サイトマップを再帰取得する。
    url_patternで絞り込み、重複を除いて返す。
    """
    try:
        resp = requests.get(
            sitemap_url,
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )
        if resp.status_code != 200:
            logger.warning(f"サイトマップ取得失敗: {sitemap_url} status={resp.status_code}")
            return []

        soup = BeautifulSoup(resp.content, "lxml-xml")

        # サイトマップインデックスの場合は子サイトマップを再帰処理
        if soup.find("sitemapindex"):
            child_urls = [loc.text.strip() for loc in soup.find_all("loc")]
            seen: set[str] = set()
            results: list[str] = []
            for child_url in child_urls:
                for url in fetch_urls_from_sitemap(child_url, url_pattern, timeout, user_agent):
                    if url not in seen:
                        results.append(url)
                        seen.add(url)
            logger.info(f"サイトマップインデックス処理完了: {sitemap_url} → {len(results)}件")
            return results

        # 通常のサイトマップ
        seen = set()
        urls = []
        for loc in soup.find_all("loc"):
            url = loc.text.strip()
            if (not url_pattern or url_pattern in url) and url not in seen:
                urls.append(url)
                seen.add(url)
        logger.info(f"サイトマップ取得完了: {sitemap_url} → {len(urls)}件")
        return urls

    except Exception as e:
        logger.error(f"サイトマップ取得例外: {sitemap_url} / {e}")
        return []
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_sitemap_fetcher.py -v
```

Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/fetchers/sitemap_fetcher.py tests/test_sitemap_fetcher.py
git commit -m "feat: add sitemap fetcher with sitemap index support"
```

---

### Task 5: ページネーションフェッチャー

**Files:**
- Create: `crawler/fetchers/pagination_fetcher.py`
- Test: `tests/test_pagination_fetcher.py`

grooveinc.jp（`/blog/page/{page}`）と force-r.co.jp（`/column/page/{page}/`）で使用する。

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_pagination_fetcher.py
from unittest.mock import patch, MagicMock
from crawler.fetchers.pagination_fetcher import fetch_urls_from_pagination

# ページ1: 記事2件あり、次ページリンクあり
PAGE1_HTML = """<html><body>
  <ul>
    <li><a href="https://example.com/blog/article-1">記事1</a></li>
    <li><a href="https://example.com/blog/article-2">記事2</a></li>
  </ul>
  <a class="next" href="https://example.com/blog/page/2">次へ</a>
</body></html>"""

# ページ2: 記事1件、次ページリンクなし
PAGE2_HTML = """<html><body>
  <ul>
    <li><a href="https://example.com/blog/article-3">記事3</a></li>
  </ul>
</body></html>"""


def _make_mock(html: str):
    m = MagicMock()
    m.status_code = 200
    m.text = html
    return m


def test_fetch_urls_from_pagination_collects_all_pages():
    responses = [_make_mock(PAGE1_HTML), _make_mock(PAGE2_HTML)]
    with patch("crawler.fetchers.pagination_fetcher.requests.get", side_effect=responses):
        urls = fetch_urls_from_pagination(
            pagination_url_template="https://example.com/blog/page/{page}",
            article_url_pattern="/blog/article",
            article_list_selector="a",
        )
    assert "https://example.com/blog/article-1" in urls
    assert "https://example.com/blog/article-2" in urls
    assert "https://example.com/blog/article-3" in urls


def test_fetch_urls_from_pagination_stops_on_empty_page():
    """記事が見つからないページでストップする。"""
    empty = "<html><body><p>記事なし</p></body></html>"
    with patch("crawler.fetchers.pagination_fetcher.requests.get") as mock_get:
        mock_get.return_value = _make_mock(empty)
        urls = fetch_urls_from_pagination(
            pagination_url_template="https://example.com/blog/page/{page}",
            article_url_pattern="/blog/article",
            article_list_selector="a",
        )
    assert urls == []


def test_fetch_urls_from_pagination_deduplicates():
    """同じURLが複数ページに現れても重複しない。"""
    same = """<html><body>
      <a href="https://example.com/blog/article-1">記事1</a>
    </body></html>"""
    responses = [_make_mock(same), _make_mock(same), MagicMock(status_code=404)]
    with patch("crawler.fetchers.pagination_fetcher.requests.get", side_effect=responses):
        urls = fetch_urls_from_pagination(
            pagination_url_template="https://example.com/blog/page/{page}",
            article_url_pattern="/blog/article",
            article_list_selector="a",
        )
    assert urls.count("https://example.com/blog/article-1") == 1
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_pagination_fetcher.py -v
```

- [ ] **Step 3: pagination_fetcher.py を実装する**

```python
# crawler/fetchers/pagination_fetcher.py
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"
MAX_PAGES = 100  # 無限ループ防止


def fetch_urls_from_pagination(
    pagination_url_template: str,
    article_url_pattern: str,
    article_list_selector: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> list[str]:
    """
    ページネーションを辿って記事URL一覧を収集する。
    pagination_url_template は {page} プレースホルダーを含むURL（例: /blog/page/{page}）。
    article_list_selector は記事リンクを含む要素のCSSセレクタ。
    記事が見つからないページで終了。
    """
    collected: list[str] = []
    seen: set[str] = set()

    for page in range(1, MAX_PAGES + 1):
        page_url = pagination_url_template.format(page=page)
        try:
            resp = requests.get(
                page_url,
                timeout=timeout,
                headers={"User-Agent": user_agent},
            )
            if resp.status_code != 200:
                logger.info(f"ページ取得終了: {page_url} status={resp.status_code}")
                break

            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select(article_list_selector)
            page_urls = [
                a["href"] for a in links
                if a.get("href") and article_url_pattern in a["href"]
            ]

            if not page_urls:
                logger.info(f"記事URLなし、ページネーション終了: page={page}")
                break

            for url in page_urls:
                if url not in seen:
                    collected.append(url)
                    seen.add(url)

            logger.info(f"ページ {page}: {len(page_urls)}件取得")

        except Exception as e:
            logger.error(f"ページ取得例外: {page_url} / {e}")
            break

    logger.info(f"ページネーション完了: 計{len(collected)}件")
    return collected
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_pagination_fetcher.py -v
```

Expected: 3 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/fetchers/pagination_fetcher.py tests/test_pagination_fetcher.py
git commit -m "feat: add pagination fetcher with infinite loop guard"
```

---

### Task 6: 一括スクレイプフェッチャー（single_page）

**Files:**
- Create: `crawler/fetchers/single_page_fetcher.py`
- Test: `tests/test_single_page_fetcher.py`

meetsc.co.jp のように全記事が1ページに存在するサイト向け。

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_single_page_fetcher.py
from unittest.mock import patch, MagicMock
from crawler.fetchers.single_page_fetcher import fetch_urls_from_single_page

SAMPLE_HTML = """<html><body>
  <div class="card"><a href="https://example.com/blog/article-1">記事1</a></div>
  <div class="card"><a href="https://example.com/blog/article-2">記事2</a></div>
  <div class="card"><a href="https://example.com/other/page">別ページ</a></div>
  <div class="card"><a href="https://example.com/blog/article-1">重複</a></div>
</body></html>"""


def test_fetch_urls_from_single_page_filters_and_deduplicates():
    mock_resp = MagicMock(status_code=200, text=SAMPLE_HTML)
    with patch("crawler.fetchers.single_page_fetcher.requests.get", return_value=mock_resp):
        urls = fetch_urls_from_single_page(
            blog_url="https://example.com/blog/",
            article_url_pattern="/blog/",
            article_list_selector=".card a",
        )
    assert "https://example.com/blog/article-1" in urls
    assert "https://example.com/blog/article-2" in urls
    assert "https://example.com/other/page" not in urls
    assert urls.count("https://example.com/blog/article-1") == 1


def test_fetch_urls_from_single_page_returns_empty_on_error():
    mock_resp = MagicMock(status_code=500)
    with patch("crawler.fetchers.single_page_fetcher.requests.get", return_value=mock_resp):
        urls = fetch_urls_from_single_page(
            blog_url="https://example.com/blog/",
            article_url_pattern="/blog/",
            article_list_selector=".card a",
        )
    assert urls == []
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_single_page_fetcher.py -v
```

- [ ] **Step 3: single_page_fetcher.py を実装する**

```python
# crawler/fetchers/single_page_fetcher.py
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"


def fetch_urls_from_single_page(
    blog_url: str,
    article_url_pattern: str,
    article_list_selector: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> list[str]:
    """
    全記事が1ページに存在するサイト（例: meetsc.co.jp）向け。
    blog_url を取得して article_list_selector で記事リンクを抽出する。
    """
    try:
        resp = requests.get(
            blog_url,
            timeout=timeout,
            headers={"User-Agent": user_agent},
        )
        if resp.status_code != 200:
            logger.warning(f"一括取得失敗: {blog_url} status={resp.status_code}")
            return []

        soup = BeautifulSoup(resp.text, "lxml")
        seen: set[str] = set()
        urls: list[str] = []
        for a in soup.select(article_list_selector):
            href = a.get("href", "")
            if article_url_pattern in href and href not in seen:
                urls.append(href)
                seen.add(href)

        logger.info(f"一括取得完了: {blog_url} → {len(urls)}件")
        return urls

    except Exception as e:
        logger.error(f"一括取得例外: {blog_url} / {e}")
        return []
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_single_page_fetcher.py -v
```

Expected: 2 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/fetchers/single_page_fetcher.py tests/test_single_page_fetcher.py
git commit -m "feat: add single page fetcher for sites with all articles on one page"
```

---

## Chunk 3: HTML取得・本文抽出・ハッシュ生成

### Task 7: HTMLフェッチャー（requests + Playwright fallback）

**Files:**
- Create: `crawler/html_fetcher.py`
- Test: `tests/test_html_fetcher.py`

`use_playwright: true` のサイト（wac-works-ec.jp）ではPlaywrightで取得する。

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_html_fetcher.py
from unittest.mock import patch, MagicMock
from crawler.html_fetcher import fetch_html


def test_fetch_html_returns_success_with_requests():
    mock_resp = MagicMock(status_code=200, text="<html><body>content</body></html>")
    with patch("crawler.html_fetcher.requests.get", return_value=mock_resp):
        result = fetch_html("https://example.com/article/1", use_playwright=False)
    assert result["status_code"] == 200
    assert result["html"] == "<html><body>content</body></html>"
    assert result["fetch_status"] == "success"


def test_fetch_html_returns_failed_on_http_error():
    mock_resp = MagicMock(status_code=404, text="")
    with patch("crawler.html_fetcher.requests.get", return_value=mock_resp):
        result = fetch_html("https://example.com/article/404", use_playwright=False)
    assert result["status_code"] == 404
    assert result["fetch_status"] == "failed"


def test_fetch_html_returns_failed_on_exception():
    with patch("crawler.html_fetcher.requests.get", side_effect=Exception("timeout")):
        result = fetch_html("https://example.com/article/1", use_playwright=False)
    assert result["fetch_status"] == "failed"
    assert "timeout" in result["error_message"]


def test_fetch_html_uses_playwright_when_specified(tmp_path):
    """use_playwright=True のとき _fetch_with_playwright が呼ばれることを確認。"""
    mock_html = "<html><body>playwright content</body></html>"
    with patch("crawler.html_fetcher._fetch_with_playwright", return_value=mock_html) as mock_pw:
        result = fetch_html("https://example.com/article/1", use_playwright=True)
    mock_pw.assert_called_once_with("https://example.com/article/1")
    assert result["fetch_status"] == "success"
    assert result["html"] == mock_html
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_html_fetcher.py -v
```

- [ ] **Step 3: html_fetcher.py を実装する**

```python
# crawler/html_fetcher.py
import logging
import os
import requests

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = int(os.getenv("CRAWLER_TIMEOUT", 30))
DEFAULT_USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT", "Mozilla/5.0 (compatible; ai-seo-optimizer/1.0)"
)


def fetch_html(
    url: str,
    use_playwright: bool = False,
    timeout: int = DEFAULT_TIMEOUT,
    user_agent: str = DEFAULT_USER_AGENT,
) -> dict:
    """
    URLからHTMLを取得する。
    use_playwright=True のときは Playwright を使用（JS重めのサイト向け）。
    戻り値: {status_code, html, fetch_status, error_message}
    """
    if use_playwright:
        try:
            html = _fetch_with_playwright(url)
            return {
                "status_code": 200,
                "html": html,
                "fetch_status": "success",
                "error_message": None,
            }
        except Exception as e:
            logger.error(f"Playwright取得例外: {url} / {e}")
            return {
                "status_code": None,
                "html": None,
                "fetch_status": "failed",
                "error_message": str(e),
            }

    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": user_agent})
        if resp.status_code == 200:
            return {
                "status_code": resp.status_code,
                "html": resp.text,
                "fetch_status": "success",
                "error_message": None,
            }
        logger.warning(f"HTTP {resp.status_code}: {url}")
        return {
            "status_code": resp.status_code,
            "html": None,
            "fetch_status": "failed",
            "error_message": f"HTTP {resp.status_code}",
        }
    except Exception as e:
        logger.error(f"requests取得例外: {url} / {e}")
        return {
            "status_code": None,
            "html": None,
            "fetch_status": "failed",
            "error_message": str(e),
        }


def _fetch_with_playwright(url: str) -> str:
    """Playwright でページをレンダリングして HTML を返す。"""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(url, wait_until="networkidle")
        html = page.content()
        browser.close()
    return html
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_html_fetcher.py -v
```

Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/html_fetcher.py tests/test_html_fetcher.py
git commit -m "feat: add html fetcher with playwright fallback support"
```

---

### Task 8: コンテンツエクストラクター

**Files:**
- Create: `crawler/content_extractor.py`
- Test: `tests/test_content_extractor.py`

調査で判明したJSON-LD形式の日付取得に対応する。

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_content_extractor.py
from crawler.content_extractor import extract_content

# grooveinc.jpやHubSpotサイトでよく見られるJSON-LDパターン
HTML_WITH_JSON_LD = """
<html>
<head>
  <title>テスト記事タイトル</title>
  <script type="application/ld+json">
  {"@type": "Article", "headline": "LD記事タイトル",
   "datePublished": "2024-01-15", "dateModified": "2024-02-01"}
  </script>
</head>
<body>
  <article>
    <h1>メイン見出し</h1>
    <h2>セクション1</h2>
    <p>本文テキスト1です。</p>
    <h2>セクション2</h2>
    <p>本文テキスト2です。</p>
  </article>
</body>
</html>"""

HTML_WITHOUT_JSON_LD = """
<html>
<head><title>シンプルな記事</title></head>
<body>
  <article>
    <h1>記事タイトル</h1>
    <p>本文テキスト。</p>
    <time datetime="2024-03-01">2024年3月1日</time>
  </article>
</body>
</html>"""


def test_extract_content_returns_title_from_title_tag():
    result = extract_content(HTML_WITHOUT_JSON_LD)
    assert result["title"] == "シンプルな記事"


def test_extract_content_returns_body_text():
    result = extract_content(HTML_WITH_JSON_LD)
    assert "本文テキスト1" in result["body_text"]
    assert "本文テキスト2" in result["body_text"]


def test_extract_content_returns_headings():
    result = extract_content(HTML_WITH_JSON_LD)
    headings = result["heading_structure"]
    assert any(h["text"] == "メイン見出し" and h["level"] == 1 for h in headings)
    assert any(h["text"] == "セクション1" and h["level"] == 2 for h in headings)


def test_extract_content_prefers_json_ld_date():
    result = extract_content(HTML_WITH_JSON_LD)
    assert result["published_at"] == "2024-01-15"
    assert result["updated_at"] == "2024-02-01"


def test_extract_content_falls_back_to_time_tag():
    result = extract_content(HTML_WITHOUT_JSON_LD)
    assert result["published_at"] == "2024-03-01"


def test_extract_content_returns_none_for_missing_date():
    html = "<html><body><p>日付なし</p></body></html>"
    result = extract_content(html)
    assert result["published_at"] is None
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_content_extractor.py -v
```

- [ ] **Step 3: content_extractor.py を実装する**

```python
# crawler/content_extractor.py
import json
import logging
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def extract_content(html: str) -> dict:
    """HTMLからタイトル・本文・見出し・日付を抽出する。取得できない項目はNone。"""
    soup = BeautifulSoup(html, "lxml")
    json_ld = _extract_json_ld(soup)

    return {
        "title": _extract_title(soup, json_ld),
        "body_text": _extract_body_text(soup),
        "heading_structure": _extract_headings(soup),
        "published_at": _extract_published_at(soup, json_ld),
        "updated_at": json_ld.get("dateModified") if json_ld else None,
    }


def _extract_json_ld(soup: BeautifulSoup) -> dict:
    """JSON-LDスクリプトタグからArticle情報を取得する。"""
    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and "Article" in item.get("@type", ""):
                        return item
            elif isinstance(data, dict) and "Article" in data.get("@type", ""):
                return data
        except (json.JSONDecodeError, AttributeError):
            continue
    return {}


def _extract_title(soup: BeautifulSoup, json_ld: dict) -> str | None:
    tag = soup.find("title")
    return tag.get_text(strip=True) if tag else None


def _extract_body_text(soup: BeautifulSoup) -> str:
    for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
        tag.decompose()
    article = soup.find("article") or soup.find("main") or soup.body
    if article is None:
        return ""
    text = article.get_text(separator="\n")
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_headings(soup: BeautifulSoup) -> list[dict]:
    return [
        {"level": int(tag.name[1]), "text": tag.get_text(strip=True)}
        for tag in soup.find_all(["h1", "h2", "h3", "h4"])
    ]


def _extract_published_at(soup: BeautifulSoup, json_ld: dict) -> str | None:
    # JSON-LD優先
    if json_ld.get("datePublished"):
        return json_ld["datePublished"]
    # <time datetime="..."> フォールバック
    time_tag = soup.find("time")
    if time_tag:
        return time_tag.get("datetime") or time_tag.get_text(strip=True)
    # <meta property="article:published_time"> フォールバック
    meta = soup.find("meta", {"property": "article:published_time"})
    if meta:
        return meta.get("content")
    return None
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_content_extractor.py -v
```

Expected: 6 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/content_extractor.py tests/test_content_extractor.py
git commit -m "feat: add content extractor with JSON-LD date support"
```

---

### Task 9: ハッシュ生成・変更判定

**Files:**
- Create: `crawler/hash_detector.py`
- Test: `tests/test_hash_detector.py`

- [ ] **Step 1: 失敗するテストを書く**

```python
# tests/test_hash_detector.py
from crawler.hash_detector import generate_hash, detect_status


def test_generate_hash_is_consistent():
    assert generate_hash("テキスト") == generate_hash("テキスト")


def test_generate_hash_normalizes_whitespace():
    assert generate_hash("本文  テキスト\n\nサンプル") == generate_hash("本文 テキスト サンプル")


def test_detect_status_new_when_no_existing_hash():
    assert detect_status("abc123", None) == "new"


def test_detect_status_unchanged_when_same():
    assert detect_status("abc123", "abc123") == "unchanged"


def test_detect_status_updated_when_different():
    assert detect_status("abc123", "xyz789") == "updated"
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_hash_detector.py -v
```

- [ ] **Step 3: hash_detector.py を実装する**

```python
# crawler/hash_detector.py
import hashlib
import re


def generate_hash(body_text: str) -> str:
    normalized = re.sub(r"\s+", " ", body_text).strip()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def detect_status(current_hash: str, existing_hash: str | None) -> str:
    if existing_hash is None:
        return "new"
    return "unchanged" if current_hash == existing_hash else "updated"
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_hash_detector.py -v
```

Expected: 5 passed

- [ ] **Step 5: コミット**

```bash
git add crawler/hash_detector.py tests/test_hash_detector.py
git commit -m "feat: add hash generator and change status detector"
```

---

## Chunk 4: DBリポジトリ・オーケストレーター・エントリーポイント

### Task 10: DBリポジトリ

**Files:**
- Create: `database/repository.py`
- Modify: `tests/test_repository.py`

- [ ] **Step 1: テストを追記する**

```python
# tests/test_repository.py に追加（既存の test_initialize_db_creates_tables は残す）

from database.repository import upsert_site, upsert_article, get_article_by_url, insert_crawl_log


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
```

- [ ] **Step 2: テストが失敗することを確認する**

```bash
pytest tests/test_repository.py -v
```

- [ ] **Step 3: repository.py を実装する**

```python
# database/repository.py
import sqlite3
from datetime import datetime, timezone


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


def get_article_by_url(conn: sqlite3.Connection, url: str) -> sqlite3.Row | None:
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


def get_pending_articles(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    """new/updated の競合記事を返す（後続モジュール向け）。"""
    return conn.execute(
        "SELECT * FROM articles WHERE article_type='competitor' AND status IN ('new','updated')"
    ).fetchall()
```

- [ ] **Step 4: テストを実行して通過を確認する**

```bash
pytest tests/test_repository.py -v
```

Expected: 4 passed

- [ ] **Step 5: コミット**

```bash
git add database/repository.py tests/test_repository.py
git commit -m "feat: add database repository with upsert and crawl log"
```

---

### Task 11: オーケストレーター

**Files:**
- Create: `crawler/orchestrator.py`

3つの取得戦略を設定に基づいて切り替え、HTML取得→本文抽出→ハッシュ判定→DB保存まで行う。

- [ ] **Step 1: orchestrator.py を実装する**

```python
# crawler/orchestrator.py
"""
収集フローのオーケストレーター。
サイト設定の crawl_type に基づいて URL 発見戦略を切り替え、
HTML取得 → 本文抽出 → ハッシュ判定 → DB保存 を実行する。
"""
import json
import logging
import time

from crawler.fetchers.sitemap_fetcher import fetch_urls_from_sitemap
from crawler.fetchers.pagination_fetcher import fetch_urls_from_pagination
from crawler.fetchers.single_page_fetcher import fetch_urls_from_single_page
from crawler.html_fetcher import fetch_html
from crawler.content_extractor import extract_content
from crawler.hash_detector import generate_hash, detect_status
from database.repository import get_article_by_url, upsert_article, insert_crawl_log

logger = logging.getLogger(__name__)


def discover_urls(site: dict) -> list[str]:
    """
    crawl_type に応じて記事URLを発見する。
    戻り値: 記事URLのリスト
    """
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
    urls: list[str],
    site_id: int,
    article_type: str,
    use_playwright: bool = False,
    delay_seconds: float = 1.0,
) -> dict:
    """
    URL一覧を処理してDB保存。
    新規・更新・未変更・失敗の件数を返す。
    """
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
```

- [ ] **Step 2: コミット**

```bash
git add crawler/orchestrator.py
git commit -m "feat: add orchestrator with 3-strategy url discovery"
```

---

### Task 12: エントリーポイント（run_crawler.py）

**Files:**
- Create: `scripts/run_crawler.py`

- [ ] **Step 1: run_crawler.py を実装する**

```python
# scripts/run_crawler.py
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


def load_config(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def run_competitor_crawl(conn, competitors: list[dict]) -> dict:
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
```

- [ ] **Step 2: ローカル手動実行テスト（1サイトだけ）**

competitors.yaml の bxo.co.jp だけ `enabled: true`、他を `enabled: false` にして実行：
```bash
cd ~/Desktop/"Claude Code"/test/ai-seo-optimizer
python scripts/run_crawler.py --target competitor
```

Expected: ログが出力され、`data/articles.db` が生成される

- [ ] **Step 3: DB内容を確認する**

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/articles.db')
conn.row_factory = sqlite3.Row
rows = conn.execute('SELECT article_url, title, status FROM articles LIMIT 5').fetchall()
for r in rows: print(dict(r))
"
```

Expected: 取得した記事データが表示される

- [ ] **Step 4: コミット**

```bash
git add scripts/run_crawler.py
git commit -m "feat: add run_crawler entrypoint with 3-strategy support"
```

---

## Chunk 5: GitHub Actions と最終確認

### Task 13: GitHub Actions ワークフロー

**Files:**
- Create: `.github/workflows/crawler.yml`

- [ ] **Step 1: crawler.yml を作成する**

```yaml
name: Daily Crawler

on:
  schedule:
    - cron: '0 1 * * *'  # 毎日 JST 10:00
  workflow_dispatch:

jobs:
  crawl:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          playwright install chromium

      - name: Run crawler
        env:
          DB_PATH: data/articles.db
          CRAWLER_DELAY_SECONDS: 2
        run: python scripts/run_crawler.py --target both

      - name: Upload DB artifact
        uses: actions/upload-artifact@v4
        with:
          name: articles-db-${{ github.run_id }}
          path: data/articles.db
          retention-days: 7
```

- [ ] **Step 2: コミット**

```bash
git add .github/workflows/crawler.yml
git commit -m "ci: add GitHub Actions daily crawler workflow"
```

---

### Task 14: 全テスト実行と最終確認

- [ ] **Step 1: 全テストを実行する**

```bash
cd ~/Desktop/"Claude Code"/test/ai-seo-optimizer
pytest tests/ -v
```

Expected: 全テスト PASSED（test_html_fetcher, test_sitemap_fetcher, test_pagination_fetcher, test_single_page_fetcher, test_content_extractor, test_hash_detector, test_repository）

- [ ] **Step 2: 全競合サイトを有効にして実行する**

すべての `enabled: true` に戻してから：
```bash
python scripts/run_crawler.py --target both
```

Expected:
- エラーで処理が止まらない（1件失敗しても継続）
- `data/articles.db` に記事データが蓄積される

- [ ] **Step 3: 取得結果を確認する**

```bash
python -c "
import sqlite3
conn = sqlite3.connect('data/articles.db')
conn.row_factory = sqlite3.Row
total = conn.execute('SELECT COUNT(*) as n FROM articles').fetchone()['n']
by_site = conn.execute('''
  SELECT s.site_name, COUNT(*) as cnt,
         SUM(CASE WHEN a.status=\"new\" THEN 1 ELSE 0 END) as new_cnt
  FROM articles a JOIN sites s ON a.site_id=s.id
  GROUP BY s.site_name
''').fetchall()
print(f'総記事数: {total}')
for r in by_site: print(dict(r))
"
```

- [ ] **Step 4: 最終コミット**

```bash
git add .
git commit -m "feat: Phase 1 collection module complete"
```

---

## 検証チェックリスト（完成条件）

- [ ] 3つのURL取得戦略（sitemap/pagination/single_page）が動作する
- [ ] HTMLから本文・タイトル・見出し・日付（JSON-LD対応）を抽出できる
- [ ] 本文ハッシュで新規/更新/未変更を判定できる
- [ ] `use_playwright: true` のサイトでPlaywrightが使われる
- [ ] SQLiteに articles/sites/crawl_logs が保存される
- [ ] 1件失敗しても処理全体が継続する
- [ ] 全pytestがパスしている
- [ ] GitHub Actionsワークフローが定義されている

---

## 注意事項

- `data/` と `*.db` は `.gitignore` に含まれている
- GitHub Actions では DB は Artifact として保存（リポジトリにはコミットしない）
- Playwright が必要なサイトは現時点で wac-works-ec.jp のみ
- 新しいサイトを追加するには `competitors.yaml` に行を追加するだけ
