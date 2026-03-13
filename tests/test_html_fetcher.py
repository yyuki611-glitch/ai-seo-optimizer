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


def test_fetch_html_uses_playwright_when_specified():
    mock_html = "<html><body>playwright content</body></html>"
    with patch("crawler.html_fetcher._fetch_with_playwright", return_value=mock_html) as mock_pw:
        result = fetch_html("https://example.com/article/1", use_playwright=True)
    mock_pw.assert_called_once_with("https://example.com/article/1")
    assert result["fetch_status"] == "success"
    assert result["html"] == mock_html
