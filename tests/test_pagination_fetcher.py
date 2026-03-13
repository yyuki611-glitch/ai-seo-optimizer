from unittest.mock import patch, MagicMock
from crawler.fetchers.pagination_fetcher import fetch_urls_from_pagination

PAGE1_HTML = """<html><body>
  <ul>
    <li><a href="https://example.com/blog/article-1">記事1</a></li>
    <li><a href="https://example.com/blog/article-2">記事2</a></li>
  </ul>
  <a class="next" href="https://example.com/blog/page/2">次へ</a>
</body></html>"""

PAGE2_HTML = """<html><body>
  <ul>
    <li><a href="https://example.com/blog/article-3">記事3</a></li>
  </ul>
</body></html>"""


def _make_mock(html):
    m = MagicMock()
    m.status_code = 200
    m.text = html
    return m


def test_fetch_urls_from_pagination_collects_all_pages():
    responses = [_make_mock(PAGE1_HTML), _make_mock(PAGE2_HTML), MagicMock(status_code=404)]
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
