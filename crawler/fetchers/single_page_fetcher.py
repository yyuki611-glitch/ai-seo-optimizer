import logging
import requests
from bs4 import BeautifulSoup
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"


def fetch_urls_from_single_page(
    blog_url: str,
    article_url_pattern: str,
    article_list_selector: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[str]:
    """
    全記事が1ページに存在するサイト向け。
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
        seen = set()
        urls = []
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
