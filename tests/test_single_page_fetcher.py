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
