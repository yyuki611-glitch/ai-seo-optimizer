import logging
import os
import requests
from typing import Optional, Dict, Any

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
) -> Dict[str, Any]:
    """
    URLからHTMLを取得する。
    use_playwright=True のときは Playwright を使用。
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
