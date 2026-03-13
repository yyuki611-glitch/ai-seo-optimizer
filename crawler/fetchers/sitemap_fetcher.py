import logging
import requests
from bs4 import BeautifulSoup
from typing import List

logger = logging.getLogger(__name__)

DEFAULT_USER_AGENT = "ai-seo-optimizer/1.0"


def fetch_urls_from_sitemap(
    sitemap_url: str,
    url_pattern: str,
    timeout: int = 30,
    user_agent: str = DEFAULT_USER_AGENT,
) -> List[str]:
    """
    サイトマップから記事URL一覧を取得する。
    サイトマップインデックスの場合は子サイトマップを再帰取得する。
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

        if soup.find("sitemapindex"):
            child_urls = [loc.text.strip() for loc in soup.find_all("loc")]
            seen = set()
            results = []
            for child_url in child_urls:
                for url in fetch_urls_from_sitemap(child_url, url_pattern, timeout, user_agent):
                    if url not in seen:
                        results.append(url)
                        seen.add(url)
            logger.info(f"サイトマップインデックス処理完了: {sitemap_url} → {len(results)}件")
            return results

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
