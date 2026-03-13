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
